"""
Tests for AtlantaMunicipalClient.

Note: These tests may require network access or mocking.
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from atlanta_court.client import AtlantaMunicipalClient


@pytest.fixture
def mock_search_page_html():
    """Mock HTML response for search page."""
    return """
    <html>
        <body>
            <form>
                <input type="hidden" name="__RequestVerificationToken" value="test_token_123" />
            </form>
        </body>
    </html>
    """


@pytest.fixture
def client():
    """Create a client instance."""
    return AtlantaMunicipalClient()


class TestAtlantaMunicipalClient:
    """Tests for AtlantaMunicipalClient class."""
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == AtlantaMunicipalClient.DEFAULT_BASE_URL
        assert client.session is not None
        assert 'User-Agent' in client.session.headers
    
    def test_init_with_custom_url(self):
        """Test client initialization with custom URL."""
        custom_url = "https://example.com"
        client = AtlantaMunicipalClient(base_url=custom_url)
        assert client.base_url == custom_url
    
    @patch('atlanta_court.client.requests.Session.get')
    def test_get_search_page(self, mock_get, client, mock_search_page_html):
        """Test getting search page and extracting tokens."""
        # Mock response
        mock_response = Mock()
        mock_response.text = mock_search_page_html
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Mock cookies
        client.session.cookies = {
            'ASP.NET_SessionId': 'test_session_123',
            '__RequestVerificationToken_ABC123': 'test_csrf_cookie'
        }
        
        # Call method
        client._get_search_page()
        
        # Assertions
        assert client._csrf_token_body == 'test_token_123'
        assert client._csrf_cookie_name == '__RequestVerificationToken_ABC123'
        mock_get.assert_called_once()
    
    @patch('atlanta_court.client.requests.Session.get')
    def test_get_search_page_no_csrf_cookie(self, mock_get, client, mock_search_page_html):
        """Test error when CSRF cookie not found."""
        mock_response = Mock()
        mock_response.text = mock_search_page_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # No CSRF cookie in cookies
        client.session.cookies = {'ASP.NET_SessionId': 'test_session'}
        
        with pytest.raises(ValueError, match="Could not find CSRF token cookie"):
            client._get_search_page()
    
    @patch('atlanta_court.client.requests.Session.get')
    def test_get_search_page_no_csrf_token_in_html(self, mock_get, client):
        """Test error when CSRF token not in HTML."""
        mock_response = Mock()
        mock_response.text = "<html><body>No token here</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client.session.cookies = {
            '__RequestVerificationToken_ABC': 'cookie_value'
        }
        
        with pytest.raises(ValueError, match="Could not find CSRF token in HTML"):
            client._get_search_page()
    
    def test_context_manager(self):
        """Test using client as context manager."""
        with AtlantaMunicipalClient() as client:
            assert client.session is not None
        
        # Session should be closed after exiting context
        # (Note: This is a basic test, actual verification would check session state)
    
    def test_search_type_constants(self):
        """Test that search type constants are defined."""
        assert hasattr(AtlantaMunicipalClient, 'SEARCH_TYPE_NAME')
        assert hasattr(AtlantaMunicipalClient, 'SEARCH_TYPE_CASE_NUMBER')
        assert hasattr(AtlantaMunicipalClient, 'SEARCH_TYPE_ATTORNEY')

    @patch('atlanta_court.client.requests.Session.post')
    def test_search_no_results_table(self, mock_post, client):
        """Test search when no results table is found in response."""
        # Setup CSRF token first
        client._csrf_token_body = 'test_token'
        client._csrf_cookie_name = '__RequestVerificationToken_ABC'

        # Mock response with HTML that has no results table
        mock_response = Mock()
        mock_response.text = "<html><body><p>No results found</p></body></html>"
        mock_response.url = "https://benchmark.atlantaga.gov/BenchmarkWeb/CourtCase.aspx/CaseSearch"
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Perform search
        result = client.search("Smith, John")

        # Verify response indicates no results
        assert result['success'] is False
        assert 'No results found' in result['message']
        assert 'html' in result

    @patch('atlanta_court.client.AtlantaMunicipalClient.get_results_data')
    @patch('atlanta_court.client.AtlantaMunicipalClient.search')
    def test_search_and_get_results_failed_search(self, mock_search, mock_get_results, client):
        """Test search_and_get_results when search fails."""
        # Mock a failed search
        mock_search.return_value = {
            'success': False,
            'message': 'Search failed'
        }

        # Call the method
        results = client.search_and_get_results("Nonexistent, Person")

        # Should return empty list
        assert results == []

        # get_results_data should not be called when search fails
        mock_get_results.assert_not_called()

    @patch('atlanta_court.client.requests.Session.post')
    def test_search_http_error(self, mock_post, client):
        """Test search handles HTTP errors gracefully."""
        client._csrf_token_body = 'test_token'
        client._csrf_cookie_name = '__RequestVerificationToken_ABC'

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            client.search("Smith, John")

    @patch('atlanta_court.client.requests.Session.post')
    def test_get_results_data_invalid_json(self, mock_post, client):
        """Test get_results_data handles invalid JSON."""
        client._csrf_token_body = 'test_token'

        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            client.get_results_data()

    def test_get_case_details_missing_ids(self, client):
        """Test get_case_details_with_dockets when IDs not found in page."""
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.text = "<html><body>No JavaScript here</body></html>"
            mock_response.url = "https://example.com/case/123"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = client.get_case_details_with_dockets("https://example.com/case/123")

            # Should still return case data but with empty docket_history
            assert result['docket_history'] == []
# Integration tests (require network access)
class TestAtlantaMunicipalClientIntegration:
    """Integration tests that make actual HTTP requests."""
    
    @pytest.mark.integration
    def test_real_search(self):
        """Test actual search (requires network)."""
        with AtlantaMunicipalClient() as client:
            results = client.search_and_get_results(
                search_term="brewington, brent",
                max_results=5
            )
            
            # Basic validation
            assert isinstance(results, list)
            # Note: Can't assert specific results as data changes


class TestMainFunction:
    """Tests for the main() function."""

    @patch('atlanta_court.client.AtlantaMunicipalClient')
    def test_main_basic_search(self, mock_client_class):
        """Test main function with basic search."""
        from atlanta_court.client import main

        # Mock client and its methods
        mock_client = Mock()
        mock_client.search_and_get_results.return_value = [
            {'case': '2024-CR-001', 'name': 'Doe, John'}
        ]
        mock_client_class.return_value = mock_client

        # Call main
        results = main(
            search_term="Doe, John",
            search_type=AtlantaMunicipalClient.SEARCH_TYPE_NAME
        )

        # Verify results
        assert len(results) == 1
        assert results[0]['case'] == '2024-CR-001'

        # Verify client was used correctly
        mock_client.search_and_get_results.assert_called_once()
        mock_client.close.assert_called_once()

    @patch('atlanta_court.client.AtlantaMunicipalClient')
    def test_main_with_output_file(self, mock_client_class, tmp_path):
        """Test main function saves to file."""
        from atlanta_court.client import main

        mock_client = Mock()
        mock_client.search_and_get_results.return_value = [
            {'case': '2024-CR-001', 'name': 'Smith, Jane'}
        ]
        mock_client_class.return_value = mock_client

        output_file = tmp_path / "test_output.json"

        # Call main with output_path
        main(
            search_term="25TR089095",
            search_type=AtlantaMunicipalClient.SEARCH_TYPE_CASE_NUMBER,
            output_path=str(output_file)
        )

        # Verify file was created
        assert output_file.exists()

        # Verify file contents
        import json
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]['case'] == '2024-CR-001'

        # Client should be closed
        mock_client.close.assert_called_once()

    @patch('atlanta_court.client.AtlantaMunicipalClient')
    def test_main_with_all_params(self, mock_client_class):
        """Test main function with all parameters."""
        from atlanta_court.client import main

        mock_client = Mock()
        mock_client.search_and_get_results.return_value = []
        mock_client_class.return_value = mock_client

        # Call with all parameters
        main(
            search_term="Test",
            search_type=AtlantaMunicipalClient.SEARCH_TYPE_NAME,
            base_url="https://example.com",
            court_types=['1', '2'],
            party_types=['3', '4'],
            divisions=['5'],
            opened_from="2024-01-01",
            opened_to="2024-12-31",
            closed_from="2024-06-01",
            closed_to="2024-06-30",
            max_results=100
        )

        # Verify client was instantiated with base_url
        mock_client_class.assert_called_once_with(base_url="https://example.com")

        # Verify search was called with correct params
        call_kwargs = mock_client.search_and_get_results.call_args[1]
        assert call_kwargs['court_types'] == ['1', '2']
        assert call_kwargs['party_types'] == ['3', '4']
        assert call_kwargs['divisions'] == ['5']
        assert call_kwargs['opened_from'] == "2024-01-01"
        assert call_kwargs['opened_to'] == "2024-12-31"
        assert call_kwargs['closed_from'] == "2024-06-01"
        assert call_kwargs['closed_to'] == "2024-06-30"

        mock_client.close.assert_called_once()

    @patch('atlanta_court.client.AtlantaMunicipalClient')
    def test_main_closes_client_on_exception(self, mock_client_class):
        """Test main function closes client even on exception."""
        from atlanta_court.client import main

        mock_client = Mock()
        mock_client.search_and_get_results.side_effect = Exception("Test error")
        mock_client_class.return_value = mock_client

        # Should raise exception
        with pytest.raises(Exception, match="Test error"):
            main(search_term="Test")

        # Client should still be closed
        mock_client.close.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
