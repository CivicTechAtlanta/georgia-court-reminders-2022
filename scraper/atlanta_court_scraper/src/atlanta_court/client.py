"""
Client for interacting with Atlanta Municipal Court's Benchmark system.
This can be refactored later to support other Tyler Technologies Benchmark systems.
"""

import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AtlantaMunicipalClient:
    """
    Client for searching court cases in the Atlanta Municipal Court system.
    
    This system uses Tyler Technologies' Benchmark platform with ASP.NET
    anti-CSRF protection.
    """
    
    DEFAULT_BASE_URL = "https://benchmark.atlantaga.gov"
    
    # Search types
    SEARCH_TYPE_NAME = "Name"
    SEARCH_TYPE_CASE_NUMBER = "CaseNumber"
    SEARCH_TYPE_ATTORNEY = "Attorney"
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL for the court system. Defaults to Atlanta Municipal Court.
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.session = requests.Session()
        
        # Set headers that mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # Tokens extracted from initial page load
        self._csrf_token_body: Optional[str] = None
        self._csrf_cookie_name: Optional[str] = None
        
    def _get_search_page(self) -> None:
        """
        Load the search page to obtain session cookies and CSRF token.

        This must be called before performing any searches.
        """
        search_url = urljoin(self.base_url, "/BenchmarkWeb/Home.aspx/Search")

        response = self.session.get(search_url)
        response.raise_for_status()

        # Extract CSRF cookie name and value from Set-Cookie headers
        for cookie_name, _ in self.session.cookies.items():
            if cookie_name.startswith('__RequestVerificationToken_'):
                self._csrf_cookie_name = cookie_name
                break

        if not self._csrf_cookie_name:
            raise ValueError("Could not find CSRF token cookie in response")

        # Extract CSRF token from HTML body
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': '__RequestVerificationToken'})

        if not csrf_input or not csrf_input.get('value'):
            raise ValueError("Could not find CSRF token in HTML")

        csrf_value = csrf_input.get('value')
        if isinstance(csrf_value, list):
            self._csrf_token_body = csrf_value[0] if csrf_value else None
        else:
            self._csrf_token_body = csrf_value
    
    def search(
        self,
        search_term: str,
        search_type: str = SEARCH_TYPE_NAME,
        court_types: Optional[List[str]] = None,
        party_types: Optional[List[str]] = None,
        divisions: Optional[List[str]] = None,
        opened_from: Optional[str] = None,
        opened_to: Optional[str] = None,
        closed_from: Optional[str] = None,
        closed_to: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search for court cases.
        
        Args:
            search_term: The search term (e.g., "Last, First" for name searches)
            search_type: Type of search - SEARCH_TYPE_NAME, SEARCH_TYPE_CASE_NUMBER, or SEARCH_TYPE_ATTORNEY
            court_types: List of court type IDs (defaults to common types)
            party_types: List of party type IDs (defaults to all common types)
            divisions: List of division IDs (defaults to [1])
            opened_from: Case opened from date (YYYY-MM-DD format)
            opened_to: Case opened to date (YYYY-MM-DD format)
            closed_from: Case closed from date (YYYY-MM-DD format)
            closed_to: Case closed to date (YYYY-MM-DD format)
            **kwargs: Additional search parameters
        
        Returns:
            Dict containing the search results
        """
        # Initialize session if not already done
        if not self._csrf_token_body:
            self._get_search_page()
        
        # Set defaults for common parameters
        if court_types is None:
            court_types = ['22', '2', '20', '21', '7', '10']
        if party_types is None:
            party_types = ['1', '2', '3', '4', '5']
        if divisions is None:
            divisions = ['1']
        
        # Build the form data
        form_data = {
            '__RequestVerificationToken': self._csrf_token_body,
            'type': search_type,
            'search': search_term,
            'openedFrom': opened_from or '',
            'openedTo': opened_to or '',
            'closedFrom': closed_from or '',
            'closedTo': closed_to or '',
            'courtTypes': ','.join(court_types),
            'caseTypes': '',
            'partyTypes': ','.join(party_types),
            'divisions': ','.join(divisions),
            'statutes': '',
            'partyBirthYear': '',
            'partyDOB': '',
            'caseStatus': '',
            'propertyAddress': '',
            'propertyCity': '',
            'propertyZip': '',
            'propertySubDivision': '',
            'lawFirm': '',
            'unpaidPrincipleBalanceFrom': '',
            'unpaidPrincipleBalanceTo': '',
            'electionDemandFrom': '',
            'electionDemandTo': '',
            'attorneyFileNumber': '',
        }
        
        # Add any additional kwargs
        form_data.update(kwargs)

        # Submit the search
        search_url = urljoin(self.base_url, "/BenchmarkWeb/CourtCase.aspx/CaseSearch")

        logger.info(f"Searching: {search_term} ({search_type})")

        response = self.session.post(
            search_url,
            data=form_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': urljoin(self.base_url, '/BenchmarkWeb/Home.aspx/Search'),
                'Origin': self.base_url,
            }
        )
        response.raise_for_status()
        
        # The response is the HTML page with search results OR a case details page
        # Parse to determine what type of page we received
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if we have a results table (gridSearchResults)
        results_table = soup.find('table', {'id': 'gridSearchResults'})

        # Check if we're on a case details page instead
        # Case details pages have the URL pattern: /BenchmarkWeb/CourtCase.aspx/Details/{id}
        is_case_details = '/CourtCase.aspx/Details/' in response.url

        if results_table:
            # We have a search results table (multiple results)
            logger.info("Received search results table")
            return {
                'success': True,
                'response_type': 'search_results',
                'html': response.text,
                'soup': soup,
                'url': response.url
            }
        elif is_case_details:
            # We were redirected to a case details page (single result)
            logger.info(f"Redirected to case details page: {response.url}")
            return {
                'success': True,
                'response_type': 'case_details',
                'html': response.text,
                'soup': soup,
                'url': response.url
            }
        else:
            # Neither results table nor case details found
            logger.warning("No results table or case details page found")
            return {
                'success': False,
                'response_type': 'unknown',
                'message': 'No results found or search failed',
                'html': response.text,
                'url': response.url
            }
    
    def parse_case_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse case details from a case details page.

        Args:
            soup: BeautifulSoup object of the case details page

        Returns:
            Dict containing parsed case information including docket history
        """
        import re

        case_data = {}

        # Extract case number - try multiple methods
        case_number = None

        # Method 1: Try to find it in the page title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Title format is usually: "CASENUMBER - PARTY vs PARTY"
            # Extract the first part before the dash
            parts = title_text.split('-')
            if parts:
                potential_case = parts[0].strip()
                # Check if it looks like a case number (contains letters and numbers)
                if re.search(r'[A-Z]+.*\d+', potential_case):
                    case_number = potential_case

        # Method 2: Try h2 with case-heading class
        if not case_number:
            case_heading = soup.find('h2', class_='case-heading')
            if case_heading:
                case_number = case_heading.get_text(strip=True)

        # Method 3: Look for it in JavaScript variables
        if not case_number:
            # Find script tags and look for: var caseNumber = '99TR268487';
            for script in soup.find_all('script'):
                if script.string:
                    match = re.search(r"var caseNumber = '([^']+)'", script.string)
                    if match:
                        case_number = match.group(1)
                        break

        if case_number:
            case_data['case_number'] = case_number

        # Extract data from the case details table(s)
        detail_tables = soup.find_all('table', class_='table')

        for table in detail_tables:
            # Skip the gridDockets table as we'll handle it separately
            if table.get('id') == 'gridDockets':
                continue

            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).rstrip(':')
                    value = cells[1].get_text(strip=True)
                    if label and value:
                        # Convert label to lowercase key
                        key = label.lower().replace(' ', '_')
                        case_data[key] = value

        # Extract party information
        parties_section = soup.find('div', id='parties') or soup.find('section', class_='parties')
        if parties_section:
            parties = []
            party_rows = parties_section.find_all('tr')
            for row in party_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    parties.append({
                        'name': cells[0].get_text(strip=True),
                        'type': cells[1].get_text(strip=True) if len(cells) > 1 else None
                    })
            if parties:
                case_data['parties'] = parties

        # Extract charges/violations
        charges_section = soup.find('div', id='charges') or soup.find('section', class_='charges')
        if charges_section:
            charges = []
            charge_rows = charges_section.find_all('tr')
            for row in charge_rows:
                cells = row.find_all('td')
                if cells:
                    charge_text = ' '.join(cell.get_text(strip=True) for cell in cells)
                    if charge_text:
                        charges.append(charge_text)
            if charges:
                case_data['charges'] = charges

        # Extract docket history table (gridDockets)
        docket_table = soup.find('table', {'id': 'gridDockets'})

        if docket_table:
            docket_entries = []

            # Get headers
            headers = []
            header_row = docket_table.find('thead')
            if header_row:
                header_cells = header_row.find_all('th')
                headers = [cell.get_text(strip=True).lower().replace(' ', '_') for cell in header_cells]

            # Get docket entries
            tbody = docket_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if cells:
                        # Extract docket ID from the first column's image tag
                        docket_id = ''
                        if cells:
                            first_cell = cells[0]
                            img_tag = first_cell.find('img')
                            if img_tag:
                                # The ID is in the 'rel' attribute or 'id' attribute
                                rel_attr = img_tag.get('rel')
                                id_attr = img_tag.get('id')

                                # Handle both single values and lists
                                if rel_attr:
                                    docket_id = rel_attr[0] if isinstance(rel_attr, list) else rel_attr
                                elif id_attr:
                                    id_val = id_attr[0] if isinstance(id_attr, list) else id_attr
                                    # Remove 'img_' prefix if present
                                    docket_id = id_val.replace('img_', '') if isinstance(id_val, str) else str(id_val)

                        if headers and len(headers) == len(cells):
                            # Use headers as keys
                            entry = {headers[i]: cells[i].get_text(strip=True) for i in range(len(cells))}
                            # Replace empty first header with 'id'
                            if '' in entry:
                                entry.pop('')
                                entry['id'] = docket_id
                            else:
                                entry['id'] = docket_id
                        else:
                            # Fallback: use generic keys
                            entry = {f'column_{i}': cell.get_text(strip=True) for i, cell in enumerate(cells)}
                            entry['id'] = docket_id
                        docket_entries.append(entry)

            if docket_entries:
                case_data['docket_history'] = docket_entries

        return case_data

    def get_results_data(
        self,
        start: int = 0,
        length: int = 50,
        order_column: int = 4,
        order_direction: str = 'desc'
    ) -> Dict[str, Any]:
        """
        Fetch the actual search results data via AJAX endpoint.
        
        This should be called after a successful search() call.
        The search() method sets up the session, and this method retrieves
        the paginated JSON data.
        
        Args:
            start: Starting record number (for pagination)
            length: Number of records to return
            order_column: Column index to sort by (default: 4)
            order_direction: Sort direction ('asc' or 'desc')
        
        Returns:
            Dict containing the JSON response with case data
        """
        # Build DataTables-style request parameters
        params = {
            'draw': '1',
            'start': str(start),
            'length': str(length),
            'search[value]': '',
            'search[regex]': 'false',
            f'order[0][column]': str(order_column),
            f'order[0][dir]': order_direction,
        }
        
        # Add column definitions (required by DataTables)
        for i in range(6):  # 6 columns in the results table
            params[f'columns[{i}][data]'] = str(i)
            params[f'columns[{i}][searchable]'] = 'true'
            params[f'columns[{i}][orderable]'] = 'true' if i > 0 else 'false'
            params[f'columns[{i}][search][value]'] = ''
            params[f'columns[{i}][search][regex]'] = 'false'
        
        # Fetch results data
        results_url = urljoin(self.base_url, "/BenchmarkWeb/Search.aspx/CaseSearch")

        response = self.session.post(
            results_url,
            data=params,
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': urljoin(self.base_url, '/BenchmarkWeb/CourtCase.aspx/CaseSearch'),
                'Origin': self.base_url,
            }
        )
        response.raise_for_status()

        data = response.json()
        logger.info(f"Retrieved {len(data.get('data', []))} of {data.get('recordsTotal', 0)} records")

        return data
    
    def search_and_get_results(
        self,
        search_term: str,
        search_type: str = SEARCH_TYPE_NAME,
        max_results: int = 50,
        **search_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Convenience method to search and retrieve results in one call.

        Args:
            search_term: The search term
            search_type: Type of search
            max_results: Maximum number of results to retrieve
            **search_kwargs: Additional search parameters

        Returns:
            List of case records. If the search returns a single case details page,
            returns a list with one item containing the parsed case details.
        """
        # Perform the search
        search_result = self.search(search_term, search_type, **search_kwargs)

        if not search_result.get('success'):
            return []

        response_type = search_result.get('response_type')

        if response_type == 'case_details':
            # We were redirected to a case details page (single result)
            case_url = search_result.get('url')
            if case_url:
                # Use get_case_details_with_dockets to get full data including dockets
                case_data = self.get_case_details_with_dockets(case_url)
                return [case_data]
            return []

        elif response_type == 'search_results':
            # We have a search results table (multiple results)
            # Get the results data via AJAX
            results_data = self.get_results_data(length=max_results)
            return results_data.get('data', [])

        else:
            # Unknown response type
            return []

    def get_case_summary(self, case_id: str, digest: str) -> Dict[str, Any]:
        """
        Fetch case summary details via AJAX endpoint.

        This endpoint returns the HTML for the case summary that is
        dynamically loaded when viewing a case details page.

        Args:
            case_id: The case ID (e.g., "2574263")
            digest: The digest parameter from the case URL

        Returns:
            Dict containing parsed case summary data
        """
        from datetime import datetime

        # Format time parameter (HH:MM:SS AM/PM format)
        current_time = datetime.now().strftime('%I:%M:%S %p')

        # Build the URL
        summary_url = urljoin(
            self.base_url,
            f"/BenchmarkWeb/CourtCase.aspx/DetailsSummary/{case_id}"
        )

        params = {
            'digest': digest,
            'time': current_time
        }

        logger.info(f"Fetching case summary for case {case_id}")

        response = self.session.get(
            summary_url,
            params=params,
            headers={
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': urljoin(self.base_url, f'/BenchmarkWeb/CourtCase.aspx/Details/{case_id}?digest={digest}'),
            }
        )
        response.raise_for_status()

        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse the summary data
        case_data = {}

        # Extract data from definition lists (dl-horizontal)
        detail_lists = soup.find_all('dl', class_='dl-horizontal')

        for dl in detail_lists:
            # Find all dt/dd pairs
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')

            # Match dt and dd elements
            for dt, dd in zip(dts, dds):
                label = dt.get_text(strip=True).rstrip(':')
                value = dd.get_text(strip=True)

                # Skip empty values (just non-breaking spaces)
                if label and value and value not in ['', '\xa0', '&#160;']:
                    # Convert label to lowercase key
                    key = label.lower().replace(' ', '_')
                    case_data[key] = value

        # Extract party information from the parties table
        parties_table = soup.find('table', id='gridParties')
        if parties_table:
            parties = []
            party_rows = parties_table.find('tbody')
            if party_rows:
                for row in party_rows.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        party_type = cells[0].get_text(strip=True)
                        # Extract name from the anchor tag
                        name_link = cells[1].find('a')
                        name = name_link.get_text(strip=True) if name_link else cells[1].get_text(strip=True)

                        # Extract attorney if present
                        attorney = cells[2].get_text(strip=True) if len(cells) > 2 else None

                        party = {
                            'type': party_type,
                            'name': name
                        }
                        if attorney:
                            party['attorney'] = attorney

                        parties.append(party)

            if parties:
                case_data['parties'] = parties

        # Extract charges from the charges table
        charges_table = soup.find('table', id='gridCharges')
        if charges_table:
            charges = []

            # Get headers to use as keys
            headers = []
            header_row = charges_table.find('thead')
            if header_row:
                header_cells = header_row.find_all('th')
                headers = [cell.get_text(strip=True).lower().replace(' ', '_') for cell in header_cells]

            charge_rows = charges_table.find('tbody')
            if charge_rows:
                for row in charge_rows.find_all('tr'):
                    cells = row.find_all('td')
                    if cells:
                        charge = {}
                        # Use headers if available, otherwise use generic field names
                        if headers and len(headers) == len(cells):
                            for i, cell in enumerate(cells):
                                text = cell.get_text(strip=True)
                                # Skip empty values
                                if text and text not in ['', '\xa0', '&#160;']:
                                    charge[headers[i]] = text
                        else:
                            # Fallback to generic field names
                            for i, cell in enumerate(cells):
                                text = cell.get_text(strip=True)
                                if text and text not in ['', '\xa0', '&#160;']:
                                    charge[f'field_{i}'] = text

                        if charge:
                            charges.append(charge)

            if charges:
                case_data['charges'] = charges

        logger.info(f"Extracted case summary data with {len(case_data)} fields")

        return {
            'success': True,
            'summary_data': case_data,
            'html': response.text
        }

    def get_case_dockets(self, case_id: str, digest: str) -> Dict[str, Any]:
        """
        Fetch docket history for a case via AJAX endpoint.

        This endpoint returns the HTML for the docket history table that is
        dynamically loaded when viewing a case details page.

        Args:
            case_id: The case ID (e.g., "2574263")
            digest: The digest parameter from the case URL

        Returns:
            Dict containing parsed docket history data
        """
        from datetime import datetime

        # Format time parameter (HH:MM:SS AM/PM format)
        current_time = datetime.now().strftime('%I:%M:%S %p')

        # Build the URL
        dockets_url = urljoin(
            self.base_url,
            f"/BenchmarkWeb/CourtCase.aspx/CaseDockets/{case_id}"
        )

        params = {
            'digest': digest,
            'time': current_time
        }

        logger.info(f"Fetching dockets for case {case_id}")

        response = self.session.get(
            dockets_url,
            params=params,
            headers={
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': urljoin(self.base_url, f'/BenchmarkWeb/CourtCase.aspx/Details/{case_id}?digest={digest}'),
            }
        )
        response.raise_for_status()

        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract docket table
        docket_table = soup.find('table', {'id': 'gridDockets'})

        if not docket_table:
            logger.warning("Docket table not found in response")
            return {
                'success': False,
                'docket_history': []
            }

        docket_entries = []

        # Get headers
        headers = []
        header_row = docket_table.find('thead')
        if header_row:
            header_cells = header_row.find_all('th')
            headers = [cell.get_text(strip=True).lower().replace(' ', '_') for cell in header_cells]

        # Get docket entries
        tbody = docket_table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if cells:
                    # Extract docket ID from the first column's image tag
                    docket_id = ''
                    if cells:
                        first_cell = cells[0]
                        img_tag = first_cell.find('img')
                        if img_tag:
                            # The ID is in the 'rel' attribute or 'id' attribute
                            rel_attr = img_tag.get('rel')
                            id_attr = img_tag.get('id')

                            # Handle both single values and lists
                            if rel_attr:
                                docket_id = rel_attr[0] if isinstance(rel_attr, list) else rel_attr
                            elif id_attr:
                                id_val = id_attr[0] if isinstance(id_attr, list) else id_attr
                                # Remove 'img_' prefix if present
                                docket_id = id_val.replace('img_', '') if isinstance(id_val, str) else str(id_val)

                    if headers and len(headers) == len(cells):
                        # Use headers as keys
                        entry = {headers[i]: cells[i].get_text(strip=True) for i in range(len(cells))}
                        # Replace empty first header with 'id'
                        if '' in entry:
                            entry.pop('')
                            entry['id'] = docket_id
                        else:
                            entry['id'] = docket_id
                    else:
                        # Fallback: use generic keys
                        entry = {f'column_{i}': cell.get_text(strip=True) for i, cell in enumerate(cells)}
                        entry['id'] = docket_id
                    docket_entries.append(entry)

        logger.info(f"Extracted {len(docket_entries)} docket entries")

        return {
            'success': True,
            'docket_history': docket_entries,
            'html': response.text
        }

    def get_case_details_with_dockets(self, case_url: str) -> Dict[str, Any]:
        """
        Fetch case details page, summary, and docket history.

        This is a convenience method that fetches the case details page,
        extracts the case ID and digest, then fetches both the case summary
        and docket history via AJAX endpoints.

        Args:
            case_url: Full URL to case details page

        Returns:
            Dict containing complete case data including summary and docket history
        """
        import re

        # Fetch the case details page
        response = self.session.get(case_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse basic case details (including case number from title)
        case_data = self.parse_case_details(soup)
        case_data['url'] = response.url

        # Extract case ID and digest from the page JavaScript
        html = response.text

        # Look for: var cid = 2574263 + 0;
        cid_match = re.search(r'var cid = (\d+)', html)
        # Look for: var caseDigest = 'F7EKw+8ZEQL4oLpbaaU9fA';
        digest_match = re.search(r"var caseDigest = '([^']+)'", html)

        if cid_match and digest_match:
            case_id = cid_match.group(1)
            digest = digest_match.group(1)

            logger.info(f"Found case ID: {case_id}, digest: {digest}")

            # Fetch case summary
            summary_result = self.get_case_summary(case_id, digest)

            if summary_result.get('success'):
                # Merge summary data into case_data
                summary_data = summary_result.get('summary_data', {})
                case_data.update(summary_data)
            else:
                logger.warning("Failed to fetch case summary")

            # Fetch docket history
            dockets_result = self.get_case_dockets(case_id, digest)

            if dockets_result.get('success'):
                case_data['docket_history'] = dockets_result.get('docket_history', [])
            else:
                logger.warning("Failed to fetch docket history")
                case_data['docket_history'] = []
        else:
            logger.warning("Could not extract case ID and digest from page")
            case_data['docket_history'] = []

        return case_data

    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
