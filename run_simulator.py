#!/usr/bin/env python3
"""
Wrapper script to run the HFT Simulator.
"""

import sys
import os

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import and run the main function
from hft_simulator.__main__ import main

if __name__ == "__main__":
    main() 