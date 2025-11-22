"""
Example script to fetch case data for multiple case numbers using the Atlanta Court scraper.

This demonstrates how to use the main() function from atlanta_court.client to search
for multiple cases and save them to individual JSON files.
"""

import logging
from pathlib import Path

from dotenv import load_dotenv

from atlanta_court.client import main, AtlantaMunicipalClient

# Example case numbers to fetch
case_numbers = [
    '15TR118118',
    '14TR135255'
]


def setup_logging(level: str = "INFO"):
    """Configure logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def fetch_case_data(case_number: str, output_dir: str = "case_data"):
    """
    Fetch case data for a single case number and save to file.

    Args:
        case_number: The case number to search for
        output_dir: Directory to save the JSON file (default: "case_data")

    Returns:
        0 on success, 1 on failure
    """
    output_path = Path(output_dir) / f"{case_number}.json"

    try:
        # Use the main function to search by case number
        results = main(
            search_term=case_number,
            search_type=AtlantaMunicipalClient.SEARCH_TYPE_CASE_NUMBER,
            output_path=str(output_path)
        )

        logging.info(f"Successfully fetched {len(results)} result(s) for {case_number}")
        return 0

    except Exception as e:
        logging.error(f"Failed to fetch case {case_number}: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging(level="INFO")

    # Fetch data for each case number
    for i, case in enumerate(case_numbers):
        print(f"\n[{i+1}/{len(case_numbers)}] Fetching case: {case}")
        fetch_case_data(case, output_dir="case_data")
