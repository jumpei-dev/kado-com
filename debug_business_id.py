#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app.core.database import get_database

async def check_business_data():
    try:
        db = await get_database()
        businesses = db.get_businesses()
        
        print(f"Total businesses: {len(businesses)}")
        print("\nFirst 10 businesses:")
        
        for i, (key, biz) in enumerate(businesses.items()):
            business_id = biz.get('Business ID')
            name = biz.get('name')
            print(f"Key: {key}, Business ID: {business_id} (type: {type(business_id)}), Name: {name}")
            
            if i >= 9:  # Show first 10
                break
                
        # Check if any business has ID 0
        zero_id_businesses = [biz for key, biz in businesses.items() if biz.get('Business ID') == 0]
        if zero_id_businesses:
            print(f"\n⚠️  Found {len(zero_id_businesses)} businesses with ID 0:")
            for biz in zero_id_businesses:
                print(f"  - {biz.get('name')} (ID: {biz.get('Business ID')})")
        else:
            print("\n✅ No businesses found with ID 0")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_business_data())