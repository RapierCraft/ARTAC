"""
ARTAC PostgreSQL Database Connection
Real PostgreSQL implementation with asyncpg and pgvector support
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import asyncpg
from core.config import settings

logger = logging.getLogger(__name__)


class PostgreSQLDatabase:
    """PostgreSQL database connection manager with asyncpg"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.is_connected = False
        self._connection_url = settings.DATABASE_URL
    
    async def connect(self):
        """Initialize database connection pool"""
        if not self._connection_url:
            logger.error("No database URL configured")
            return False
            
        try:
            logger.info("Connecting to PostgreSQL database...")
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self._connection_url,
                min_size=2,
                max_size=settings.DATABASE_POOL_SIZE,
                command_timeout=60
            )
            
            # Test connection and enable pgvector
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
                await self._enable_pgvector(conn)
            
            self.is_connected = True
            logger.info("✅ PostgreSQL connected and initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("PostgreSQL disconnected")
    
    async def _enable_pgvector(self, conn: asyncpg.Connection):
        """Enable pgvector extension for vector operations"""
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("✅ pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Could not enable pgvector: {e}")
    
    async def execute(
        self, 
        query: str, 
        *args, 
        timeout: float = 30.0
    ) -> str:
        """Execute a query and return status"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *args, timeout=timeout)
            return result
    
    async def fetch_one(
        self, 
        query: str, 
        *args, 
        timeout: float = 30.0
    ) -> Optional[asyncpg.Record]:
        """Fetch one row from query"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetch_all(
        self, 
        query: str, 
        *args, 
        timeout: float = 30.0
    ) -> List[asyncpg.Record]:
        """Fetch all rows from query"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetch_val(
        self, 
        query: str, 
        *args, 
        timeout: float = 30.0
    ) -> Any:
        """Fetch single value from query"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args, timeout=timeout)
    
    async def execute_many(
        self, 
        query: str, 
        args_list: List[List[Any]], 
        timeout: float = 30.0
    ) -> None:
        """Execute query with multiple parameter sets"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(query, args_list, timeout=timeout)
    
    async def transaction(self):
        """Get a transaction context manager"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        return self.pool.acquire()
    
    async def create_tables_if_not_exist(self, table_definitions: Dict[str, str]):
        """Create tables if they don't exist"""
        if not self.pool:
            raise RuntimeError("Database not connected")
            
        async with self.pool.acquire() as conn:
            for table_name, create_sql in table_definitions.items():
                try:
                    await conn.execute(create_sql)
                    logger.info(f"✅ Table '{table_name}' created or already exists")
                except Exception as e:
                    logger.error(f"❌ Failed to create table '{table_name}': {e}")
                    raise


# Global database instance
db = PostgreSQLDatabase()


# Convenience functions
async def get_connection():
    """Get a database connection from the pool"""
    if not db.pool:
        raise RuntimeError("Database not connected")
    return db.pool.acquire()


async def execute_query(query: str, *args) -> str:
    """Execute a query"""
    return await db.execute(query, *args)


async def fetch_one(query: str, *args) -> Optional[asyncpg.Record]:
    """Fetch one row"""
    return await db.fetch_one(query, *args)


async def fetch_all(query: str, *args) -> List[asyncpg.Record]:
    """Fetch all rows"""
    return await db.fetch_all(query, *args)


async def fetch_val(query: str, *args) -> Any:
    """Fetch single value"""
    return await db.fetch_val(query, *args)