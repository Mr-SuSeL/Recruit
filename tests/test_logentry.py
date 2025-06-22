import datetime
import pytest
from profil_logger.logger import LogEntry, LogLevel # Ważne: upewnij się, że LogLevel jest również zaimportowany, jeśli go używasz

def test_log_entry_initialization():
    """Test that LogEntry can be initialized correctly."""
    now = datetime.datetime.now()
    entry = LogEntry(date=now, level="INFO", message="Test message") # ZMIANA: msg na message
    assert entry.date == now
    assert entry.level == "INFO"
    assert entry.message == "Test message"

def test_log_entry_str_representation():
    """Test the string representation of a LogEntry."""
    test_date = datetime.datetime(2023, 1, 15, 10, 30, 0)
    entry = LogEntry(date=test_date, level="WARNING", message="Something happened.") # ZMIANA: msg na message
    expected_str = f"[{test_date.isoformat()}] WARNING: Something happened."
    assert str(entry) == expected_str

def test_log_entry_repr_representation():
    """Test the developer-friendly representation of a LogEntry."""
    test_date = datetime.datetime(2023, 1, 15, 10, 30, 0)
    entry = LogEntry(date=test_date, level="ERROR", message="Critical error!") # ZMIANA: msg na message
    expected_repr = (
        f"LogEntry(date={test_date!r}, " # Użycie !r dla daty zapewnia poprawny repr
        f"level={'ERROR'!r}, message={'Critical error!'!r})" # ZMIANA: msg na message i dostosowanie klucza w repr
    )
    assert repr(entry) == expected_repr

def test_log_entry_to_dict():
    """Test conversion of LogEntry to a dictionary."""
    test_date = datetime.datetime(2023, 1, 15, 11, 0, 0)
    entry = LogEntry(date=test_date, level="INFO", message="Data point.") # ZMIANA: msg na message
    expected_dict = {
        "date": test_date.isoformat(),
        "level": "INFO",
        "message": "Data point.",
    }
    assert entry.to_dict() == expected_dict

def test_log_entry_from_dict():
    """Test creation of LogEntry from a dictionary."""
    test_date_str = "2023-01-15T12:00:00"
    data_dict = {
        "date": test_date_str,
        "level": "DEBUG",
        "message": "Debugging info.", # Upewnij się, że ten klucz jest 'message' w słowniku
    }
    entry = LogEntry.from_dict(data_dict)
    assert entry.date == datetime.datetime.fromisoformat(test_date_str)
    assert entry.level == "DEBUG"
    assert entry.message == "Debugging info."

def test_log_entry_from_dict_invalid_date_format():
    """Test from_dict with an invalid date format."""
    data_dict = {
        "date": "invalid-date",
        "level": "INFO",
        "message": "Some message", # ZMIANA: msg na message
    }
    with pytest.raises(ValueError):
        LogEntry.from_dict(data_dict)

def test_log_entry_from_dict_missing_keys():
    """Test from_dict with missing keys."""
    data_dict = {
        "level": "INFO",
        "message": "Some message", # ZMIANA: msg na message. Oczekiwana jest tu ValueError, nie KeyError.
    }
    # LogEntry.from_dict sprawdza 'date', 'level', 'message'.
    # Jeśli 'date' brakuje, to podniesie ValueError zgodnie z Twoją implementacją LogEntry.from_dict.
    # W Twoim poprzednim logu błędu było: ValueError: Missing keys in log entry dictionary.
    # Zmieniam oczekiwany wyjątek z KeyError na ValueError, aby był zgodny z kodem LogEntry.from_dict.
    with pytest.raises(ValueError):
        LogEntry.from_dict(data_dict)