#!/usr/bin/env python3
"""Entry point — run as `python3 nexload.py` or `./nexload.py`."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from nexload.__main__ import main

if __name__ == "__main__":
    main()
