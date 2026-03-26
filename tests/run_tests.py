import sys
import os
import traceback

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import test_system
    print("Import successful!")
except Exception as e:
    print("Import failed!")
    traceback.print_exc()
