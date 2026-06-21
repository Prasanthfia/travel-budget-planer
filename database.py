@@ -0,0 +1,20 @@
"""
database.py
MySQL connection helper using mysql-connector-python.
"""

import mysql.connector


DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "your_password",   # ← change this
    "database": "travel",
}


def get_db_connection():
    """Return a new MySQL connection."""
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn
