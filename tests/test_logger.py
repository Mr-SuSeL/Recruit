import pytest
import datetime
from unittest.mock import MagicMock

# Zostawiamy import LogLevel, ale zmieniamy sposób jego użycia
from profil_logger.logger import LogEntry, ProfilLogger, LogLevel 

# Fixture dla mockowanego handlera
@pytest.fixture
def mock_handler():
    # MagicMock symuluje handler z metodą 'write'
    handler = MagicMock()
    return handler

# Fixture dla ProfilLogger z mockowanym handlerem
@pytest.fixture
def profil_logger(mock_handler):
    return ProfilLogger(handlers=[mock_handler])

def test_info_logging_calls_handler(profil_logger, mock_handler):
    """Testuje, czy metoda info() wywołuje metodę write handlera."""
    profil_logger.info("Test info message.")
    mock_handler.write.assert_called_once()
    assert mock_handler.write.call_args[0][0].level == "INFO"
    assert mock_handler.write.call_args[0][0].message == "Test info message."

def test_debug_logging_at_default_level_does_not_call_handler(profil_logger, mock_handler):
    """Testuje, czy debug() nie loguje domyślnie (poziom INFO)."""
    profil_logger.debug("Test debug message.")
    mock_handler.write.assert_not_called()

def test_debug_logging_at_debug_level_calls_handler(profil_logger, mock_handler):
    """Testuje, czy debug() loguje po ustawieniu poziomu na DEBUG."""
    # Zmieniamy LogLevel.DEBUG na "DEBUG"
    profil_logger.set_log_level("DEBUG") 
    profil_logger.debug("Another debug message.")
    mock_handler.write.assert_called_once()
    assert mock_handler.write.call_args[0][0].level == "DEBUG"

def test_set_log_level_changes_level(profil_logger):
    """Testuje poprawną zmianę poziomu logowania."""
    # Zmieniamy LogLevel.ERROR na "ERROR"
    profil_logger.set_log_level("ERROR") 
    assert profil_logger.log_level == "ERROR"

def test_set_log_level_with_invalid_level_raises_error(profil_logger):
    """Testuje, czy ustawienie nieprawidłowego poziomu wywołuje błąd."""
    with pytest.raises(ValueError):
        profil_logger.set_log_level("INVALID_LEVEL")