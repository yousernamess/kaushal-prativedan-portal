"""Apply database migration to add question text and options."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL not found in environment")
    sys.exit(1)

# Convert psycopg URL to psycopg2 format if needed
if 'psycopg' in db_url:
    db_url = db_url.replace('postgresql+psycopg://', 'postgresql://')

print(f"Connecting to database...")

try:
    import psycopg2
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Check if columns already exist
    cur.execute('''
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'questions' AND column_name IN ('question_text', 'option_a', 'option_b', 'option_c', 'option_d')
    ''')
    existing = [row[0] for row in cur.fetchall()]
    
    # Add missing columns
    columns_to_add = [
        ('question_text', 'VARCHAR(500)'),
        ('option_a', 'VARCHAR(200)'),
        ('option_b', 'VARCHAR(200)'),
        ('option_c', 'VARCHAR(200)'),
        ('option_d', 'VARCHAR(200)')
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing:
            cur.execute(f'ALTER TABLE questions ADD COLUMN {col_name} {col_type}')
            print(f'✓ Added column: {col_name}')
        else:
            print(f'• Column already exists: {col_name}')
    
    conn.commit()
    cur.close()
    conn.close()
    print('\nMigration completed successfully!')
    
except ImportError:
    print("ERROR: psycopg2 module not found. Please install it with: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
