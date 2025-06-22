import datetime
import inspect
from typing import Literal, get_args

# Definicja typów poziomów logowania
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class LogEntry:
    """Reprezentuje pojedynczy wpis w logu."""

    def __init__(self, date: datetime.datetime, level: LogLevel, message: str) -> None:
        if not isinstance(date, datetime.datetime):
            raise TypeError("Date must be a datetime object.")
        if level not in get_args(LogLevel):
            raise ValueError(f"Invalid log level: {level}. Must be one of {get_args(LogLevel)}")
        if not isinstance(message, str):
            raise TypeError("Message must be a string.")

        self.date = date
        self.level = level
        self.message = message

    def to_dict(self) -> dict[str, str]:
        """Konwertuje LogEntry na słownik."""
        return {
            "date": self.date.isoformat(),
            "level": self.level,
            "message": self.message
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "LogEntry":
        """Tworzy LogEntry ze słownika."""
        if not all(k in data for k in ["date", "level", "message"]):
            raise ValueError("Missing keys in log entry dictionary.")
        
        try:
            date_obj = datetime.datetime.fromisoformat(data["date"])
        except ValueError as e:
            raise ValueError(f"Invalid date format: {data['date']}. Expected ISO format.") from e
            
        return cls(date_obj, data["level"], data["message"])

    def __str__(self) -> str:
        """Zwraca czytelną reprezentację LogEntry."""
        return f"[{self.date.isoformat()}] {self.level}: {self.message}"

    def __repr__(self) -> str:
        """Zwraca reprezentację LogEntry dla deweloperów."""
        return f"LogEntry(date={self.date!r}, level={self.level!r}, message={self.message!r})"


class Handler:
    """
    Bazowa klasa dla handlerów logów. 
    Wszystkie handlery muszą dziedziczyć z tej klasy i implementować metodę 'write'.
    """

    def write(self, log_entry: LogEntry) -> None:
        """
        Zapisuje wpis logu. Musi być zaimplementowana przez podklasy.
        """
        raise NotImplementedError("Subclasses must implement 'write' method.")

    def _get_supported_retrieve_methods(self) -> list[str]:
        """
        Pobiera listę nazw metod 'retrieve_all_logs_X' zaimplementowanych w handlerze.
        """
        supported_methods = []
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name.startswith("retrieve_all_logs_"):
                supported_methods.append(name)
        return supported_methods


class ProfilLogger:
    """Główna klasa do logowania wiadomości."""

    _LOG_LEVELS: dict[LogLevel, int] = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3,
        "CRITICAL": 4
    }

    def __init__(self, handlers: list[Handler]) -> None:
        self.handlers = handlers
        self.log_level: LogLevel = "INFO"  # Domyślny poziom logowania

    def set_log_level(self, level: LogLevel) -> None:
        """
        Ustawia minimalny poziom logowania. Wiadomości o niższym priorytecie
        nie będą logowane.
        """
        # Sprawdzamy, czy podany poziom jest jednym z dozwolonych literałów
        if level.upper() not in get_args(LogLevel):
            raise ValueError(f"Unknown log level: '{level}'. Must be one of {get_args(LogLevel)}")
        
        # PRZYKŁAD KOREKTY: Bezpośrednie przypisanie stringa
        self.log_level = level.upper()  # Ustawiamy poziom jako string (np. "INFO", "DEBUG")

    def _should_log(self, level: LogLevel) -> bool:
        """Sprawdza, czy wiadomość powinna być zalogowana zgodnie z ustawionym poziomem."""
        return self._LOG_LEVELS.get(level, -1) >= self._LOG_LEVELS.get(self.log_level, 0)

    def _log(self, level: LogLevel, message: str) -> None:
        """Wewnętrzna metoda do tworzenia LogEntry i przekazywania go do handlerów."""
        if self._should_log(level):
            entry = LogEntry(datetime.datetime.now(), level, message)
            for handler in self.handlers:
                try:
                    handler.write(entry)
                except Exception as e:
                    # Tutaj możesz logować błędy handlera do konsoli lub innego awaryjnego miejsca
                    print(f"ERROR: Failed to persist log with {handler.__class__.__name__}: {e}")

    def debug(self, message: str) -> None:
        """Loguje wiadomość na poziomie DEBUG."""
        self._log("DEBUG", message)

    def info(self, message: str) -> None:
        """Loguje wiadomość na poziomie INFO."""
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        """Loguje wiadomość na poziomie WARNING."""
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        """Loguje wiadomość na poziomie ERROR."""
        self._log("ERROR", message)

    def critical(self, message: str) -> None:
        """Loguje wiadomość na poziomie CRITICAL."""
        self._log("CRITICAL", message)


class ProfilLoggerReader:
    """Klasa do odczytywania i filtrowania logów z handlerów."""

    def __init__(self, handler: Handler) -> None:
        self.handler = handler

    def _get_all_logs_from_handler(self) -> list[LogEntry]:
        """
        Pobiera wszystkie logi z przypisanego handlera, próbując dostępnych metod retrieve.
        """
        supported_methods = self.handler._get_supported_retrieve_methods()
        
        # Priorytetowanie JSON, następnie CSV, następnie File, następnie SQL
        priority_order = ["retrieve_all_logs_json", "retrieve_all_logs_csv", 
                          "retrieve_all_logs_file", "retrieve_all_logs_sql"]
                          
        for method_name in priority_order:
            if method_name in supported_methods:
                retrieve_method = getattr(self.handler, method_name)
                try:
                    logs_data = retrieve_method()
                    return [LogEntry.from_dict(d) if isinstance(d, dict) else d for d in logs_data]
                except Exception as e:
                    print(f"WARNING: Failed to retrieve logs using {method_name} from {self.handler.__class__.__name__}: {e}")
                    # Możesz zdecydować, czy kontynuować próbowanie innych metod po błędzie
                    continue # Kontynuuj do następnej metody, jeśli jedna zawiedzie
        
        print(f"ERROR: No working retrieve method found for {self.handler.__class__.__name__}.")
        return [] # Zwróć pustą listę, jeśli żadna metoda nie zadziałała

    def find_by_text(self, text: str, case_sensitive: bool = False) -> list[LogEntry]:
        """Wyszukuje logi zawierające dany tekst."""
        all_logs = self._get_all_logs_from_handler()
        
        if not case_sensitive:
            text = text.lower()
        
        found_logs = []
        for log in all_logs:
            message_to_check = log.message if case_sensitive else log.message.lower()
            if text in message_to_check:
                found_logs.append(log)
        return found_logs

    def find_by_level(self, level: str) -> list[LogEntry]:
        """Wyszukuje logi o danym poziomie."""
        all_logs = self._get_all_logs_from_handler()
        target_level = level.upper() # Normalizacja do wielkich liter
        
        if target_level not in get_args(LogLevel):
            print(f"WARNING: Invalid log level '{level}' provided for search. Valid levels are: {get_args(LogLevel)}")
            return []

        return [log for log in all_logs if log.level == target_level]

    def find_by_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime) -> list[LogEntry]:
        """Wyszukuje logi w określonym zakresie dat."""
        all_logs = self._get_all_logs_from_handler()
        return [log for log in all_logs if start_date <= log.date <= end_date]

    def groupby_level(self) -> dict[LogLevel, list[LogEntry]]:
        """Grupuej logi według poziomu."""
        all_logs = self._get_all_logs_from_handler()
        grouped_logs: dict[LogLevel, list[LogEntry]] = {level: [] for level in get_args(LogLevel)}
        
        for log in all_logs:
            if log.level in grouped_logs:
                grouped_logs[log.level].append(log)
        return grouped_logs

    def sort_by_date(self, ascending: bool = True) -> list[LogEntry]:
        """Sortuje logi według daty."""
        all_logs = self._get_all_logs_from_handler()
        return sorted(all_logs, key=lambda log: log.date, reverse=not ascending)