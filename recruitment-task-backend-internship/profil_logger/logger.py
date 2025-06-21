import datetime
import threading
import re
from typing import List, Optional, Dict, Any

LOG_LEVEL_VALUES = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
DEFAULT_LOG_LEVEL = "DEBUG"


class LogEntry:
    def __init__(self, date: datetime.datetime, level: str, msg: str):
        self.date = date
        self.level = msg
        self.message = msg

    def __repr__(self):
        return f"LogEntry(date={self.date.isoformat()}, level='{self.level}', msg='{self.message}')"

    def to_dict(self) -> dict:
        return {"date": self.date.isoformat(), "level": self.level, "msg": self.message}

    @staticmethod
    def from_dict(data: Dict[str, str]) -> 'LogEntry':
        return LogEntry(date=datetime.datetime.fromisoformat(data['date']), level=data['level'], msg=data['msg'])


class ProfilLogger:
    def __init__(self, handlers: List[Any]):
        self.handlers = handlers
        self.current_log_level_val = LOG_LEVEL_VALUES[DEFAULT_LOG_LEVEL]

    def _log(self, level: str, msg: str):
        if LOG_LEVEL_VALUES[level] < self.current_log_level_val:
            return
        entry = LogEntry(date=datetime.datetime.now(), level=level, msg=msg)
        for handler_item in self.handlers:
            self._write_to_handler(handler_item, entry)

    def _write_to_handler(self, handler: Any, entry: LogEntry):
        try:
            try:
                handler.persist_log_sql(entry)
            except AttributeError:
                try:
                    handler.persist_log_json(entry)
                except AttributeError:
                    handler.persist_log_csv(entry)
        except Exception as e:
            try:
                handler.persist_log_file(entry)
            except Exception as final_e:
                 print(f"ERROR: All handlers failed. Final error on {type(handler).__name__}: {final_e}")


    def info(self, msg: str): self._log("INFO", msg)
    def warning(self, msg: str): self._log("WARNING", msg)
    def critical(self, msg: str): self._log("CRITICAL", msg)
    def error(self, msg: str): self._log("ERROR", msg)
    def debug(self, msg: str): self._log("DEBUG", msg)

    def set_log_level(self, level: str):
        self.current_log_level_val = LOG_LEVEL_VALUES.get(level.upper(), self.current_log_level_val)


class ProfilLoggerReader:
    def __init__(self, handler: Any):
        self.handler = handler

    def _get_all_logs_from_handler(self) -> List[LogEntry]:
        try: 
            return self.handler.retrieve_all_logs_sql()
        except AttributeError:
            try: return self.handler.retrieve_all_logs_json()
            except AttributeError:
                try: return self.handler.retrieve_all_logs_csv()
                except AttributeError:
                    try: return self.handler.retrieve_all_logs_file()
                    except AttributeError:
                        print(f"ERROR: Handler {type(self.handler).__name__} has no recognized retrieval method.")
                        return []

    def _filter_by_date(self, logs: List[LogEntry], start_date: Optional[datetime.datetime] = None,
                        end_date: Optional[datetime.datetime] = None) -> List[LogEntry]:
        if not start_date and not end_date:
            return logs
        to_remove = [log for log in logs if (start_date and log.date < start_date) or (end_date and log.date >= end_date)]
        for item in to_remove:
            logs.remove(item)
        return logs

    def find_by_text(self, text: str, start_date=None, end_date=None) -> List[LogEntry]:
        all_logs = self._get_all_logs_from_handler()
        result_logs = [log for log in all_logs if text in log.message]
        return self._filter_by_date(result_logs, start_date, end_date)

    def find_by_regex(self, regex: str, start_date=None, end_date=None) -> List[LogEntry]:
        all_logs = self._get_all_logs_from_handler()
        try:
            pattern = re.compile(regex)
            matching_logs = [log for log in all_logs if pattern.search(log.message)]
            return self._filter_by_date(matching_logs, start_date, end_date)
        except re.error:
            return []

    def groupby_level(self, start_date=None, end_date=None) -> Dict[str, List[LogEntry]]:
        all_logs = self._get_all_logs_from_handler()
        logs_to_group = self._filter_by_date(all_logs, start_date, end_date)

        unique_levels = []
        for log_entry in logs_to_group:
            if log_entry.level not in unique_levels:
                unique_levels.append(log_entry.level)

        grouped_logs_map = {}
        for level_key in unique_levels:
            current_level_logs = []
            for log_entry in logs_to_group:
                if log_entry.level == level_key:
                    current_level_logs.append(log_entry)
            
            if current_level_logs:
                grouped_logs_map[level_key] = current_level_logs

        return grouped_logs_map

    def groupby_month(self, start_date=None, end_date=None) -> Dict[str, List[LogEntry]]:
        all_logs = self._get_all_logs_from_handler()
        logs_to_group = self._filter_by_date(all_logs, start_date, end_date)

        unique_month_year_keys = []
        for log_entry in logs_to_group:
            month_year_str = log_entry.date.strftime('%Y-%m')
            if month_year_str not in unique_month_year_keys:
                unique_month_year_keys.append(month_year_str)

        grouped_by_month_data = {}
        for month_key_str in unique_month_year_keys:
            logs_for_this_month = []
            for log_entry in logs_to_group:
                if log_entry.date.strftime('%Y-%m') == month_key_str:
                    logs_for_this_month.append(log_entry)
            
            if logs_for_this_month:
                grouped_by_month_data[month_key_str] = logs_for_this_month

        return grouped_by_month_data