"""
Database initialization script.
Run this to ensure all database tables are created.
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database tables"""
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobfinder.db")
    
    print(f"Connecting to database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    if DATABASE_URL.startswith("postgresql"):
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
    else:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    try:
        # Import models to register them with Base
        from app.models import Base
        from app.models import UserProfile, UserPreferences, UserUpload
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            if DATABASE_URL.startswith("postgresql"):
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
            else:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """))
            
            tables = [row[0] for row in result]
            print(f"\n✅ Database initialized successfully!")
            print(f"📊 Created tables: {', '.join(tables)}")
            
            # Check if tables have the expected structure
            expected_tables = ['user_profiles', 'user_preferences', 'user_uploads']
            missing = [t for t in expected_tables if t not in tables]
            if missing:
                print(f"⚠️  Warning: Missing tables: {', '.join(missing)}")
            else:
                print("✅ All expected tables are present")
                
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database()

