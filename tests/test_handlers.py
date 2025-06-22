import pytest
import datetime
import json
import csv
import os
import sqlite3

# Pamiętaj o poprawnym imporcie z Twojego pakietu profil_logger
from profil_logger.logger import LogEntry
from profil_logger.handlers import JsonHandler, CSVHandler, FileHandler, SQLLiteHandler

# Przykładowe dane LogEntry do użycia w testach
@pytest.fixture
def sample_log_entry():
    """Fixture to provide a sample LogEntry for tests."""
    return LogEntry(
        date=datetime.datetime(2023, 10, 26, 10, 30, 0, 0),
        level="INFO",
        msg="Test message for handler."
    )

# --- Testy dla JsonHandler ---
def test_json_handler_write(tmp_path, sample_log_entry):
    """Test that JsonHandler correctly writes a log entry to a JSON file."""
    output_dir = tmp_path / "json_logs"
    output_dir.mkdir() # Upewnij się, że katalog istnieje
    handler = JsonHandler(output_dir) # Przekazujemy katalog
    handler.write(sample_log_entry)

    # Scieżka do pliku jest teraz generowana dynamicznie w handlerze
    expected_file = output_dir / f"log_{datetime.date.today().isoformat()}.json"
    assert expected_file.exists()

    with open(expected_file, 'r') as f:
        content = json.load(f)
    assert len(content) == 1
    assert content[0] == sample_log_entry.to_dict()

def test_json_handler_append(tmp_path, sample_log_entry):
    """Test that JsonHandler appends to an existing JSON file."""
    output_dir = tmp_path / "json_append_logs"
    output_dir.mkdir()
    handler = JsonHandler(output_dir)

    # Write first entry
    handler.write(sample_log_entry)

    # Write second entry
    second_entry = LogEntry(
        date=datetime.datetime(2023, 10, 26, 10, 31, 0, 0),
        level="WARNING",
        msg="Another test message."
    )
    handler.write(second_entry)

    expected_file = output_dir / f"log_{datetime.date.today().isoformat()}.json"
    assert expected_file.exists()

    with open(expected_file, 'r') as f:
        content = json.load(f)
    assert len(content) == 2
    assert content[0] == sample_log_entry.to_dict()
    assert content[1] == second_entry.to_dict()

# --- Testy dla CSVHandler ---
def test_csv_handler_write(tmp_path, sample_log_entry):
    """Test that CSVHandler correctly writes a log entry to a CSV file."""
    output_dir = tmp_path / "csv_logs"
    output_dir.mkdir()
    handler = CSVHandler(output_dir) # Przekazujemy katalog
    handler.write(sample_log_entry)

    expected_file = output_dir / f"log_{datetime.date.today().isoformat()}.csv"
    assert expected_file.exists()

    with open(expected_file, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        data_row = next(reader)
    
    assert header == ["date", "level", "message"] # Poprawiono 'msg' na 'message' w nagłówku
    assert data_row == [str(sample_log_entry.date.isoformat()), sample_log_entry.level, sample_log_entry.message] # Dostosowano format daty i kolejność

def test_csv_handler_append(tmp_path, sample_log_entry):
    """Test that CSVHandler appends to an existing CSV file."""
    output_dir = tmp_path / "csv_append_logs"
    output_dir.mkdir()
    handler = CSVHandler(output_dir)

    # Write first entry
    handler.write(sample_log_entry)

    # Write second entry
    second_entry = LogEntry(
        date=datetime.datetime(2023, 10, 26, 10, 31, 0, 0),
        level="ERROR",
        msg="CSV error message."
    )
    handler.write(second_entry)

    expected_file = output_dir / f"log_{datetime.date.today().isoformat()}.csv"
    assert expected_file.exists()

    with open(expected_file, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader) # Skip header
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0] == [str(sample_log_entry.date.isoformat()), sample_log_entry.level, sample_log_entry.message]
    assert rows[1] == [str(second_entry.date.isoformat()), second_entry.level, second_entry.message]


# --- Testy dla FileHandler (zwykły plik tekstowy) ---
def test_file_handler_write(tmp_path, sample_log_entry):
    """Test that FileHandler correctly writes a log entry to a text file."""
    output_dir = tmp_path / "text_logs"
    output_dir.mkdir()
    handler = FileHandler(output_dir) # Przekazujemy katalog
    handler.write(sample_log_entry)

    expected_file = output_dir / f"log_{datetime.date.today().isoformat()}.log"
    assert expected_file.exists()

    with open(expected_file, 'r') as f:
        content = f.read()
    # Pamiętaj, że FileHandler dodaje '\n' na końcu
    assert content.strip() == f"{sample_log_entry.date.isoformat()} {sample_log_entry.level} {sample_log_entry.message}"


def test_file_handler_append(tmp_path, sample_log_entry):
    """Test that FileHandler appends to an existing text file."""
    output_dir = tmp_path / "text_append_logs"
    output_dir.mkdir()
    handler = FileHandler(output_dir)

    # Write first entry
    handler.write(sample_log_entry)

    # Write second entry
    second_entry = LogEntry(
        date=datetime.datetime(2023, 10, 26, 10, 31, 0, 0),
        level="DEBUG",
        msg="Debug message for text file."
    )
    handler.write(second_entry)

    expected_file = output_dir / f"log_{datetime.date.today().isoformat()}.log"
    assert expected_file.exists()

    with open(expected_file, 'r') as f:
        content_lines = f.read().strip().split('\n')
    assert len(content_lines) == 2
    assert content_lines[0] == f"{sample_log_entry.date.isoformat()} {sample_log_entry.level} {sample_log_entry.message}"
    assert content_lines[1] == f"{second_entry.date.isoformat()} {second_entry.level} {second_entry.message}"


# --- Testy dla SQLLiteHandler ---
@pytest.fixture
def sqlite_handler(tmp_path):
    """Fixture to provide a SQLLiteHandler with a temporary database."""
    db_path = tmp_path / "test.db"
    # SQLLiteHandler oczekuje ścieżki do pliku DB
    handler = SQLLiteHandler(db_path) 
    yield handler
    # Połączenie jest zamykane automatycznie przez menedżer kontekstu w klasie SQLLiteHandler
    # Nie ma potrzeby handler.conn.close() tutaj, ponieważ 'conn' nie jest atrybutem instancji.

def test_sqlite_handler_write(sqlite_handler, sample_log_entry):
    """Test that SQLLiteHandler correctly writes a log entry to a database."""
    sqlite_handler.write(sample_log_entry)

    conn = sqlite3.connect(sqlite_handler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, level, message FROM logs ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    # SQLite stores datetime as strings by default for text columns
    assert rows[0] == (sample_log_entry.date.isoformat(), sample_log_entry.level, sample_log_entry.message)


def test_sqlite_handler_multiple_writes(sqlite_handler, sample_log_entry):
    """Test that SQLLiteHandler correctly writes multiple log entries."""
    sqlite_handler.write(sample_log_entry)
    
    second_entry = LogEntry(
        date=datetime.datetime(2023, 10, 26, 10, 31, 0, 0),
        level="CRITICAL",
        msg="Critical DB error."
    )
    sqlite_handler.write(second_entry)

    conn = sqlite3.connect(sqlite_handler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, level, message FROM logs ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0] == (sample_log_entry.date.isoformat(), sample_log_entry.level, sample_log_entry.message)
    assert rows[1] == (second_entry.date.isoformat(), second_entry.level, second_entry.message)


def test_sqlite_handler_table_creation_on_first_write(tmp_path, sample_log_entry):
    """Test that the SQLite table is created on the first write if it doesn't exist."""
    db_path = tmp_path / "new_test_db.db"
    # Ensure the database file does not exist initially
    if db_path.exists():
        os.remove(db_path)

    handler = SQLLiteHandler(db_path)
    # At this point, the file might not exist yet, or the table might not be created.
    # The first write should trigger table creation.
    handler.write(sample_log_entry)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Try to select from the table, if it exists, this will work.
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs';")
    table_exists = cursor.fetchone() is not None
    
    conn.close()
    assert table_exists, "Logs table should have been created."