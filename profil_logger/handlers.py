# profil_logger/handlers.py
import csv
import datetime
import json
import os
import sqlite3
from contextlib import contextmanager # Dodano import contextmanager

from .logger import LogEntry, Handler


class JsonHandler(Handler): # PRZYWRÓCONO NAZWĘ KLASY
    """Handles logging to a JSON file."""
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filepath = os.path.join(self.output_dir, f"log_{datetime.date.today().isoformat()}.json")
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, "w", encoding='utf-8') as f:
                json.dump([], f)

    def write(self, entry: LogEntry):
        all_logs_data = []
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath, "r", encoding='utf-8') as f_in:
                    all_logs_data = json.load(f_in)
        except (json.JSONDecodeError, FileNotFoundError):
            all_logs_data = []
        all_logs_data.append(entry.to_dict())
        with open(self.filepath, "w", encoding='utf-8') as f_out:
            json.dump(all_logs_data, f_out, indent=4, ensure_ascii=False)

    def retrieve_all_logs_json(self) -> list[dict]:
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath, encoding='utf-8') as f:
                    data_dicts_list = json.load(f)
                    return data_dicts_list
            return []
        except json.JSONDecodeError:
            print(f"ERROR: JSON file {self.filepath} is corrupted or empty. Returning empty list.")
            return []
        except FileNotFoundError:
            return []


class CSVHandler(Handler): # PRZYWRÓCONO NAZWĘ KLASY
    """Handles logging to a CSV file."""
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.fieldnames = ["date", "level", "message"]
        os.makedirs(self.output_dir, exist_ok=True)
        self.filepath = os.path.join(self.output_dir, f"log_{datetime.date.today().isoformat()}.csv")
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, "w", newline="", encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def write(self, entry: LogEntry):
        with open(self.filepath, "a", newline="", encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(entry.to_dict())

    def retrieve_all_logs_csv(self) -> list[dict]:
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath, newline="", encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            return []
        except (FileNotFoundError, csv.Error):
            return []


class FileHandler(Handler): # PRZYWRÓCONO NAZWĘ KLASY
    """Handles logging to a plain text file."""
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filepath = os.path.join(self.output_dir, f"log_{datetime.date.today().isoformat()}.log")
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding='utf-8'):
                pass

    def write(self, entry: LogEntry):
        log_line = f"[{entry.date.isoformat()}] {entry.level}: {entry.message}\n"
        with open(self.filepath, "a", encoding='utf-8') as f:
            f.write(log_line)

    def retrieve_all_logs_file(self) -> list[dict]:
        log_entries_dicts_list = []
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath, encoding='utf-8') as f:
                    for line_content_str in f.readlines():
                        parts = line_content_str.strip().split(" ", 2)
                        if len(parts) == 3:
                            date_str = parts[0][1:-1]
                            level_str = parts[1][:-1]
                            message_str = parts[2]
                            log_entries_dicts_list.append({
                                "date": date_str,
                                "level": level_str,
                                "message": message_str,
                            })
            return log_entries_dicts_list
        except (FileNotFoundError, ValueError, IndexError):
            return []


class SQLLiteHandler(Handler): # PRZYWRÓCONO NAZWĘ KLASY
    """Handles logging to an SQLite database."""
    _ALLOWED_TABLE_NAMES = {"logs", "other_logs", "debug_logs", "app_events"}

    def __init__(self, db_path: str, table_name: str = "logs"):
        self.db_path = db_path
        if table_name not in self._ALLOWED_TABLE_NAMES:
            raise ValueError(f"Table name '{table_name}' is not allowed for security reasons.")
        self.table_name = table_name
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self._create_table_if_not_exists()

    @contextmanager # Użycie contextmanager dla pewniejszego zamykania
    def _get_conn_context(self) -> sqlite3.Connection:
        """Provide a SQLite database connection within a context."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _create_table_if_not_exists(self):
        """Create the log table if it doesn't already exist."""
        with self._get_conn_context() as conn: # Użycie kontekstu
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            conn.commit()

    def write(self, entry: LogEntry):
        """Persist a single log entry to the SQLite database."""
        with self._get_conn_context() as conn: # Użycie kontekstu
            cursor = conn.cursor()
            sql_query = (
                f"INSERT INTO {self.table_name} (timestamp, level, message) "
                "VALUES (?, ?, ?)"
            )
            cursor.execute(sql_query, (entry.date.isoformat(), entry.level, entry.message))
            conn.commit()

    def retrieve_all_logs_sql(self) -> list[dict]:
        """Retrieve all log entries from the SQLite database."""
        log_entries_dicts_list = []
        try:
            with self._get_conn_context() as conn: # Użycie kontekstu
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT timestamp, level, message FROM {self.table_name} "
                    "ORDER BY timestamp ASC",
                )
                for row in cursor.fetchall():
                    log_entries_dicts_list.append({
                        "date": row[0],
                        "level": row[1],
                        "message": row[2],
                    })
            return log_entries_dicts_list
        except sqlite3.Error:
            print(f"ERROR: SQLite database error during retrieval from {self.db_path}.")
            return []