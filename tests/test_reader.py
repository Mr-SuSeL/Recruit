import pytest
import datetime
from unittest.mock import MagicMock, patch

from profil_logger.logger import LogEntry, ProfilLoggerReader, LogLevel
from profil_logger.handlers import JsonHandler # Poprawiona nazwa klasy handlera JSON

# ---
# Fixture dla przykładowych LogEntry
# ---
@pytest.fixture
def sample_log_entries():
    """
    Dostarcza listę obiektów LogEntry dla testów.
    """
    return [
        LogEntry(datetime.datetime(2023, 1, 1, 10, 0, 0), "INFO", "User logged in."),
        LogEntry(datetime.datetime(2023, 1, 1, 10, 5, 0), "WARNING", "Low disk space."),
        LogEntry(datetime.datetime(2023, 1, 1, 10, 15, 0), "INFO", "Application started successfully."),
        LogEntry(datetime.datetime(2023, 1, 2, 11, 0, 0), "ERROR", "Database connection failed."),
        LogEntry(datetime.datetime(2023, 1, 2, 11, 30, 0), "DEBUG", "System heartbeat check."),
        LogEntry(datetime.datetime(2023, 1, 3, 12, 0, 0), "CRITICAL", "Disk full, system halted."),
    ]

# ---
# Fixture dla mockowanego handlera z gotowymi danymi
# ---
@pytest.fixture
def mock_handler_with_data(sample_log_entries):
    """
    Fixtura dla mockowanego handlera JsonHandler.
    Symuluje pobieranie danych i ich konwersję na słowniki.
    """
    # Użycie JsonHandler, który posiada metodę retrieve_all_logs_json
    handler = MagicMock(spec=JsonHandler)

    # Mockowanie metody pobierającej logi jako listę słowników
    handler.retrieve_all_logs_json.return_value = [log.to_dict() for log in sample_log_entries]

    # Mockowanie metody informującej ProfilLoggerReader o dostępnych sposobach pobierania
    handler._get_supported_retrieve_methods.return_value = ["retrieve_all_logs_json"]

    return handler

# ---
# Fixture dla ProfilLoggerReader
# ---
@pytest.fixture
def profil_logger_reader(mock_handler_with_data):
    """Dostarcza instancję ProfilLoggerReader z zamockowanym handlerem."""
    return ProfilLoggerReader(handler=mock_handler_with_data)

# ---
# Testy funkcjonalności ProfilLoggerReader
# ---

def test_find_by_text_returns_correct_logs(profil_logger_reader):
    """Testuje wyszukiwanie logów po fragmencie tekstu (case-insensitive i case-sensitive)."""
    results = profil_logger_reader.find_by_text("user logged", case_sensitive=False)
    assert len(results) == 1
    assert results[0].message == "User logged in."

    results_sensitive = profil_logger_reader.find_by_text("database", case_sensitive=True)
    assert len(results_sensitive) == 0

    results_sensitive_correct = profil_logger_reader.find_by_text("Database", case_sensitive=True)
    assert len(results_sensitive_correct) == 1
    assert results_sensitive_correct[0].message == "Database connection failed."


def test_find_by_level_returns_correct_logs(profil_logger_reader):
    """Testuje wyszukiwanie logów po poziomie (również z uwzględnieniem wielkości liter)."""
    info_logs = profil_logger_reader.find_by_level("INFO")
    assert len(info_logs) == 2
    assert all(log.level == "INFO" for log in info_logs)
    assert "User logged in." in [log.message for log in info_logs]
    assert "Application started successfully." in [log.message for log in info_logs]

    error_logs = profil_logger_reader.find_by_level("error")
    assert len(error_logs) == 1
    assert error_logs[0].level == "ERROR"
    assert error_logs[0].message == "Database connection failed."

    critical_logs = profil_logger_reader.find_by_level("CRITICAL")
    assert len(critical_logs) == 1
    assert critical_logs[0].level == "CRITICAL"
    assert critical_logs[0].message == "Disk full, system halted."

def test_find_by_date_range_returns_correct_logs(profil_logger_reader):
    """Testuje wyszukiwanie logów w podanym zakresie dat."""
    start_date = datetime.datetime(2023, 1, 1, 9, 0, 0)
    end_date = datetime.datetime(2023, 1, 1, 10, 30, 0)
    results = profil_logger_reader.find_by_date_range(start_date, end_date)
    assert len(results) == 3

    messages = [log.message for log in results]
    assert "User logged in." in messages
    assert "Low disk space." in messages
    assert "Application started successfully." in messages

    assert all(start_date <= log.date <= end_date for log in results)


def test_groupby_level_groups_logs_correctly(profil_logger_reader):
    """Testuje grupowanie logów według poziomu."""
    grouped_logs = profil_logger_reader.groupby_level()

    assert "INFO" in grouped_logs
    assert "WARNING" in grouped_logs
    assert "ERROR" in grouped_logs
    assert "DEBUG" in grouped_logs
    assert "CRITICAL" in grouped_logs

    assert len(grouped_logs["INFO"]) == 2
    assert len(grouped_logs["WARNING"]) == 1
    assert len(grouped_logs["ERROR"]) == 1
    assert len(grouped_logs["DEBUG"]) == 1
    assert len(grouped_logs["CRITICAL"]) == 1

    info_messages = [log.message for log in grouped_logs["INFO"]]
    assert "User logged in." in info_messages
    assert "Application started successfully." in info_messages

def test_sort_by_date_ascending_orders_correctly(profil_logger_reader):
    """Testuje sortowanie logów rosnąco po dacie."""
    sorted_logs = profil_logger_reader.sort_by_date(ascending=True)
    assert len(sorted_logs) == 6

    for i in range(len(sorted_logs) - 1):
        assert sorted_logs[i].date <= sorted_logs[i+1].date

    assert sorted_logs[0].message == "User logged in."
    assert sorted_logs[1].message == "Low disk space."
    assert sorted_logs[2].message == "Application started successfully."
    assert sorted_logs[3].message == "Database connection failed."
    assert sorted_logs[4].message == "System heartbeat check."
    assert sorted_logs[5].message == "Disk full, system halted."


def test_sort_by_date_descending_orders_correctly(profil_logger_reader):
    """Testuje sortowanie logów malejąco po dacie."""
    sorted_logs = profil_logger_reader.sort_by_date(ascending=False)
    assert len(sorted_logs) == 6

    for i in range(len(sorted_logs) - 1):
        assert sorted_logs[i].date >= sorted_logs[i+1].date

    assert sorted_logs[0].message == "Disk full, system halted."
    assert sorted_logs[1].message == "System heartbeat check."
    assert sorted_logs[2].message == "Database connection failed."
    assert sorted_logs[3].message == "Application started successfully."
    assert sorted_logs[4].message == "Low disk space."
    assert sorted_logs[5].message == "User logged in."