import os
import sys
from typing import List, Optional

# Импортируем классы из соответствующих модулей (пути могут отличаться)
from src.utils import GeoAirClient
from src.aircrafts_handler import Aircraft
from src.file_handler import JsonFileHandler, CsvFileHandler


def get_data_file_path(country_name: str, file_format: str = "json") -> str:
    """
    Возвращает путь к файлу для сохранения данных о самолётах заданной страны.
    Папка data создаётся в корне проекта (рядом с main.py).
    """
    safe_name = country_name.strip().lower().replace(" ", "_")
    filename = f"{safe_name}_aircraft.{file_format}"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


def print_aircraft_table(aircraft_list: List[Aircraft], limit: Optional[int] = None) -> None:
    """Выводит список самолётов в виде таблицы."""
    if not aircraft_list:
        print("Нет данных для отображения.")
        return

    headers = [
        "ICAO24",
        "Callsign",
        "Страна рег.",
        "Долгота",
        "Широта",
        "Высота (м)",
        "На земле",
        "Скорость (м/с)",
        "Курс",
    ]
    col_widths = [10, 10, 15, 10, 10, 10, 10, 12, 8]

    def format_row(ac: Aircraft) -> List[str]:
        return [
            ac.icao24,
            ac.callsign or "",
            ac.origin_country,
            f"{ac.longitude:.2f}" if ac.longitude is not None else "N/A",
            f"{ac.latitude:.2f}" if ac.latitude is not None else "N/A",
            str(ac.altitude) if ac.altitude is not None else "N/A",
            "Да" if ac.on_ground else "Нет",
            f"{ac.velocity:.1f}" if ac.velocity is not None else "N/A",
            f"{ac.heading:.0f}" if ac.heading is not None else "N/A",
        ]

    header_str = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_str)
    print("-" * len(header_str))

    for i, ac in enumerate(aircraft_list):
        if limit and i >= limit:
            break
        row = format_row(ac)
        print(" | ".join(cell.ljust(w) for cell, w in zip(row, col_widths)))


def get_top_n_by_altitude(aircraft_list: List[Aircraft], n: int) -> List[Aircraft]:
    """
    Возвращает n самолётов с наибольшей высотой.
    Самолёты с неизвестной высотой помещаются в конец списка.
    """
    with_alt = [ac for ac in aircraft_list if ac.altitude is not None]
    without_alt = [ac for ac in aircraft_list if ac.altitude is None]

    with_alt.sort(key=lambda ac: ac.altitude, reverse=True)

    result = with_alt[:n]
    if len(result) < n:
        result.extend(without_alt[: n - len(result)])
    return result


def filter_by_registration_country(aircraft_list: List[Aircraft], country: str) -> List[Aircraft]:
    """Возвращает самолёты, зарегистрированные в указанной стране (без учёта регистра)."""
    country_lower = country.lower()
    return [ac for ac in aircraft_list if ac.origin_country and ac.origin_country.lower() == country_lower]


def choose_file_format() -> str:
    """Запрашивает у пользователя предпочитаемый формат файла (json/csv)."""
    while True:
        fmt = input("Выберите формат файла (json/csv) [по умолчанию json]: ").strip().lower()
        if fmt in ("", "json"):
            return "json"
        elif fmt == "csv":
            return "csv"
        else:
            print("Некорректный ввод. Введите 'json' или 'csv'.")


def load_aircraft_from_file(file_path: str, file_format: str) -> List[Aircraft]:
    """Загружает список самолётов из файла с помощью соответствующего обработчика."""
    if file_format == "json":
        handler = JsonFileHandler(file_path)
    else:
        handler = CsvFileHandler(file_path)
    return handler.read_data()


def save_aircraft_to_file(aircraft_list: List[Aircraft], file_path: str, file_format: str) -> None:
    """Сохраняет список самолётов в файл с помощью соответствующего обработчика."""
    if file_format == "json":
        handler = JsonFileHandler(file_path)
    else:
        handler = CsvFileHandler(file_path)
    handler.write_data(aircraft_list)


def main():
    api_client = GeoAirClient()

    while True:
        country_name = input("\nВведите название страны для поиска самолётов (или 'exit' для выхода): ").strip()
        if country_name.lower() in ("exit", "quit", "q"):
            print("До свидания!")
            break

        if not country_name:
            print("Название страны не может быть пустым.")
            continue

        # Выбор формата файла
        file_format = choose_file_format()
        file_path = get_data_file_path(country_name, file_format)

        aircraft_objects = None

        # Проверяем, существует ли уже файл с данными для этой страны
        if os.path.exists(file_path):
            print(f"Найден сохранённый файл: {file_path}")
            choice = (
                input("Использовать сохранённые данные (S) или запросить новые из API (N)? [S/n]: ").strip().lower()
            )
            if choice in ("", "s"):
                try:
                    aircraft_objects = load_aircraft_from_file(file_path, file_format)
                    print(f"Загружено {len(aircraft_objects)} самолётов из файла.")
                except Exception as e:
                    print(f"Ошибка при чтении файла: {e}. Будет выполнен запрос к API.")
                    aircraft_objects = None
            # Если choice == 'n' или что-то иное, идём к API

        if aircraft_objects is None:
            # Запрашиваем данные через API
            try:
                print(f"Запрашиваю данные для страны {country_name} через OpenSky...")
                aircraft_dicts = api_client.get_aircraft_info(country_name)
                # Преобразуем словари в объекты Aircraft
                aircraft_objects = [Aircraft.from_dict(d) for d in aircraft_dicts]
                print(f"Получено {len(aircraft_objects)} самолётов.")
                # Сохраняем в файл
                save_aircraft_to_file(aircraft_objects, file_path, file_format)
                print(f"Данные сохранены в {file_path}")
            except Exception as e:
                print(f"Ошибка при получении данных: {e}")
                continue

        if not aircraft_objects:
            print("В воздушном пространстве этой страны сейчас нет самолётов (или страна не найдена).")
            continue
        print(f"Всего самолётов в выборке: {len(aircraft_objects)}")
        # Работа с полученными данными
        while True:
            print("\nМеню действий:")
            print("1 - Показать топ N самолётов по высоте")
            print("2 - Показать самолёты по стране регистрации")
            print("3 - Ввести другую страну")
            print("0 - Выход из программы")

            choice = input("Ваш выбор: ").strip()
            if choice == "1":
                n_str = input("Введите количество самолётов для вывода (N): ").strip()
                try:
                    n = int(n_str)
                    if n <= 0:
                        print("N должно быть положительным числом.")
                        continue
                except ValueError:
                    print("Некорректное число.")
                    continue

                top = get_top_n_by_altitude(aircraft_objects, n)
                print(f"\nТоп {len(top)} самолётов по высоте:")
                print_aircraft_table(top)

            elif choice == "2":
                reg_country = input("Введите страну регистрации: ").strip()
                if not reg_country:
                    print("Страна не может быть пустой.")
                    continue
                filtered = filter_by_registration_country(aircraft_objects, reg_country)
                if not filtered:
                    print(f"Нет самолётов, зарегистрированных в стране '{reg_country}'.")
                else:
                    print(f"\nСамолёты, зарегистрированные в '{reg_country}':")
                    print_aircraft_table(filtered)

            elif choice == "3":
                break  # возврат к выбору новой страны

            elif choice == "0":
                print("До свидания!")
                sys.exit(0)

            else:
                print("Неверный выбор, повторите.")


if __name__ == "__main__":
    main()
