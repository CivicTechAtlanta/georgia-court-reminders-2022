"""
Command-line interface for Atlanta Court case search.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .client import AtlantaMunicipalClient


def setup_logging(level: str = "INFO"):
    """Configure logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def search_command(args):
    """Execute a search command."""
    client = AtlantaMunicipalClient(base_url=args.base_url)
    
    try:
        # Determine search type
        search_type = AtlantaMunicipalClient.SEARCH_TYPE_NAME
        if args.case_number:
            search_type = AtlantaMunicipalClient.SEARCH_TYPE_CASE_NUMBER
        elif args.attorney:
            search_type = AtlantaMunicipalClient.SEARCH_TYPE_ATTORNEY
        
        # Get the search term
        search_term = args.name or args.case_number or args.attorney
        
        # Build optional parameters
        search_kwargs = {}
        if args.court_types:
            search_kwargs['court_types'] = args.court_types.split(',')
        if args.party_types:
            search_kwargs['party_types'] = args.party_types.split(',')
        if args.divisions:
            search_kwargs['divisions'] = args.divisions.split(',')
        if args.opened_from:
            search_kwargs['opened_from'] = args.opened_from
        if args.opened_to:
            search_kwargs['opened_to'] = args.opened_to
        if args.closed_from:
            search_kwargs['closed_from'] = args.closed_from
        if args.closed_to:
            search_kwargs['closed_to'] = args.closed_to
        
        # Execute search
        logging.info(f"Searching for: {search_term}")
        results = client.search_and_get_results(
            search_term=search_term,
            search_type=search_type,
            max_results=args.max_results,
            **search_kwargs
        )
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logging.info(f"Results written to: {output_path}")
        else:
            # Print to stdout
            print(json.dumps(results, indent=2))
        
        logging.info(f"Found {len(results)} results")
        
        return 0
        
    except Exception as e:
        logging.error(f"Search failed: {e}", exc_info=True)
        return 1
    
    finally:
        client.close()


def main():
    """Main CLI entry point."""
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='Search Atlanta Municipal Court cases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search by name
  atlanta-court search --name "Doe, John"
  
  # Search by case number
  atlanta-court search --case-number "2024-CR-12345"
  
  # Search with date range
  atlanta-court search --name "Smith, Jane" --opened-from 2024-01-01 --opened-to 2024-12-31
  
  # Save results to file
  atlanta-court search --name "Johnson, Bob" --output results.json
  
  # Increase verbosity
  atlanta-court search --name "Brown, Alice" --verbose
        """
    )
    
    # Global options
    parser.add_argument(
        '--base-url',
        default=os.getenv('COURT_BASE_URL', AtlantaMunicipalClient.DEFAULT_BASE_URL),
        help='Base URL for the court system (default: Atlanta Municipal Court)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--log-level',
        default=os.getenv('LOG_LEVEL', 'INFO'),
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for court cases')
    
    # Search type (mutually exclusive)
    search_type_group = search_parser.add_mutually_exclusive_group(required=True)
    search_type_group.add_argument(
        '--name',
        help='Search by name (format: "Last, First")'
    )
    search_type_group.add_argument(
        '--case-number',
        help='Search by case number'
    )
    search_type_group.add_argument(
        '--attorney',
        help='Search by attorney name'
    )
    
    # Optional search filters
    search_parser.add_argument(
        '--court-types',
        help='Comma-separated court type IDs (default: 22,2,20,21,7,10)'
    )
    search_parser.add_argument(
        '--party-types',
        help='Comma-separated party type IDs (default: 1,2,3,4,5)'
    )
    search_parser.add_argument(
        '--divisions',
        help='Comma-separated division IDs (default: 1)'
    )
    search_parser.add_argument(
        '--opened-from',
        help='Case opened from date (YYYY-MM-DD)'
    )
    search_parser.add_argument(
        '--opened-to',
        help='Case opened to date (YYYY-MM-DD)'
    )
    search_parser.add_argument(
        '--closed-from',
        help='Case closed from date (YYYY-MM-DD)'
    )
    search_parser.add_argument(
        '--closed-to',
        help='Case closed to date (YYYY-MM-DD)'
    )
    search_parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum number of results to return (default: 50)'
    )
    search_parser.add_argument(
        '--output', '-o',
        help='Output file path (JSON format). If not specified, prints to stdout'
    )
    
    search_parser.set_defaults(func=search_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else args.log_level
    setup_logging(log_level)
    
    # Execute command
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
