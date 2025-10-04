from sqlalchemy import create_engine, text
import os

# Test with SSL require mode (working configuration)
print("Testing SSL connection with require mode...")
engine_require = create_engine(
    "postgresql+psycopg2://postgres.hnmbsqydlfemlmsyexrq:Ggzzmmb3@57.182.231.186:6543/postgres",
    connect_args={
        "sslmode": "require",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

try:
    with engine_require.connect() as conn:
        result = conn.execute(text("SELECT version();")).fetchone()
        print(f"✅ SSL require mode successful: {result[0][:50]}...")
except Exception as e:
    print(f"❌ SSL require mode failed: {e}")

# Test with SSL verify-full mode using certificate
print("\nTesting SSL connection with verify-full mode...")
engine_verify = create_engine(
    "postgresql+psycopg2://postgres.hnmbsqydlfemlmsyexrq:Ggzzmmb3@57.182.231.186:6543/postgres",
    connect_args={
        "sslmode": "verify-full",
        "sslrootcert": "/Users/admin/Projects/kado-com/app/supabase-ca.pem",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

try:
    with engine_verify.connect() as conn:
        result = conn.execute(text("SELECT version();")).fetchone()
        print(f"✅ SSL verify-full mode successful: {result[0][:50]}...")
except Exception as e:
    print(f"❌ SSL verify-full mode failed: {e}")

# Test connection stability with multiple queries
print("\nTesting connection stability with multiple queries...")
try:
    with engine_require.connect() as conn:
        for i in range(3):
            result = conn.execute(text("SELECT NOW(), 'Query {}' as test;".format(i+1))).fetchone()
            print(f"Query {i+1}: {result[1]} at {result[0]}")
        print("✅ Connection stability test successful")
except Exception as e:
    print(f"❌ Connection stability test failed: {e}")