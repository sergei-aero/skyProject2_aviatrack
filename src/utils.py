import os
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Tuple

# Загружаем переменные окружения из .env файла
load_dotenv()


class BaseAPIClient(ABC):
    """
    Абстрактный базовый класс для работы с REST API.
    Содержит реализацию метода подключения (проверки доступности) и
    абстрактный метод получения информации о самолётах.
    """

    def __init__(self):
        # Единая сессия для всех запросов (приватная)
        self.__session = requests.Session()
        # Заголовки по умолчанию (можно расширять в наследниках)
        self.__session.headers.update({"User-Agent": "GeoAirClient/1.0 (pavlov.aero@gmail.com)"})

    def _connect(self, url: str, headers: Optional[Dict] = None, auth: Optional[Tuple[str, str]] = None) -> bool:
        """
        Защищённый метод для проверки доступности API.
        Выполняет HEAD-запрос к указанному URL и проверяет статус-код.
        :param url: Базовый URL API (например, https://nominatim.openstreetmap.org)
        :param headers: Дополнительные заголовки
        :param auth: Кортеж (username, password) для базовой аутентификации
        :return: True, если статус-код успешный (2xx)
        :raises: Exception при ошибках соединения или статусе >= 400
        """
        try:
            # Используем HEAD для минимизации нагрузки
            response = self.__session.head(
                url,
                headers=headers or {},
                auth=auth,
                timeout=10,
                allow_redirects=True,  # разрешаем редиректы (например, для защиты)
            )
            # Проверяем, что статус-код успешный (2xx)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise Exception(f"API connection failed for {url}: {e}") from e

    @abstractmethod
    def get_aircraft_info(self, country_name: str) -> List[Dict[str, Any]]:
        """
        Абстрактный метод для получения информации о самолётах в воздушном пространстве страны.
        Должен быть реализован в наследнике.
        """
        pass

    # Дополнительные защищённые методы для выполнения запросов
    def _get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        auth: Optional[Tuple[str, str]] = None,
    ) -> Dict[str, Any]:
        """Выполняет GET-запрос и возвращает JSON-ответ."""
        try:
            resp = self.__session.get(url, params=params, headers=headers or {}, auth=auth, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"GET request to {url} failed: {e}") from e


class GeoAirClient(BaseAPIClient):
    """
    Конкретный клиент для работы с Nominatim (поиск координат стран)
    и OpenSky Network (информация о самолётах).
    """

    def __init__(self):
        super().__init__()
        # Приватные атрибуты для URL и учётных данных
        self.__nominatim_url = "https://nominatim.openstreetmap.org"
        self.__opensky_url = "https://opensky-network.org/api"

        # Загрузка учётных данных OpenSky из переменных окружения
        opensky_username = os.getenv("OPENSKY_USERNAME")
        opensky_password = os.getenv("OPENSKY_PASSWORD")
        self.__opensky_auth = (opensky_username, opensky_password) if opensky_username and opensky_password else None

    # Приватные методы для проверки подключения к каждому API
    def __connect_nominatim(self) -> None:
        """Проверяет доступность Nominatim API."""
        # Для Nominatim обязателен заголовок User-Agent (уже есть в сессии)
        self._connect(self.__nominatim_url)

    def __connect_opensky(self) -> None:
        """
        Проверяет доступность OpenSky API через тестовый GET-запрос.
        (HEAD-запрос к корню запрещён, поэтому используем минимальный GET)
        """
        try:
            # Параметры с нулевым прямоугольником — такой запрос всегда вернёт пустой список
            test_params = {"lamin": 0, "lomin": 0, "lamax": 0, "lomax": 0}
            # Выполняем GET-запрос через унаследованный _get
            self._get(f"{self.__opensky_url}/states/all", params=test_params, auth=self.__opensky_auth)
        except Exception as e:
            raise Exception(f"OpenSky API connection failed: {e}") from e

    # Вспомогательный приватный метод для поиска страны в Nominatim
    def __nominatim_search(self, country_name: str) -> Dict[str, Any]:
        """
        Выполняет поиск страны в Nominatim и возвращает первый результат.
        """
        params = {
            "q": country_name,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "email": os.getenv("NOMINATIM_EMAIL", "pavlov.aero@gmail.com"),
        }
        # Перед запросом проверяем подключение
        self.__connect_nominatim()

        url = f"{self.__nominatim_url}/search"
        # Передаём заголовки? User-Agent уже в сессии.
        results = self._get(url, params=params)
        if not results:
            raise ValueError(f"Country '{country_name}' not found in Nominatim")
        return results[0]

    # Основной метод, реализующий абстрактный метод родителя
    def get_aircraft_info(self, country_name: str) -> List[Dict[str, Any]]:
        """
        Получает список самолётов в воздушном пространстве указанной страны.
        Использует Nominatim для получения bounding box страны и OpenSky для получения данных.
        """
        # 1. Получаем bounding box страны через Nominatim
        nominatim_data = self.__nominatim_search(country_name)
        bbox = nominatim_data.get("boundingbox")
        if not bbox:
            raise ValueError(f"Bounding box not available for {country_name}")
        min_lat, max_lat, min_lon, max_lon = map(float, bbox)

        # 2. Проверяем подключение к OpenSky
        self.__connect_opensky()

        # 3. Запрашиваем состояния воздушных судов в этом прямоугольнике
        params = {"lamin": min_lat, "lomin": min_lon, "lamax": max_lat, "lomax": max_lon}
        url = f"{self.__opensky_url}/states/all"
        data = self._get(url, params=params, auth=self.__opensky_auth)

        # 4. Преобразуем ответ в список словарей с основными полями
        states = data.get("states", [])
        aircraft_list = []
        for s in states:
            aircraft = {
                "icao24": s[0],
                "callsign": s[1].strip() if s[1] else None,
                "origin_country": s[2],
                "longitude": s[5],
                "latitude": s[6],
                "altitude": s[7],  # барометрическая высота, м
                "on_ground": s[8],
                "velocity": s[9],  # скорость, м/с
                "heading": s[10],  # истинный курс, градусы
            }
            aircraft_list.append(aircraft)
        return aircraft_list


# Пример использования
if __name__ == "__main__":
    client = GeoAirClient()

    # Получаем самолёты над Францией
    try:
        aircraft = client.get_aircraft_info("France")
        print(f"Найдено самолётов: {len(aircraft)}")
        for a in aircraft[:5]:  # покажем первые 5
            print(a)
    except Exception as e:
        print(f"Ошибка: {e}")
