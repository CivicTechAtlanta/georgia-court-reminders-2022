"""
Tests for CLI module.
"""

import json
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from atlanta_court.cli import setup_logging, search_command, main
from atlanta_court.client import AtlantaMunicipalClient


class TestSetupLogging:
    """Tests for setup_logging function."""

    @patch('logging.basicConfig')
    def test_setup_logging_info(self, mock_config):
        """Test logging setup with INFO level."""
        setup_logging("INFO")
        mock_config.assert_called_once()
        assert mock_config.call_args[1]['level'] == logging.INFO

    @patch('logging.basicConfig')
    def test_setup_logging_debug(self, mock_config):
        """Test logging setup with DEBUG level."""
        setup_logging("DEBUG")
        mock_config.assert_called_once()
        assert mock_config.call_args[1]['level'] == logging.DEBUG

    @patch('logging.basicConfig')
    def test_setup_logging_warning(self, mock_config):
        """Test logging setup with WARNING level."""
        setup_logging("WARNING")
        mock_config.assert_called_once()
        assert mock_config.call_args[1]['level'] == logging.WARNING

    @patch('logging.basicConfig')
    def test_setup_logging_error(self, mock_config):
        """Test logging setup with ERROR level."""
        setup_logging("ERROR")
        mock_config.assert_called_once()
        assert mock_config.call_args[1]['level'] == logging.ERROR

    @patch('logging.basicConfig')
    def test_setup_logging_invalid_level(self, mock_config):
        """Test logging setup with invalid level defaults to INFO."""
        setup_logging("INVALID")
        mock_config.assert_called_once()
        assert mock_config.call_args[1]['level'] == logging.INFO


class TestSearchCommand:
    """Tests for search_command function."""

    @pytest.fixture
    def mock_args_name(self):
        """Create mock args for name search."""
        args = Mock()
        args.base_url = None
        args.name = "Doe, John"
        args.case_number = None
        args.attorney = None
        args.court_types = None
        args.party_types = None
        args.divisions = None
        args.opened_from = None
        args.opened_to = None
        args.closed_from = None
        args.closed_to = None
        args.max_results = 50
        args.output = None
        return args

    @pytest.fixture
    def mock_args_case_number(self):
        """Create mock args for case number search."""
        args = Mock()
        args.base_url = None
        args.name = None
        args.case_number = "2024-CR-12345"
        args.attorney = None
        args.court_types = None
        args.party_types = None
        args.divisions = None
        args.opened_from = None
        args.opened_to = None
        args.closed_from = None
        args.closed_to = None
        args.max_results = 50
        args.output = None
        return args

    @pytest.fixture
    def mock_args_attorney(self):
        """Create mock args for attorney search."""
        args = Mock()
        args.base_url = None
        args.name = None
        args.case_number = None
        args.attorney = "Smith, Jane"
        args.court_types = None
        args.party_types = None
        args.divisions = None
        args.opened_from = None
        args.opened_to = None
        args.closed_from = None
        args.closed_to = None
        args.max_results = 50
        args.output = None
        return args

    def test_search_command_name_stdout(self, mock_args_name, capsys):
        """Test search command with name search and stdout output."""
        # Mock the client_main function
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.return_value = [
                {'case': '2024-CR-001', 'name': 'Doe, John'}
            ]

            # Execute command
            result = search_command(mock_args_name)

            # Verify success
            assert result == 0

            # Verify client_main was called correctly
            mock_client_main.assert_called_once_with(
                search_term="Doe, John",
                search_type=AtlantaMunicipalClient.SEARCH_TYPE_NAME,
                base_url=None,
                court_types=None,
                party_types=None,
                divisions=None,
                opened_from=None,
                opened_to=None,
                closed_from=None,
                closed_to=None,
                max_results=50,
                output_path=None
            )

            # Verify output to stdout
            captured = capsys.readouterr()
            output_data = json.loads(captured.out)
            assert len(output_data) == 1
            assert output_data[0]['name'] == 'Doe, John'

    def test_search_command_case_number(self, mock_args_case_number):
        """Test search command with case number."""
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.return_value = []

            result = search_command(mock_args_case_number)

            assert result == 0
            mock_client_main.assert_called_once_with(
                search_term="2024-CR-12345",
                search_type=AtlantaMunicipalClient.SEARCH_TYPE_CASE_NUMBER,
                base_url=None,
                court_types=None,
                party_types=None,
                divisions=None,
                opened_from=None,
                opened_to=None,
                closed_from=None,
                closed_to=None,
                max_results=50,
                output_path=None
            )

    def test_search_command_attorney(self, mock_args_attorney):
        """Test search command with attorney search."""
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.return_value = []

            result = search_command(mock_args_attorney)

            assert result == 0
            mock_client_main.assert_called_once_with(
                search_term="Smith, Jane",
                search_type=AtlantaMunicipalClient.SEARCH_TYPE_ATTORNEY,
                base_url=None,
                court_types=None,
                party_types=None,
                divisions=None,
                opened_from=None,
                opened_to=None,
                closed_from=None,
                closed_to=None,
                max_results=50,
                output_path=None
            )

    def test_search_command_with_file_output(self, mock_args_name, tmp_path):
        """Test search command with file output."""
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.return_value = [
                {'case': '2024-CR-001', 'name': 'Doe, John'}
            ]

            # Set output file
            output_file = tmp_path / "results.json"
            mock_args_name.output = str(output_file)

            result = search_command(mock_args_name)

            assert result == 0

            # Verify client_main was called with output_path
            mock_client_main.assert_called_once()
            assert mock_client_main.call_args[1]['output_path'] == str(output_file)

    def test_search_command_with_nested_output_path(self, mock_args_name, tmp_path):
        """Test search command creates parent directories for output."""
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.return_value = []

            # Set nested output path
            output_file = tmp_path / "nested" / "dir" / "results.json"
            mock_args_name.output = str(output_file)

            result = search_command(mock_args_name)

            assert result == 0
            # Verify client_main was called with the output_path
            assert mock_client_main.call_args[1]['output_path'] == str(output_file)

    def test_search_command_with_optional_params(self, mock_args_name):
        """Test search command with optional parameters."""
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.return_value = []

            # Set optional parameters
            mock_args_name.court_types = "1,2,3"
            mock_args_name.party_types = "4,5"
            mock_args_name.divisions = "1"
            mock_args_name.opened_from = "2024-01-01"
            mock_args_name.opened_to = "2024-12-31"
            mock_args_name.closed_from = "2024-01-01"
            mock_args_name.closed_to = "2024-12-31"

            result = search_command(mock_args_name)

            assert result == 0
            mock_client_main.assert_called_once_with(
                search_term="Doe, John",
                search_type=AtlantaMunicipalClient.SEARCH_TYPE_NAME,
                base_url=None,
                court_types=['1', '2', '3'],
                party_types=['4', '5'],
                divisions=['1'],
                opened_from='2024-01-01',
                opened_to='2024-12-31',
                closed_from='2024-01-01',
                closed_to='2024-12-31',
                max_results=50,
                output_path=None
            )

    def test_search_command_with_custom_base_url(self, mock_args_name):
        """Test search command with custom base URL."""
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.return_value = []

            custom_url = "https://custom.example.com"
            mock_args_name.base_url = custom_url

            result = search_command(mock_args_name)

            assert result == 0
            # Verify base_url was passed to client_main
            assert mock_client_main.call_args[1]['base_url'] == custom_url

    def test_search_command_exception_handling(self, mock_args_name):
        """Test search command handles exceptions."""
        with patch('atlanta_court.cli.client_main') as mock_client_main:
            mock_client_main.side_effect = Exception("Search failed")

            result = search_command(mock_args_name)

            # Should return 1 for error
            assert result == 1


class TestMain:
    """Tests for main function."""

    @patch('atlanta_court.cli.load_dotenv')
    @patch('sys.argv', ['atlanta-court'])
    def test_main_no_command(self, mock_load_dotenv, capsys):
        """Test main with no command prints help."""
        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert 'usage:' in captured.out.lower() or 'usage:' in captured.err.lower()

    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', ['atlanta-court', 'search', '--name', 'Doe, John'])
    def test_main_search_command(self, mock_search_command, mock_load_dotenv):
        """Test main with search command."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        mock_search_command.assert_called_once()
        mock_load_dotenv.assert_called_once()

    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', ['atlanta-court', 'search', '--case-number', '2024-CR-001'])
    def test_main_case_number_search(self, mock_search_command, mock_load_dotenv):
        """Test main with case number search."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        mock_search_command.assert_called_once()

    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', ['atlanta-court', 'search', '--attorney', 'Smith, Jane'])
    def test_main_attorney_search(self, mock_search_command, mock_load_dotenv):
        """Test main with attorney search."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        mock_search_command.assert_called_once()

    @patch('atlanta_court.cli.setup_logging')
    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', ['atlanta-court', '--verbose', 'search', '--name', 'Test'])
    def test_main_verbose_flag(self, mock_search_command, mock_load_dotenv, mock_setup_logging):
        """Test main with verbose flag sets DEBUG level."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        mock_setup_logging.assert_called_once_with('DEBUG')

    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', ['atlanta-court', '--log-level', 'WARNING', 'search', '--name', 'Test'])
    def test_main_log_level_flag(self, mock_search_command, mock_load_dotenv):
        """Test main with log-level flag."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        logger = logging.getLogger()
        assert logger.level == logging.WARNING

    @patch.dict('os.environ', {'COURT_BASE_URL': 'https://env.example.com'})
    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', ['atlanta-court', 'search', '--name', 'Test'])
    def test_main_base_url_from_env(self, mock_search_command, mock_load_dotenv):
        """Test main uses base URL from environment."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        # Verify the args passed to search_command have the env base_url
        args = mock_search_command.call_args[0][0]
        assert args.base_url == 'https://env.example.com'

    @patch.dict('os.environ', {'LOG_LEVEL': 'ERROR'})
    @patch('atlanta_court.cli.setup_logging')
    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', ['atlanta-court', 'search', '--name', 'Test'])
    def test_main_log_level_from_env(self, mock_search_command, mock_load_dotenv, mock_setup_logging):
        """Test main uses log level from environment."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        mock_setup_logging.assert_called_once_with('ERROR')

    @patch('atlanta_court.cli.load_dotenv')
    @patch('atlanta_court.cli.search_command')
    @patch('sys.argv', [
        'atlanta-court', 'search', '--name', 'Test',
        '--max-results', '100',
        '--court-types', '1,2,3',
        '--party-types', '4,5',
        '--divisions', '6',
        '--opened-from', '2024-01-01',
        '--opened-to', '2024-12-31',
        '--closed-from', '2024-06-01',
        '--closed-to', '2024-06-30',
        '--output', 'test.json'
    ])
    def test_main_all_search_options(self, mock_search_command, mock_load_dotenv):
        """Test main with all search options."""
        mock_search_command.return_value = 0

        result = main()

        assert result == 0
        args = mock_search_command.call_args[0][0]
        assert args.name == 'Test'
        assert args.max_results == 100
        assert args.court_types == '1,2,3'
        assert args.party_types == '4,5'
        assert args.divisions == '6'
        assert args.opened_from == '2024-01-01'
        assert args.opened_to == '2024-12-31'
        assert args.closed_from == '2024-06-01'
        assert args.closed_to == '2024-06-30'
        assert args.output == 'test.json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
