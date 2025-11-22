"""
Tests for AtlantaMunicipalClient.

Note: These tests may require network access or mocking.
"""

import pytest
from unittest.mock import Mock, patch

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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
