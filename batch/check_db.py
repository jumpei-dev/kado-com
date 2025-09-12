#!/usr/bin/env python3
import asyncio
from core.database import DatabaseManager

async def check_recent_data():
    db = DatabaseManager()
    try:
        # First check what tables exist
        tables = await db.fetch_all(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        print('Available tables:')
        for table in tables:
            print(f'  - {table[0]}')
        
        # Try to find cast-related data
        if any('cast' in str(table[0]).lower() for table in tables):
            cast_table = next(table[0] for table in tables if 'cast' in str(table[0]).lower())
            print(f'\nChecking {cast_table} table:')
            result = await db.fetch_all(f'SELECT * FROM {cast_table} ORDER BY collected_at DESC LIMIT 5')
            for r in result:
                print(f'  {r}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if hasattr(db, 'close'):
            await db.close()

if __name__ == '__main__':
    asyncio.run(check_recent_data())