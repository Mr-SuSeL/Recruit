import pytest
import datetime
import json
import csv
import sqlite3

from profil_logger.logger import LogEntry
from profil_logger.handlers import JsonHandler, CSVHandler, FileHandler, SQLLiteHandler


@pytest.fixture
def sample_log_entry():
    """Fixture to provide a sample LogEntry for tests."""
    return LogEntry(
        date=datetime.datetime(2023, 10, 26, 10, 30, 0, 0),
        level="INFO",
        message="Test message for handler."
    )

@pytest.fixture
def another_log_entry():
    """Fixture to provide another sample LogEntry for append tests."""
    return LogEntry(
        date=datetime.datetime(2023, 10, 26, 11, 0, 0, 0),
        level="DEBUG",
        message="Another test message."
    )

@pytest.fixture
def json_test_file(tmp_path):
    """Fixture for a temporary JSON file path (just a directory for handlers)."""
    # Zwracamy katalog, ponieważ JsonHandler dynamicznie tworzy nazwę pliku
    output_dir = tmp_path / "json_logs"
    output_dir.mkdir(exist_ok=True)
    yield output_dir # Zwracamy katalog
    # Czyszczenie: usuwamy cały katalog
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)


@pytest.fixture
def csv_test_file(tmp_path):
    """Fixture for a temporary CSV file path (just a directory for handlers)."""
    output_dir = tmp_path / "csv_logs"
    output_dir.mkdir(exist_ok=True)
    yield output_dir
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)

@pytest.fixture
def text_test_file(tmp_path):
    """Fixture for a temporary text file path (just a directory for handlers)."""
    output_dir = tmp_path / "text_logs"
    output_dir.mkdir(exist_ok=True)
    yield output_dir
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)


@pytest.fixture
def sqlite_test_db(tmp_path):
    """Fixture for a temporary SQLite database file path."""
    db_dir = tmp_path / "sqlite_db"
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "test.db"
    yield db_path
    # Zmieniono na rmtree dla katalogu, aby zapewnić usunięcie
    if db_dir.exists():
        import shutil
        shutil.rmtree(db_dir)


# --- Testy dla JsonHandler ---

def test_json_handler_write(json_test_file, sample_log_entry):
    """Testuje, czy JsonHandler poprawnie zapisuje pojedynczy log."""
    handler = JsonHandler(json_test_file) # Przekazujemy katalog
    handler.write(sample_log_entry)

    expected_json_filepath = json_test_file / f"log_{datetime.date.today().isoformat()}.json"
    assert expected_json_filepath.exists()
    with open(expected_json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0] == sample_log_entry.to_dict()

def test_json_handler_append(json_test_file, sample_log_entry, another_log_entry):
    """Testuje, czy JsonHandler poprawnie dodaje logi do istniejącego pliku."""
    initial_filepath = json_test_file / f"log_{datetime.date.today().isoformat()}.json"
    with open(initial_filepath, 'w', encoding='utf-8') as f:
        json.dump([sample_log_entry.to_dict()], f)

    handler = JsonHandler(json_test_file)
    handler.write(another_log_entry)

    assert initial_filepath.exists()
    with open(initial_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0] == sample_log_entry.to_dict()
    assert data[1] == another_log_entry.to_dict()

# --- Testy dla CSVHandler ---

def test_csv_handler_write(csv_test_file, sample_log_entry):
    """Testuje, czy CSVHandler poprawnie zapisuje pojedynczy log."""
    handler = CSVHandler(csv_test_file)
    handler.write(sample_log_entry)

    expected_csv_filepath = csv_test_file / f"log_{datetime.date.today().isoformat()}.csv"
    assert expected_csv_filepath.exists()
    with open(expected_csv_filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    expected_dict = sample_log_entry.to_dict()
    assert rows[0] == expected_dict

def test_csv_handler_append(csv_test_file, sample_log_entry, another_log_entry):
    """Testuje, czy CSVHandler poprawnie dodaje logi do istniejącego pliku."""
    initial_filepath = csv_test_file / f"log_{datetime.date.today().isoformat()}.csv"
    with open(initial_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "level", "message"])
        writer.writeheader()
        writer.writerow(sample_log_entry.to_dict())

    handler = CSVHandler(csv_test_file)
    handler.write(another_log_entry)

    assert initial_filepath.exists()
    with open(initial_filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0] == sample_log_entry.to_dict()
    assert rows[1] == another_log_entry.to_dict()

# --- Testy dla FileHandler ---

def test_file_handler_write(text_test_file, sample_log_entry):
    """Testuje, czy FileHandler poprawnie zapisuje pojedynczy log."""
    handler = FileHandler(text_test_file)
    handler.write(sample_log_entry)

    expected_text_filepath = text_test_file / f"log_{datetime.date.today().isoformat()}.log"
    assert expected_text_filepath.exists()
    with open(expected_text_filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    assert content == f"[{sample_log_entry.date.isoformat()}] {sample_log_entry.level}: {sample_log_entry.message}"


def test_file_handler_append(text_test_file, sample_log_entry, another_log_entry):
    """Testuje, czy FileHandler poprawnie dodaje logi do istniejącego pliku."""
    initial_filepath = text_test_file / f"log_{datetime.date.today().isoformat()}.log"
    with open(initial_filepath, 'w', encoding='utf-8') as f:
        f.write(f"[{sample_log_entry.date.isoformat()}] {sample_log_entry.level}: {sample_log_entry.message}\n")

    handler = FileHandler(text_test_file)
    handler.write(another_log_entry)

    assert initial_filepath.exists()
    with open(initial_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    assert len(lines) == 2
    assert lines[0].strip() == f"[{sample_log_entry.date.isoformat()}] {sample_log_entry.level}: {sample_log_entry.message}"
    assert lines[1].strip() == f"[{another_log_entry.date.isoformat()}] {another_log_entry.level}: {another_log_entry.message}"

# --- Testy dla SQLLiteHandler ---

def test_sqlite_handler_write(sqlite_test_db, sample_log_entry):
    """Testuje, czy SQLLiteHandler poprawnie zapisuje pojedynczy log."""
    handler = SQLLiteHandler(sqlite_test_db)
    handler.write(sample_log_entry)

    conn = sqlite3.connect(sqlite_test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, level, message FROM logs")
    rows = cursor.fetchall()
    conn.close() # Upewnij się, że połączenie jest zamknięte po teście

    assert len(rows) == 1
    assert rows[0] == (sample_log_entry.date.isoformat(), sample_log_entry.level, sample_log_entry.message)

def test_sqlite_handler_multiple_writes(sqlite_test_db, sample_log_entry, another_log_entry):
    """Testuje, czy SQLLiteHandler poprawnie zapisuje wiele logów."""
    handler = SQLLiteHandler(sqlite_test_db)
    handler.write(sample_log_entry)
    handler.write(another_log_entry)

    conn = sqlite3.connect(sqlite_test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, level, message FROM logs ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close() # Upewnij się, że połączenie jest zamknięte po teście

    assert len(rows) == 2
    assert rows[0] == (sample_log_entry.date.isoformat(), sample_log_entry.level, sample_log_entry.message)
    assert rows[1] == (another_log_entry.date.isoformat(), another_log_entry.level, another_log_entry.message)

def test_sqlite_handler_table_creation_on_first_write(sqlite_test_db, sample_log_entry):
    """Testuje, czy tabela 'logs' jest tworzona przy pierwszym zapisie."""
    # Użyj sqlite_test_db.unlink() jeśli testujesz bezpośrednio plik,
    # ale fixture usuwa katalog, więc jest ok.
    assert not sqlite_test_db.exists() 

    handler = SQLLiteHandler(sqlite_test_db)
    handler.write(sample_log_entry)

    assert sqlite_test_db.exists()
    conn = sqlite3.connect(sqlite_test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs';")
    table_exists = cursor.fetchone() is not None
    conn.close() #połączenie jest zamknięte po teście