import pytest
import csv
from src.file_handler import JsonFileHandler, CsvFileHandler
from src.aircrafts_handler import Aircraft


# Фикстура для временной директории (предоставляется pytest)
@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


class TestJsonFileHandler:
    """Тесты для JsonFileHandler с использованием временных файлов."""

    def test_write_and_read(self, temp_dir):
        file_path = temp_dir / "test.json"
        handler = JsonFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        a2 = Aircraft("def456", "DLH456", "Germany", 2.36, 48.87, 11000, False, 260, 50)
        handler.write_data([a1, a2])

        assert file_path.exists()
        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 2
        assert read_aircraft[0].icao24 == "abc123"
        assert read_aircraft[1].icao24 == "def456"

    def test_append_new(self, temp_dir):
        file_path = temp_dir / "test.json"
        handler = JsonFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        handler.write_data([a1])

        a2 = Aircraft("def456", "DLH456", "Germany", 2.36, 48.87, 11000, False, 260, 50)
        handler.append_data(a2)

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 2
        assert {a.icao24 for a in read_aircraft} == {"abc123", "def456"}

    def test_append_duplicate(self, temp_dir):
        file_path = temp_dir / "test.json"
        handler = JsonFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        handler.write_data([a1])

        a2 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)  # дубликат
        handler.append_data(a2)

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 1  # не добавился

    def test_delete_existing(self, temp_dir):
        file_path = temp_dir / "test.json"
        handler = JsonFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        a2 = Aircraft("def456", "DLH456", "Germany", 2.36, 48.87, 11000, False, 260, 50)
        handler.write_data([a1, a2])

        result = handler.delete_data("abc123")
        assert result is True

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 1
        assert read_aircraft[0].icao24 == "def456"

    def test_delete_non_existing(self, temp_dir):
        file_path = temp_dir / "test.json"
        handler = JsonFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        handler.write_data([a1])

        result = handler.delete_data("nonexistent")
        assert result is False

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 1

    def test_read_from_nonexistent_file(self, temp_dir):
        file_path = temp_dir / "nonexistent.json"
        handler = JsonFileHandler(str(file_path))
        read_aircraft = handler.read_data()
        assert read_aircraft == []


class TestCsvFileHandler:
    """Тесты для CsvFileHandler с использованием временных файлов."""

    def test_write_and_read(self, temp_dir):
        file_path = temp_dir / "test.csv"
        handler = CsvFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        a2 = Aircraft("def456", "DLH456", "Germany", 2.36, 48.87, 11000, False, 260, 50)
        handler.write_data([a1, a2])

        assert file_path.exists()
        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 2
        assert read_aircraft[0].icao24 == "abc123"
        assert read_aircraft[1].icao24 == "def456"

    def test_append_new(self, temp_dir):
        file_path = temp_dir / "test.csv"
        handler = CsvFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        handler.write_data([a1])

        a2 = Aircraft("def456", "DLH456", "Germany", 2.36, 48.87, 11000, False, 260, 50)
        handler.append_data(a2)

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 2
        assert {a.icao24 for a in read_aircraft} == {"abc123", "def456"}

    def test_append_duplicate(self, temp_dir):
        file_path = temp_dir / "test.csv"
        handler = CsvFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        handler.write_data([a1])

        a2 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)  # дубликат
        handler.append_data(a2)

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 1

    def test_delete_existing(self, temp_dir):
        file_path = temp_dir / "test.csv"
        handler = CsvFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        a2 = Aircraft("def456", "DLH456", "Germany", 2.36, 48.87, 11000, False, 260, 50)
        handler.write_data([a1, a2])

        result = handler.delete_data("abc123")
        assert result is True

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 1
        assert read_aircraft[0].icao24 == "def456"

    def test_delete_non_existing(self, temp_dir):
        file_path = temp_dir / "test.csv"
        handler = CsvFileHandler(str(file_path))
        a1 = Aircraft("abc123", "AFR123", "France", 2.35, 48.86, 10000, False, 250, 45)
        handler.write_data([a1])

        result = handler.delete_data("nonexistent")
        assert result is False

        read_aircraft = handler.read_data()
        assert len(read_aircraft) == 1

    def test_read_from_nonexistent_file(self, temp_dir):
        file_path = temp_dir / "nonexistent.csv"
        handler = CsvFileHandler(str(file_path))
        read_aircraft = handler.read_data()
        assert read_aircraft == []

    def test_write_empty_list(self, temp_dir):
        file_path = temp_dir / "empty.csv"
        handler = CsvFileHandler(str(file_path))
        handler.write_data([])
        assert file_path.exists()

        # Проверяем, что файл содержит только заголовки
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 1  # только строка заголовков
        expected_headers = [
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
        assert rows[0] == expected_headers
