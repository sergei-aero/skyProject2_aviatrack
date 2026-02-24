import os
import pytest
import requests
import requests_mock
from unittest.mock import patch

from src.utils import GeoAirClient


@pytest.fixture
def geoair_client(monkeypatch):
    """Создаёт экземпляр GeoAirClient с подменой переменных окружения."""
    monkeypatch.setenv("OPENSKY_USERNAME", "test_user")
    monkeypatch.setenv("OPENSKY_PASSWORD", "test_pass")
    monkeypatch.setenv("NOMINATIM_EMAIL", "test@example.com")
    return GeoAirClient()


class TestGeoAirClient:
    """Тесты для класса GeoAirClient."""

    def test_get_aircraft_info_country_not_found(self, geoair_client):
        """Страна не найдена в Nominatim."""
        with requests_mock.Mocker() as m:
            m.head("https://nominatim.openstreetmap.org", status_code=200)
            nominatim_url = (
                "https://nominatim.openstreetmap.org/search"
                "?q=Atlantis&format=json&limit=1&addressdetails=1&email=test@example.com"
            )
            m.get(nominatim_url, json=[])

            with pytest.raises(ValueError, match="Country 'Atlantis' not found in Nominatim"):
                geoair_client.get_aircraft_info("Atlantis")

    def test_get_aircraft_info_no_bounding_box(self, geoair_client):
        """Ответ Nominatim не содержит boundingbox."""
        with requests_mock.Mocker() as m:
            m.head("https://nominatim.openstreetmap.org", status_code=200)
            nominatim_url = (
                "https://nominatim.openstreetmap.org/search"
                "?q=France&format=json&limit=1&addressdetails=1&email=test@example.com"
            )
            m.get(nominatim_url, json=[{"lat": "48.8566", "lon": "2.3522"}])

            with pytest.raises(ValueError, match="Bounding box not available for France"):
                geoair_client.get_aircraft_info("France")

    def test_get_aircraft_info_nominatim_connection_fail(self, geoair_client):
        """Ошибка подключения к Nominatim (HEAD-запрос не удался)."""
        with requests_mock.Mocker() as m:
            m.head("https://nominatim.openstreetmap.org", exc=requests.ConnectionError)

            with pytest.raises(Exception, match="API connection failed for https://nominatim.openstreetmap.org"):
                geoair_client.get_aircraft_info("France")

    def test_get_aircraft_info_opensky_test_fail(self, geoair_client):
        """Ошибка при тестовом подключении к OpenSky."""
        with requests_mock.Mocker() as m:
            # Nominatim успешен
            m.head("https://nominatim.openstreetmap.org", status_code=200)
            nominatim_url = (
                "https://nominatim.openstreetmap.org/search"
                "?q=France&format=json&limit=1&addressdetails=1&email=test@example.com"
            )
            m.get(nominatim_url, json=[{"boundingbox": ["48.815", "48.902", "2.224", "2.470"]}])

            # OpenSky test request — ошибка таймаута
            opensky_test_url = (
                "https://opensky-network.org/api/states/all"
                "?lamin=0&lomin=0&lamax=0&lomax=0"
            )
            m.get(opensky_test_url, exc=requests.Timeout)

            with pytest.raises(Exception, match="OpenSky API connection failed"):
                geoair_client.get_aircraft_info("France")

    def test_opensky_auth_used_when_credentials_present(self):
        """Если заданы логин и пароль, они передаются в запросы."""
        with patch.dict(os.environ, {
            "OPENSKY_USERNAME": "user",
            "OPENSKY_PASSWORD": "pass",
            "NOMINATIM_EMAIL": "test@example.com"
        }):
            client = GeoAirClient()
            assert client._GeoAirClient__opensky_auth == ("user", "pass")

    def test_opensky_auth_none_when_credentials_missing(self):
        """Если учётные данные не заданы, аутентификация не используется."""
        with patch.dict(os.environ, {}, clear=True):
            client = GeoAirClient()
            assert client._GeoAirClient__opensky_auth is None