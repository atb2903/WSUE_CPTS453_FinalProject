import sys
from pathlib import Path

# Add src/ to the import path so tests can resolve map.* imports
# without requiring the package to be installed
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
