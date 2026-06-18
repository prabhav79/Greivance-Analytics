import sys
import os

print("--- Diagnostic Check ---")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

try:
    import streamlit as st
    print(f"Streamlit version: {st.__version__}")
except ImportError as e:
    print(f"CRITICAL: Streamlit not found: {e}")

try:
    import database
    print("Database module imported successfully.")
    database.init_db()
    print("Database initialized successfully.")
except Exception as e:
    print(f"CRITICAL: Database initialization failed: {e}")

try:
    import analyzer
    print("Analyzer module imported successfully.")
except Exception as e:
    print(f"CRITICAL: Analyzer import failed: {e}")

try:
    import pandas as pd
    print(f"Pandas version: {pd.__version__}")
except ImportError as e:
    print(f"CRITICAL: Pandas not found: {e}")

print("--- End of Check ---")
