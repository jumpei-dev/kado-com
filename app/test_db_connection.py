#!/usr/bin/env python3
from core.database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)

def test_db_connection():
    print('Testing database connection with query...')
    try:
        dm = DatabaseManager()
        with dm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            print(f'Query result: {result}')
            print('Query test successful!')
    except Exception as e:
        print(f'Query test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_db_connection()