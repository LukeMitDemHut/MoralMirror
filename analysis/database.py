"""
Database Connection Module

Provides easy connection to the MySQL database using SQLAlchemy.
Database credentials are loaded from a .env file in the analysis directory.
"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from models import Base


class Database:
    """Database connection manager"""
    
    def __init__(self, env_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            env_path: Path to .env file. If None, looks in current directory.
        """
        # Load environment variables
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # Get database credentials from environment
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.database = os.getenv('DB_NAME', 'symfony')
        self.user = os.getenv('DB_USER', 'symfony')
        self.password = os.getenv('DB_PASSWORD', '')
        
        # Create connection string
        connection_string = (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset=utf8mb4"
        )
        
        # Create engine
        self.engine = create_engine(
            connection_string,
            echo=False,  # Set to True to see SQL queries
            pool_pre_ping=True  # Verify connections before using
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session object
            
        Example:
            db = Database()
            session = db.get_session()
            try:
                # Do queries
                participants = session.query(Participant).all()
            finally:
                session.close()
        """
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """
        Test if database connection works.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def create_tables(self):
        """
        Create all tables in the database.
        WARNING: This should not be needed as tables already exist from Symfony.
        """
        Base.metadata.create_all(bind=self.engine)
    
    def __enter__(self):
        """Context manager entry"""
        self.session = self.get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            self.session.rollback()
        self.session.close()


def get_db() -> Database:
    """
    Convenience function to get a database instance.
    
    Returns:
        Database instance
    """
    return Database()


# Example usage
if __name__ == "__main__":
    # Test connection
    db = get_db()
    
    if db.test_connection():
        print("✓ Database connection successful!")
        
        # Test query
        with db as session:
            from models import Participant, Vignette
            
            participant_count = session.query(Participant).count()
            vignette_count = session.query(Vignette).count()
            
            print(f"✓ Found {participant_count} participants")
            print(f"✓ Found {vignette_count} vignettes")
    else:
        print("✗ Database connection failed!")
        print("\nMake sure to create a .env file with:")
        print("DB_HOST=localhost")
        print("DB_PORT=3306")
        print("DB_NAME=symfony")
        print("DB_USER=symfony")
        print("DB_PASSWORD=your_password")
