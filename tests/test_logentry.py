import datetime
import pytest
from profil_logger.logger import LogEntry

def test_log_entry_initialization():
    """Test that LogEntry can be initialized correctly."""
    now = datetime.datetime.now()
    entry = LogEntry(date=now, level="INFO", msg="Test message")
    assert entry.date == now
    assert entry.level == "INFO"
    assert entry.message == "Test message"

def test_log_entry_str_representation():
    """Test the string representation of a LogEntry."""
    test_date = datetime.datetime(2023, 1, 15, 10, 30, 0)
    entry = LogEntry(date=test_date, level="WARNING", msg="Something happened.")
    expected_str = f"[{test_date.isoformat()}] WARNING: Something happened."
    assert str(entry) == expected_str

def test_log_entry_repr_representation():
    """Test the developer-friendly representation of a LogEntry."""
    test_date = datetime.datetime(2023, 1, 15, 10, 30, 0)
    entry = LogEntry(date=test_date, level="ERROR", msg="Critical error!")
    expected_repr = (
        f"LogEntry(date={test_date.isoformat()!r}, "
        f"level={'ERROR'!r}, msg={'Critical error!'!r})"
    )
    assert repr(entry) == expected_repr

def test_log_entry_to_dict():
    """Test conversion of LogEntry to a dictionary."""
    test_date = datetime.datetime(2023, 1, 15, 11, 0, 0)
    entry = LogEntry(date=test_date, level="INFO", msg="Data point.")
    expected_dict = {
        "date": test_date.isoformat(),
        "level": "INFO",
        "msg": "Data point.",
    }
    assert entry.to_dict() == expected_dict

def test_log_entry_from_dict():
    """Test creation of LogEntry from a dictionary."""
    test_date_str = "2023-01-15T12:00:00"
    data_dict = {
        "date": test_date_str,
        "level": "DEBUG",
        "msg": "Debugging info.",
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
        "msg": "Some message",
    }
    with pytest.raises(ValueError):
        LogEntry.from_dict(data_dict)

def test_log_entry_from_dict_missing_keys():
    """Test from_dict with missing keys."""
    data_dict = {
        "level": "INFO",
        "msg": "Some message",
    }
    with pytest.raises(KeyError):
        LogEntry.from_dict(data_dict)