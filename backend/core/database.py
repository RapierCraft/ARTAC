"""
ARTAC Database Configuration
PostgreSQL with pgvector for embeddings
"""

import logging
from core.database_postgres import db

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager - proxy to PostgreSQL implementation"""
    
    def __init__(self):
        self.postgres_db = db
        self.is_connected = False
    
    async def connect(self):
        """Initialize database connection and setup"""
        success = await self.postgres_db.connect()
        self.is_connected = success
        return success
    
    async def disconnect(self):
        """Close database connections"""
        await self.postgres_db.disconnect()
        self.is_connected = False
    
    async def execute(self, query: str, *args):
        """Execute a raw SQL query"""
        return await self.postgres_db.execute(query, *args)
    
    async def fetch_one(self, query: str, *args):
        """Fetch one row from query"""
        return await self.postgres_db.fetch_one(query, *args)
    
    async def fetch_all(self, query: str, *args):
        """Fetch all rows from query"""
        return await self.postgres_db.fetch_all(query, *args)
    
    async def fetch_val(self, query: str, *args):
        """Fetch single value from query"""
        return await self.postgres_db.fetch_val(query, *args)


# Global database instance
database = Database()