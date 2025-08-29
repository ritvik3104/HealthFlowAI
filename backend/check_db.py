import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load the .env file from the current directory
load_dotenv()

# Get the database URL
db_url = os.getenv("DATABASE_URL")

print("--- Database Connection Test ---")
print(f"Attempting to connect to URL: {db_url}")

if not db_url:
    print("\nERROR: DATABASE_URL not found in .env file or environment!")
    exit()

try:
    # Create an engine and connect
    engine = create_engine(db_url)
    with engine.connect() as connection:
        print("Successfully connected to the database.")
        
        # Try to run a query against the 'users' table
        print("Querying the 'users' table...")
        result = connection.execute(text("SELECT COUNT(*) FROM users;"))
        count = result.scalar_one()
        print(f"SUCCESS: The 'users' table exists and contains {count} rows.")
        
except Exception as e:
    print(f"\nERROR: An error occurred.")
    print(e)

print("--- Test Complete ---")