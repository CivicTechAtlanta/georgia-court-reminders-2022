"""
Test package for atlanta_court.

This package contains unit tests and integration tests for the
Atlanta Court Scraper client.
"""

import sys
from pathlib import Path

# Add src directory to path for test imports
test_dir = Path(__file__).parent
project_root = test_dir.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
