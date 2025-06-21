import csv
import datetime
import json
import os
import sqlite3

from .logger import LogEntry


class JsonHandler:
    """Handles logging to a JSON file.

    This handler manages the persistence and retrieval of log entries
    in a structured JSON format. Each log entry is stored as a JSON object
    within a list in the specified file.

    Attributes:
        filepath (str): The path to the JSON log file.

    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.filepath) or '.', exist_ok=True)
        # Create an empty file if it doesn't exist or is empty to ensure valid JSON structure
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, "w") as f:
                json.dump([], f) # Initialize with an empty JSON array

    def persist_log_json(self, entry: LogEntry):
        """Persist a single log entry to the JSON file.

        This method appends a new LogEntry object to the JSON file.
        It reads existing logs, adds the new entry, and writes the updated list
        back to the file.

        Args:
            entry (LogEntry): The log entry object to persist.

        """
        all_logs_data = []
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath) as f_in:
                    all_logs_data = json.load(f_in)
        except (json.JSONDecodeError, FileNotFoundError):
            # Handle cases where the file is empty, corrupted, or not found
            all_logs_data = []

        all_logs_data.append(entry.to_dict())

        with open(self.filepath, "w") as f_out:
            json.dump(all_logs_data, f_out, indent=4)

    def retrieve_all_logs_json(self) -> list[LogEntry]:
        """Retrieve all log entries from the JSON file.

        This method reads all log entries from the specified JSON file
        and converts them into a list of LogEntry objects.

        Returns:
            list[LogEntry]: A list of all LogEntry objects found in the file.

        """
        log_entries_list = []
        try:
            with open(self.filepath) as f:
                data_dicts_list = json.load(f)
                for entry_dict_item in data_dicts_list:
                    log_entry = LogEntry.from_dict(entry_dict_item)
                    log_entries_list.append(log_entry)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        return log_entries_list

class CSVHandler:
    """Handles logging to a CSV file.

    This handler manages the persistence and retrieval of log entries
    in a comma-separated values (CSV) format. Each log entry is represented
    as a row in the CSV file.

    Attributes:
        filepath (str): The path to the CSV log file.
        fieldnames (list[str]): The column headers for the CSV file.

    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.fieldnames = ["date", "level", "message"]
        os.makedirs(os.path.dirname(self.filepath) or '.', exist_ok=True)
        # Ensure header is written only if file is new/empty
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def persist_log_csv(self, entry: LogEntry):
        """Persist a single log entry to the CSV file.

        This method appends a new LogEntry object as a row to the CSV file.
        It ensures that the CSV header is present.

        Args:
            entry (LogEntry): The log entry object to persist.

        """
        with open(self.filepath, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(entry.to_dict())

    def retrieve_all_logs_csv(self) -> list[LogEntry]:
        """Retrieve all log entries from the CSV file.

        This method reads all log entries from the specified CSV file
        and converts them into a list of LogEntry objects.

        Returns:
            list[LogEntry]: A list of all LogEntry objects found in the file.

        """
        log_entries_list = []
        try:
            with open(self.filepath, newline="") as f:
                reader = csv.DictReader(f)
                for row_as_dict in reader:
                    log_entry = LogEntry.from_dict(row_as_dict)
                    log_entries_list.append(log_entry)
        except (FileNotFoundError, csv.Error):
            return []
        return log_entries_list

class FileHandler:
    """Handles logging to a plain text file.

    This handler writes log entries as plain text lines to a specified file.
    Each line contains the timestamp, log level, and message.

    Attributes:
        filepath (str): The path to the text log file.

    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath) or '.', exist_ok=True)
        # Create an empty file if it doesn't exist
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w"):
                pass

    def persist_log_file(self, entry: LogEntry):
        """Persist a single log entry to the text file.

        This method appends a new LogEntry object as a formatted string
        to the text file.

        Args:
            entry (LogEntry): The log entry object to persist.

        """
        log_line = f"{entry.date.isoformat()} {entry.level} {entry.message}\n"
        with open(self.filepath, "a") as f:
            f.write(log_line)

    def retrieve_all_logs_file(self) -> list[LogEntry]:
        """Retrieve all log entries from the text file.

        This method reads all log entries line by line from the text file,
        parses them, and converts them into LogEntry objects.

        Returns:
            list[LogEntry]: A list of all LogEntry objects found in the file.

        """
        log_entries_list = []
        try:
            with open(self.filepath) as f:
                for line_content_str in f.readlines():
                    parts = line_content_str.strip().split(" ", 2)
                    expected_parts_count = 3
                    if len(parts) == expected_parts_count:
                        log_entry = LogEntry(
                            date=datetime.datetime.fromisoformat(parts[0]),
                            level=parts[1],
                            msg=parts[2],
                        )
                        log_entries_list.append(log_entry)
        except (FileNotFoundError, ValueError):
            return []
        return log_entries_list

class SQLLiteHandler:
    """Handles logging to an SQLite database.

    This handler manages the persistence and retrieval of log entries
    in an SQLite database. Log entries are stored in a specified table.

    Attributes:
        db_path (str): The path to the SQLite database file.
        table_name (str): The name of the table within the database to store logs.

    """

    # Define a set of allowed table names to prevent S608
    _ALLOWED_TABLE_NAMES = {"logs", "other_logs", "debug_logs"}

    def __init__(self, db_path: str, table_name: str = "logs"):
        self.db_path = db_path
        # Validate table_name against a whitelist to prevent S608 warning
        if table_name not in self._ALLOWED_TABLE_NAMES:
            raise ValueError(f"Table name '{table_name}' is not allowed.")
        self.table_name = table_name
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self._create_table_if_not_exists()

    def _get_conn(self) -> sqlite3.Connection:
        """Establish and return a SQLite database connection."""
        return sqlite3.connect(self.db_path)

    def _create_table_if_not_exists(self):
        """Create the log table if it doesn't already exist."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Table name is now validated in __init__
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            conn.commit()

    def persist_log_sql(self, entry: LogEntry):
        """Persist a single log entry to the SQLite database.

        Args:
            entry (LogEntry): The log entry object to persist.

        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # S608: Table name is safe because it's validated against a whitelist in __init__
            sql_query = (
                f"INSERT INTO {self.table_name} (timestamp, level, message) "
                "VALUES (?, ?, ?)"
            )
            cursor.execute(sql_query, (entry.date.isoformat(), entry.level, entry.message))
            conn.commit()

    def retrieve_all_logs_sql(self) -> list[LogEntry]:
        """Retrieve all log entries from the SQLite database.

        Returns:
            list[LogEntry]: A list of all LogEntry objects found in the database.

        """
        log_entries_list = []
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                # S608: Table name is safe because it's validated against a whitelist in __init__
                cursor.execute(
                    f"SELECT timestamp, level, message FROM {self.table_name} "
                    "ORDER BY timestamp ASC",
                )
                for row in cursor.fetchall():
                    log_entry = LogEntry(
                        date=datetime.datetime.fromisoformat(row[0]),
                        level=row[1],
                        msg=row[2],
                    )
                    log_entries_list.append(log_entry)
        except (sqlite3.Error, ValueError):
            return []
        return log_entries_list
