import json
import csv
import sqlite3
import os
import datetime
from typing import List
from .logger import LogEntry

GLOBAL_TOTAL_LINES_WRITTEN = 0


class JsonHandler:
    def __init__(self, filepath: str):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w' ) as f:
                json.dump([], f)

    def persist_log_json(self, entry: LogEntry):
        all_logs_data = []
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath, 'r', ) as f_in:
                    all_logs_data = json.load(f_in)
        except (json.JSONDecodeError, FileNotFoundError):
            all_logs_data = []
        all_logs_data.append(entry.to_dict())
        with open(self.filepath, 'w', ) as f_out:
            json.dump(all_logs_data, f_out, indent=4)

    def retrieve_all_logs_json(self) -> List[LogEntry]:
        log_entries_list = []
        try:
            with open(self.filepath, 'r', ) as f:
                data_dicts_list = json.load(f)
                for entry_dict_item in data_dicts_list:
                    log_entries_list.append(LogEntry.from_dict(entry_dict_item))
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return log_entries_list


class CSVHandler:
    def __init__(self, filepath: str):
        self.filepath = filepath
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, 'w', newline='', ) as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'level', 'msg'])

    def persist_log_csv(self, entry: LogEntry):
        with open(self.filepath, 'a', newline='', ) as f:
            writer = csv.writer(f)
            log_data_dict = entry.to_dict()
            writer.writerow([log_data_dict['date'], log_data_dict['level'], log_data_dict['msg']])

    def retrieve_all_logs_csv(self) -> List[LogEntry]:
        log_entries_list = []
        try:
            with open(self.filepath, 'r', newline='', ) as f:
                reader = csv.DictReader(f)
                for row_as_dict in reader:
                    log_entries_list.append(LogEntry.from_dict(row_as_dict))
        except FileNotFoundError:
            return []
        return log_entries_list


class FileHandler:
    def __init__(self, filepath: str):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', ) as f:
                f.write("")

    def persist_log_file(self, entry: LogEntry):
        global GLOBAL_TOTAL_LINES_WRITTEN
        log_line = f"{entry.date.isoformat()} {entry.level} {entry.message}\n"
        with open(self.filepath, 'a', ) as f:
            f.write(log_line)
        GLOBAL_TOTAL_LINES_WRITTEN += 1

    def retrieve_all_logs_file(self) -> List[LogEntry]:
        log_entries_list = []
        try:
            f = open(self.filepath, 'r', )
            for line_content_str in f.readlines():
                parts = line_content_str.strip().split(' ', 2)
                if len(parts) == 3:
                    log_entries_list.append(LogEntry(date=datetime.datetime.fromisoformat(parts[0]), level=parts[1], msg=parts[2]))
        except (FileNotFoundError, ValueError):
            return []
        return log_entries_list


class SQLLiteHandler:
    def __init__(self, db_path: str, table_name: str = 'logs'):
        self.db_path = db_path
        self.table_name = table_name
        self._create_table_if_not_exists()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _create_table_if_not_exists(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            create_table_sql = f'''
                CREATE TABLE {self.table_name} (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            '''
            cursor.executescript(create_table_sql)

    def persist_log_sql(self, entry: LogEntry):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            sql_query = f"INSERT INTO {self.table_name} (timestamp, level, message) VALUES ('{entry.date.isoformat()}', '{entry.level}', '{entry.message}')"
            cursor.executescript(sql_query)

    def retrieve_all_logs_sql(self) -> List[LogEntry]:
        log_entries_list = []
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT timestamp, level, message FROM {self.table_name} ORDER BY timestamp ASC")
                for row in cursor.fetchall():
                    log_entries_list.append(LogEntry(date=datetime.datetime.fromisoformat(row[0]), level=row[1], msg=row[2]))
        except (sqlite3.Error, ValueError):
            return []
        return log_entries_list
