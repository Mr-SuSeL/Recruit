import datetime
from collections import defaultdict
from typing import Any, Literal


class LogEntry:
    """Represents a single log entry with a timestamp, level, and message.

    This class encapsulates the data for a single log event, including
    when it occurred, its severity, and the message content.

    Attributes:
        date (datetime.datetime): The timestamp when the log entry was created.
        level (str): The severity level of the log entry (e.g., "INFO", "ERROR").
        message (str): The actual text content of the log.

    """

    def __str__(self) -> str:
        """Return a string representation of the log entry."""
        return f"[{self.date.isoformat()}] {self.level}: {self.message}"

    def __repr__(self) -> str:
        """Return a developer-friendly representation of the log entry."""
        return (
            f"LogEntry(date={self.date.isoformat()!r}, "
            f"level={self.level!r}, msg={self.message!r})"
        )

    def to_dict(self) -> dict:
        """Convert the log entry to a dictionary.

        This method serializes the LogEntry object into a dictionary
        suitable for JSON or CSV storage.

        Returns:
            dict: A dictionary representation of the log entry.

        """
        return {"date": self.date.isoformat(), "level": self.level, "msg": self.message}

    @staticmethod
    def from_dict(data: dict[str, str]) -> "LogEntry":
        """Create a LogEntry instance from a dictionary.

        This static method reconstructs a LogEntry object from a dictionary,
        typically used when reading logs from storage.

        Args:
            data (dict[str, str]): A dictionary containing 'date', 'level', and 'msg' keys.

        Returns:
            LogEntry: A new LogEntry instance.

        """
        return LogEntry(
            date=datetime.datetime.fromisoformat(data["date"]),
            level=data["level"],
            msg=data["msg"],
        )

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class ProfilLogger:
    """A logger that dispatches log entries to multiple handlers.

    This class provides an interface for logging messages at different
    severity levels. It supports multiple logging handlers (e.g., JSON, CSV,
    SQLite) to persist log entries.

    Attributes:
        handlers (list[Any]): A list of handler objects responsible for persisting logs.
        log_level (LogLevel): The minimum log level to process. Messages below this
                              level will be ignored.
        log_levels (dict[str, int]): A mapping of log level names to their integer priorities.

    """

    def __init__(self, handlers: list[Any]):
        self.handlers = handlers
        self.log_level: LogLevel = "INFO"
        self.log_levels = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }

    def _log(self, level: LogLevel, msg: str):
        """Process and dispatch a log entry to all registered handlers.

        This internal method checks if the given log level meets the
        configured minimum log level and, if so, creates a LogEntry
        and attempts to persist it using each handler.

        Args:
            level (LogLevel): The severity level of the log message.
            msg (str): The log message content.

        """
        if self.log_levels[level] >= self.log_levels[self.log_level]:
            entry = LogEntry(date=datetime.datetime.now(), level=level, msg=msg)
            for handler in self.handlers:
                try:
                    # Determine which persist method to call based on handler type
                    if hasattr(handler, "persist_log_json"):
                        handler.persist_log_json(entry)
                    elif hasattr(handler, "persist_log_csv"):
                        handler.persist_log_csv(entry)
                    elif hasattr(handler, "persist_log_file"):
                        handler.persist_log_file(entry)
                    elif hasattr(handler, "persist_log_sql"):
                        handler.persist_log_sql(entry)
                    else:
                        print(
                            f"WARNING: Handler {type(handler).__name__} has no "
                            "recognized persist method.",
                        )
                except Exception as e:
                    print(f"ERROR: Failed to persist log with {type(handler).__name__}: {e}")

    def info(self, msg: str):
        """Log an informational message."""
        self._log("INFO", msg)

    def warning(self, msg: str):
        """Log a warning message."""
        self._log("WARNING", msg)

    def critical(self, msg: str):
        """Log a critical message."""
        self._log("CRITICAL", msg)

    def error(self, msg: str):
        """Log an error message."""
        self._log("ERROR", msg)

    def debug(self, msg: str):
        """Log a debug message."""
        self._log("DEBUG", msg)

    def set_log_level(self, level: str):
        """Set the minimum log level for the logger.

        Messages with a severity lower than the set level will be ignored.

        Args:
            level (str): The desired minimum log level (e.g., "DEBUG", "INFO").
                         Case-insensitive.

        Raises:
            ValueError: If an unknown log level is provided.

        """
        upper_level = level.upper()
        if upper_level in self.log_levels:
            self.log_level = LogLevel(upper_level)
        else:
            raise ValueError(f"Unknown log level: {level}")

class ProfilLoggerReader:
    """A utility class to read and query log entries from various handlers.

    This class provides methods to retrieve, filter, and group log entries
    from different types of log handlers.

    Attributes:
        handler (Any): The log handler from which to read log entries.

    """

    def __init__(self, handler: Any):
        self.handler = handler

    def _get_all_logs_from_handler(self) -> list[LogEntry]:
        """Retrieve all log entries from the assigned handler.

        This internal method dynamically calls the appropriate retrieve method
        based on the handler's type.

        Returns:
            list[LogEntry]: A list of all LogEntry objects from the handler.

        """
        if hasattr(self.handler, "retrieve_all_logs_json"):
            return self.handler.retrieve_all_logs_json()
        if hasattr(self.handler, "retrieve_all_logs_csv"):
            return self.handler.retrieve_all_logs_csv()
        if hasattr(self.handler, "retrieve_all_logs_file"):
            return self.handler.retrieve_all_logs_file()
        if hasattr(self.handler, "retrieve_all_logs_sql"):
            return self.handler.retrieve_all_logs_sql()
        print(
            f"WARNING: Handler {type(self.handler).__name__} has no "
            "recognized retrieve method.",
        )
        return []

    def find_by_text(self, text: str, case_sensitive: bool = False) -> list[LogEntry]:
        """Find log entries containing specific text in their message.

        Args:
            text (str): The text to search for within log messages.
            case_sensitive (bool): If True, the search is case-sensitive. Defaults to False.

        Returns:
            list[LogEntry]: A list of LogEntry objects that contain the specified text.

        """
        all_logs = self._get_all_logs_from_handler()
        results = []
        for entry in all_logs:
            message_to_check = entry.message if case_sensitive else entry.message.lower()
            text_to_find = text if case_sensitive else text.lower()
            if text_to_find in message_to_check:
                results.append(entry)
        return results

    def find_by_level(self, level: str) -> list[LogEntry]:
        """Find log entries matching a specific log level.

        Args:
            level (str): The log level to filter by (e.g., "ERROR", "INFO"). Case-insensitive.

        Returns:
            list[LogEntry]: A list of LogEntry objects that match the specified level.

        """
        all_logs = self._get_all_logs_from_handler()
        results = []
        target_level_upper = level.upper()
        for entry in all_logs:
            if entry.level.upper() == target_level_upper:
                results.append(entry)
        return results

    def find_by_date_range(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[LogEntry]:
        """Find log entries within a specified date range.

        Args:
            start_date (datetime.datetime): The start of the date range (inclusive).
            end_date (datetime.datetime): The end of the date range (inclusive).

        Returns:
            list[LogEntry]: A list of LogEntry objects within the specified date range.

        """
        all_logs = self._get_all_logs_from_handler()
        results = []
        for entry in all_logs:
            if start_date <= entry.date <= end_date:
                results.append(entry)
        return results

    def groupby_level(self) -> dict[str, list[LogEntry]]:
        """Group log entries by their log level.

        Returns:
            dict[str, list[LogEntry]]: A dictionary where keys are log levels
                                       and values are lists of LogEntry objects for that level.

        """
        all_logs = self._get_all_logs_from_handler()
        grouped_logs: dict[str, list[LogEntry]] = defaultdict(list)
        for entry in all_logs:
            grouped_logs[entry.level].append(entry)
        return dict(grouped_logs)

    def sort_by_date(self, ascending: bool = True) -> list[LogEntry]:
        """Sort log entries by date.

        Args:
            ascending (bool): If True, sort in ascending order (oldest first).
                              If False, sort in descending order (newest first).
                              Defaults to True.

        Returns:
            list[LogEntry]: A new list of LogEntry objects sorted by date.

        """
        all_logs = self._get_all_logs_from_handler()
        return sorted(all_logs, key=lambda entry: entry.date, reverse=not ascending)
