"""
Pytest configuration and shared fixtures for atlanta_court tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

from atlanta_court.client import AtlantaMunicipalClient

# Test configuration constants
TEST_BASE_URL = "https://benchmark.atlantaga.gov"

# Helper functions for tests
def get_mock_cookies():
    """Return mock cookies dict."""
    return {
        'ASP.NET_SessionId': 'mock_session_id_12345',
        '__RequestVerificationToken_L0JlbmNobWFya1dlYg2': 'mock_csrf_cookie_value'
    }

def get_mock_headers():
    """Return mock headers dict."""
    return {
        'Set-Cookie': '__RequestVerificationToken_L0JlbmNobWFya1dlYg2=mock_csrf_cookie_value; Path=/; HttpOnly',
        'Content-Type': 'text/html; charset=utf-8'
    }


@pytest.fixture
def client():
    """Create a fresh AtlantaMunicipalClient instance for testing."""
    return AtlantaMunicipalClient(base_url=TEST_BASE_URL)


@pytest.fixture
def mock_search_page_html():
    """Return mock HTML for search page."""
    search_page_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Court Case Search</title></head>
    <body>
        <form method="post" action="/BenchmarkWeb/CourtCase.aspx/CaseSearch">
            <input type="hidden" name="__RequestVerificationToken" value="mock_csrf_token_12345" />
            <input type="text" name="search" />
            <button type="submit">Search</button>
        </form>
    </body>
    </html>
    """
    return search_page_html


@pytest.fixture
def mock_results_page_html():
    """Return mock HTML for results page."""
    results_page_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Search Results</title></head>
    <body>
        <table id="tblResults">
            <thead>
                <tr>
                    <th>Case Number</th>
                    <th>Party Name</th>
                    <th>Filed Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>2024-CR-12345</td>
                    <td>Doe, John</td>
                    <td>2024-01-15</td>
                    <td>Open</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    return results_page_html


@pytest.fixture
def mock_results_json():
    """Return mock JSON for AJAX results."""
    results_json = {
        "draw": 1,
        "recordsTotal": 2,
        "recordsFiltered": 2,
        "data": [
            ["", "2024-CR-12345", "Doe, John", "2024-01-15", "2024-01-15", "Open"],
            ["", "2024-CR-67890", "Smith, Jane", "2024-02-20", "2024-02-20", "Closed"]
        ]
    }
    return results_json


@pytest.fixture
def mock_cookies():
    """Return mock cookies dict."""
    return get_mock_cookies()


@pytest.fixture
def mock_headers():
    """Return mock headers dict."""
    return get_mock_headers()


@pytest.fixture
def mock_response():
    """Create a mock response object with common attributes."""
    response = Mock()
    response.status_code = 200
    response.ok = True
    response.raise_for_status = Mock()
    response.headers = get_mock_headers()
    return response


@pytest.fixture
def mock_search_response(mock_response, mock_search_page_html):
    """Create a mock response for the search page GET request."""
    mock_response.text = mock_search_page_html
    mock_response.content = mock_search_page_html.encode('utf-8')
    return mock_response


@pytest.fixture
def mock_results_response(mock_response, mock_results_page_html):
    """Create a mock response for the search POST request."""
    mock_response.text = mock_results_page_html
    mock_response.content = mock_results_page_html.encode('utf-8')
    return mock_response


@pytest.fixture
def mock_json_response(mock_response, mock_results_json):
    """Create a mock response for the AJAX JSON request."""
    mock_response.json = Mock(return_value=mock_results_json)
    return mock_response


@pytest.fixture
def mock_session(mock_cookies):
    """Create a mock requests Session with cookies."""
    session = MagicMock()
    session.cookies = mock_cookies
    session.headers = {}
    return session

