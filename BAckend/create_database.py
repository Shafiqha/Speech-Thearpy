"""
Create the database if it doesn't exist
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Database credentials
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'aphasia_therapy_db')

try:
    # Connect to MySQL without specifying a database
    if DB_PASSWORD:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
    else:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            charset='utf8mb4'
        )
    
    cursor = connection.cursor()
    
    # Create database if it doesn't exist
    print(f"Creating database '{DB_NAME}' if it doesn't exist...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"✅ Database '{DB_NAME}' ready")
    
    cursor.close()
    connection.close()
    
    print("\n✅ Database creation successful!")
    print("Now run: python init_database.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure:")
    print("1. MySQL is running (XAMPP)")
    print("2. .env file exists with correct credentials")
