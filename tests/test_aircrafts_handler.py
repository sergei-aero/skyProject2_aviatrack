import pytest
from src.aircrafts_handler import Aircraft


class TestAircraft:
    """Тесты для класса Aircraft."""

    # --- Валидное создание ---
    def test_valid_creation(self):
        """Создание экземпляра с корректными данными."""
        a = Aircraft(
            icao24="abc123",
            callsign="AFR123",
            origin_country="France",
            longitude=2.35,
            latitude=48.86,
            altitude=10000,
            on_ground=False,
            velocity=250.5,
            heading=45.0,
        )
        assert a.icao24 == "abc123"
        assert a.callsign == "AFR123"
        assert a.origin_country == "France"
        assert a.longitude == 2.35
        assert a.latitude == 48.86
        assert a.altitude == 10000
        assert a.on_ground is False
        assert a.velocity == 250.5
        assert a.heading == 45.0

    def test_valid_creation_minimal(self):
        """Создание с минимальным набором параметров (остальные по умолчанию)."""
        a = Aircraft(icao24="abc123", origin_country="France")
        assert a.icao24 == "abc123"
        assert a.callsign is None
        assert a.origin_country == "France"
        assert a.longitude == 0.0
        assert a.latitude == 0.0
        assert a.altitude == 0.0
        assert a.on_ground is False
        assert a.velocity is None
        assert a.heading is None

    # --- Валидация on_ground ---
    @pytest.mark.parametrize("og", ["True", 1, None])
    def test_on_ground_invalid(self, og):
        """on_ground должен быть булевым."""
        with pytest.raises(ValueError, match="on_ground must be a boolean"):
            Aircraft(icao24="abc123", origin_country="France", on_ground=og)

    # --- Валидация velocity ---
    @pytest.mark.parametrize("vel", [-10, "not_number"])
    def test_velocity_invalid(self, vel):
        """velocity не может быть отрицательной и должна быть числом (если не None)."""
        with pytest.raises(ValueError):
            Aircraft(icao24="abc123", origin_country="France", velocity=vel)

    # --- Валидация heading ---
    @pytest.mark.parametrize("hdg", [-1, 360, "not_number"])
    def test_heading_invalid(self, hdg):
        """heading должен быть в [0, 360) и числом (если не None)."""
        with pytest.raises(ValueError):
            Aircraft(icao24="abc123", origin_country="France", heading=hdg)

    # --- Сравнение по высоте ---
    def test_eq(self):
        a1 = Aircraft("a1", altitude=10000)
        a2 = Aircraft("a2", altitude=10000)
        a3 = Aircraft("a3", altitude=20000)
        assert a1 == a2
        assert a1 != a3
        assert not (a1 == "not_aircraft")  # NotImplemented приводит к False

    def test_lt(self):
        a_low = Aircraft("low", altitude=5000)
        a_high = Aircraft("high", altitude=15000)
        assert a_low < a_high
        assert not (a_high < a_low)
        assert not (a_low < a_low)  # равные не меньше

    def test_sorting(self):
        """Сортировка списка самолётов по возрастанию высоты."""
        a1 = Aircraft("a1", altitude=10000)
        a2 = Aircraft("a2", altitude=5000)
        a3 = Aircraft("a3", altitude=20000)
        unsorted = [a1, a2, a3]
        sorted_expected = [a2, a1, a3]
        assert sorted(unsorted) == sorted_expected

    # --- Сериализация ---
    def test_to_dict(self):
        a = Aircraft(
            icao24="abc123",
            callsign="AFR123",
            origin_country="France",
            longitude=2.35,
            latitude=48.86,
            altitude=10000,
            on_ground=False,
            velocity=250.5,
            heading=45.0,
        )
        expected = {
            "icao24": "abc123",
            "callsign": "AFR123",
            "origin_country": "France",
            "longitude": 2.35,
            "latitude": 48.86,
            "altitude": 10000,
            "on_ground": False,
            "velocity": 250.5,
            "heading": 45.0,
        }
        assert a.to_dict() == expected

    def test_from_dict(self):
        data = {
            "icao24": "abc123",
            "callsign": "AFR123",
            "origin_country": "France",
            "longitude": 2.35,
            "latitude": 48.86,
            "altitude": 10000,
            "on_ground": False,
            "velocity": 250.5,
            "heading": 45.0,
        }
        a = Aircraft.from_dict(data)
        assert a.icao24 == "abc123"
        assert a.callsign == "AFR123"
        assert a.origin_country == "France"
        assert a.longitude == 2.35
        assert a.latitude == 48.86
        assert a.altitude == 10000
        assert a.on_ground is False
        assert a.velocity == 250.5
        assert a.heading == 45.0

    def test_from_dict_minimal(self):
        """from_dict должен работать с отсутствующими полями."""
        data = {"icao24": "abc123"}
        a = Aircraft.from_dict(data)
        assert a.icao24 == "abc123"
        assert a.callsign is None
        assert a.origin_country == ""
        assert a.longitude == 0.0
        assert a.latitude == 0.0
        assert a.altitude == 0.0
        assert a.on_ground is False
        assert a.velocity is None
        assert a.heading is None

    # --- Проверка __slots__ ---
    def test_slots_prevent_new_attributes(self):
        a = Aircraft("abc123", origin_country="France")
        with pytest.raises(AttributeError):
            a.new_attr = 42

    def test_slots_defined(self):
        a = Aircraft("abc123", origin_country="France")
        assert hasattr(a, "__slots__")
        # Проверим, что можно читать существующие атрибуты
        assert a.icao24 == "abc123"
