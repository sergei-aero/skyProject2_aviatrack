import json
import os
import csv
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
from src.aircrafts_handler import Aircraft


def get_data_path(filename: str) -> str:
    """
    Возвращает абсолютный путь к файлу в папке data,
    находящейся в корне проекта (рядом с папкой src).
    """
    # Получаем путь к директории, где находится этот модуль (src)
    src_dir = Path(__file__).parent
    # Корень проекта — родитель src
    project_root = src_dir.parent
    # Папка data
    data_dir = project_root / "data"
    # Создаём папку, если её нет
    data_dir.mkdir(exist_ok=True)
    # Полный путь к файлу
    return str(data_dir / filename)


class BaseFileHandler(ABC):
    """
    Абстрактный базовый класс для работы с файлами, хранящими список самолётов.
    Определяет контракт для наследников.
    """

    def __init__(self, filename: str = "aircraft.json"):
        # filename должен быть полным путём к файлу (включая путь к data)
        self.__filename = filename

    @property
    def filename(self) -> str:
        """Защищённый доступ к имени файла (только для чтения)."""
        return self.__filename

    @abstractmethod
    def read_data(self) -> List[Aircraft]:
        """
        Читает данные из файла и возвращает список объектов Aircraft.
        Если файл не существует или пуст, возвращает пустой список.
        """
        pass

    @abstractmethod
    def write_data(self, aircraft_list: List[Aircraft]) -> None:
        """
        Полностью перезаписывает файл переданным списком самолётов.
        """
        pass

    @abstractmethod
    def append_data(self, aircraft: Aircraft) -> None:
        """
        Добавляет один самолёт в файл, избегая дубликатов.
        Если самолёт с таким icao24 уже существует, он не добавляется.
        """
        pass

    @abstractmethod
    def delete_data(self, icao24: str) -> bool:
        """
        Удаляет самолёт с указанным icao24 из файла.
        Возвращает True, если удаление произошло, иначе False.
        """
        pass


class JsonFileHandler(BaseFileHandler):
    """
    Реализация для работы с JSON-файлами.
    Данные хранятся в виде списка словарей.
    """

    def __init__(self, filename: str = "aircraft.json"):
        # Преобразуем имя файла в полный путь к папке data
        full_path = get_data_path(filename)
        super().__init__(full_path)

    def _ensure_dir_exists(self):
        """Создаёт директорию для файла, если она не существует."""
        directory = os.path.dirname(self.filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _load_json(self) -> List[Dict[str, Any]]:
        """Загружает содержимое JSON-файла в список словарей."""
        if not os.path.exists(self.filename):
            return []
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # В случае ошибки чтения возвращаем пустой список
            return []

    def _save_json(self, data: List[Dict[str, Any]]) -> None:
        """Сохраняет список словарей в JSON-файл."""
        self._ensure_dir_exists()  # создаём директорию (хотя она уже должна быть)
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def read_data(self) -> List[Aircraft]:
        data = self._load_json()
        return [Aircraft.from_dict(item) for item in data]

    def write_data(self, aircraft_list: List[Aircraft]) -> None:
        data = [a.to_dict() for a in aircraft_list]
        self._save_json(data)

    def append_data(self, aircraft: Aircraft) -> None:
        data = self._load_json()
        existing_icaos = {item["icao24"] for item in data}
        if aircraft.icao24 not in existing_icaos:
            data.append(aircraft.to_dict())
            self._save_json(data)

    def delete_data(self, icao24: str) -> bool:
        data = self._load_json()
        initial_len = len(data)
        data = [item for item in data if item["icao24"] != icao24]
        if len(data) < initial_len:
            self._save_json(data)
            return True
        return False


class CsvFileHandler(BaseFileHandler):
    """
    Дополнительный класс для работы с CSV-файлами.
    """

    def __init__(self, filename: str = "aircraft.csv"):
        # Преобразуем имя файла в полный путь к папке data
        full_path = get_data_path(filename)
        super().__init__(full_path)

    def _ensure_dir_exists(self):
        """Создаёт директорию для файла, если она не существует."""
        directory = os.path.dirname(self.filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _read_csv(self) -> List[Dict[str, Any]]:
        """Читает CSV и возвращает список словарей."""
        if not os.path.exists(self.filename):
            return []
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except (IOError, csv.Error):
            return []

    def _write_csv(self, data: List[Dict[str, Any]]) -> None:
        """Записывает список словарей в CSV."""
        self._ensure_dir_exists()
        if not data:
            # Если данных нет, создаём пустой файл с заголовками
            fieldnames = [
                "icao24",
                "callsign",
                "origin_country",
                "longitude",
                "latitude",
                "altitude",
                "on_ground",
                "velocity",
                "heading",
            ]
            with open(self.filename, "w", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            return

        fieldnames = data[0].keys()
        with open(self.filename, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    def read_data(self) -> List[Aircraft]:
        data = self._read_csv()
        aircrafts = []
        for item in data:
            try:
                aircraft = Aircraft(
                    icao24=item["icao24"],
                    callsign=item.get("callsign"),
                    origin_country=item["origin_country"],
                    longitude=float(item["longitude"]),
                    latitude=float(item["latitude"]),
                    altitude=float(item["altitude"]),
                    on_ground=item["on_ground"].lower() == "true",
                    velocity=float(item["velocity"]) if item.get("velocity") else None,
                    heading=float(item["heading"]) if item.get("heading") else None,
                )
                aircrafts.append(aircraft)
            except (KeyError, ValueError, TypeError):
                # Пропускаем некорректные строки
                continue
        return aircrafts

    def write_data(self, aircraft_list: List[Aircraft]) -> None:
        data = [a.to_dict() for a in aircraft_list]
        self._write_csv(data)

    def append_data(self, aircraft: Aircraft) -> None:
        data = self._read_csv()
        existing_icaos = {item["icao24"] for item in data}
        if aircraft.icao24 not in existing_icaos:
            data.append(aircraft.to_dict())
            self._write_csv(data)

    def delete_data(self, icao24: str) -> bool:
        data = self._read_csv()
        initial_len = len(data)
        data = [item for item in data if item["icao24"] != icao24]
        if len(data) < initial_len:
            self._write_csv(data)
            return True
        return False


# Демонстрация работы
if __name__ == "__main__":
    # Создаём несколько самолётов
    a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
    a2 = Aircraft("def456", "DLH456", "Germany", 2.36, 48.87, 11000, False, 260, 50)
    a3 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)  # дубликат

    # JSON-обработчик (файл будет в data/test_aircraft.json)
    json_handler = JsonFileHandler("test_aircraft.json")
    json_handler.write_data([a1, a2])
    json_handler.append_data(a3)  # дубликат не добавится
    print("JSON данные после добавления:", [a.icao24 for a in json_handler.read_data()])

    # Удаление
    json_handler.delete_data("def456")
    print("JSON после удаления def456:", [a.icao24 for a in json_handler.read_data()])

    # CSV-обработчик (файл будет в data/test_aircraft.csv)
    csv_handler = CsvFileHandler("test_aircraft.csv")
    csv_handler.write_data([a1, a2])
    csv_handler.append_data(a3)
    print("CSV данные после добавления:", [a.icao24 for a in csv_handler.read_data()])

    csv_handler.delete_data("abc123")
    print("CSV после удаления abc123:", [a.icao24 for a in csv_handler.read_data()])
