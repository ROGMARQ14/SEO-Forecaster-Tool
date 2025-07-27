#!/usr/bin/env python3
"""Entry point for the SEO Performance Forecaster application."""

import subprocess
import os

if __name__ == "__main__":
    # Change to the correct directory and run Streamlit
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    subprocess.run(["streamlit", "run", "app.py", "--server.port=8506"])
