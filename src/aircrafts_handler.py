class Aircraft:
    """
    Класс, представляющий самолёт с основными атрибутами.
    Использует __slots__ для экономии памяти.
    Поддерживает сравнение по высоте полета через магические методы.
    Включает приватные методы валидации данных при инициализации.
    """

    __slots__ = ('_icao24', '_callsign', '_origin_country', '_altitude',
                 '_longitude', '_latitude', '_on_ground', '_velocity', '_heading')

    def __init__(self, icao24: str, callsign: str = None, origin_country: str = '',
                 altitude: float = 0.0, longitude: float = 0.0, latitude: float = 0.0,
                 on_ground: bool = False, velocity: float = None, heading: float = None):
        # Приватные методы валидации вызываются при установке значений
        self._icao24 = self.__validate_icao24(icao24)
        self._callsign = self.__validate_callsign(callsign)
        self._origin_country = self.__validate_origin_country(origin_country)
        self._altitude = self.__validate_altitude(altitude)
        self._longitude = self.__validate_longitude(longitude)
        self._latitude = self.__validate_latitude(latitude)
        self._on_ground = self.__validate_on_ground(on_ground)
        self._velocity = self.__validate_velocity(velocity)
        self._heading = self.__validate_heading(heading)

    # --- Приватные методы валидации ---
    @staticmethod
    def __validate_icao24(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("icao24 must be a non-empty string")
        return value.strip()

    @staticmethod
    def __validate_callsign(value: str) -> str:
        if value is not None and not isinstance(value, str):
            raise ValueError("callsign must be a string or None")
        return value.strip() if value else None

    @staticmethod
    def __validate_origin_country(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("origin_country must be a string")
        return value

    @staticmethod
    def __validate_altitude(value: float) -> float:
        try:
            val = float(value)
        except (TypeError, ValueError):
            raise ValueError("altitude must be a number")
        if val < 0:
            raise ValueError("altitude cannot be negative")
        return val

    @staticmethod
    def __validate_longitude(value: float) -> float:
        try:
            val = float(value)
        except (TypeError, ValueError):
            raise ValueError("longitude must be a number")
        if val < -180 or val > 180:
            raise ValueError("longitude must be between -180 and 180")
        return val

    @staticmethod
    def __validate_latitude(value: float) -> float:
        try:
            val = float(value)
        except (TypeError, ValueError):
            raise ValueError("latitude must be a number")
        if val < -90 or val > 90:
            raise ValueError("latitude must be between -90 and 90")
        return val

    @staticmethod
    def __validate_on_ground(value: bool) -> bool:
        if not isinstance(value, bool):
            raise ValueError("on_ground must be a boolean")
        return value

    @staticmethod
    def __validate_velocity(value: float) -> float:
        if value is None:
            return None
        try:
            val = float(value)
        except (TypeError, ValueError):
            raise ValueError("velocity must be a number or None")
        if val < 0:
            raise ValueError("velocity cannot be negative")
        return val

    @staticmethod
    def __validate_heading(value: float) -> float:
        if value is None:
            return None
        try:
            val = float(value)
        except (TypeError, ValueError):
            raise ValueError("heading must be a number or None")
        if val < 0 or val >= 360:
            raise ValueError("heading must be in range [0, 360)")
        return val

    # --- Свойства для доступа к атрибутам ---
    @property
    def icao24(self) -> str:
        return self._icao24

    @property
    def callsign(self) -> str:
        return self._callsign

    @property
    def origin_country(self) -> str:
        return self._origin_country

    @property
    def altitude(self) -> float:
        return self._altitude

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def on_ground(self) -> bool:
        return self._on_ground

    @property
    def velocity(self) -> float:
        return self._velocity

    @property
    def heading(self) -> float:
        return self._heading

    # --- Методы сравнения по высоте полета (достаточно для сортировки) ---
    def __eq__(self, other) -> bool:
        if not isinstance(other, Aircraft):
            return NotImplemented
        return self._altitude == other._altitude

    def __lt__(self, other) -> bool:
        if not isinstance(other, Aircraft):
            return NotImplemented
        return self._altitude < other._altitude

    # --- Методы для сериализации ---
    def to_dict(self) -> dict:
        """Преобразует объект в словарь для JSON/CSV."""
        return {
            'icao24': self._icao24,
            'callsign': self._callsign,
            'origin_country': self._origin_country,
            'longitude': self._longitude,
            'latitude': self._latitude,
            'altitude': self._altitude,
            'on_ground': self._on_ground,
            'velocity': self._velocity,
            'heading': self._heading
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Aircraft':
        """Создаёт объект Aircraft из словаря."""
        return cls(
            icao24=data['icao24'],
            callsign=data.get('callsign'),
            origin_country=data.get('origin_country', ''),
            longitude=data.get('longitude', 0.0),
            latitude=data.get('latitude', 0.0),
            altitude=data.get('altitude', 0.0),
            on_ground=data.get('on_ground', False),
            velocity=data.get('velocity'),
            heading=data.get('heading')
        )

    def __repr__(self):
        return f"Aircraft(icao24={self._icao24}, altitude={self._altitude})"