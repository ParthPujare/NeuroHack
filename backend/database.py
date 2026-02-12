import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Supabase connection parameters (separate vars as recommended)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

POOL = None

async def init_pool():
    global POOL
    if not DB_USER or not DB_PASSWORD or not DB_HOST:
        print("WARNING: DB_USER, DB_PASSWORD, or DB_HOST is not set. Database features will be unavailable.")
        return
    try:
        # statement_cache_size=0 is required for Supabase connection pooler
        POOL = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
            ssl='require',
            statement_cache_size=0,
        )
        print("✓ Database pool initialized successfully.")
    except OSError as e:
        POOL = None
        print(f"WARNING: Failed to connect to database: {e}")
        print("Database features will be unavailable.")
    except Exception as e:
        POOL = None
        print(f"WARNING: Failed to connect to database: {e}")
        print("Database features will be unavailable.")

async def close_pool():
    global POOL
    if POOL:
        await POOL.close()

async def get_db_connection():
    if not POOL:
        raise RuntimeError("Database pool is not available. Check your DATABASE_URL configuration.")
    return POOL.acquire()

async def init_db():
    if not POOL:
        print("Skipping database initialization (pool not available).")
        return
    try:
        async with POOL.acquire() as conn:
            # Enable UUID extension
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            
            # User Table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    email VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            ''')

            # Conversations Table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id TEXT NOT NULL,
                    title VARCHAR(500),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # Messages Table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # Indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(user_id, updated_at DESC);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(conversation_id, created_at ASC);')
            
            print("✓ Database tables initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
