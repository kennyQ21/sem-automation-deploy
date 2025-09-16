"""
Service for handling all interactions with the database.
"""
import logging
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any
import os

class DatabaseService:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or "sqlite:///sem_automation.db"
        self.conn = None
        self._connect()
        self._initialize_schema()

    def _connect(self):
        """Establish a connection to the database."""
        try:
            if self.db_url.startswith('sqlite:'):
                # Extract the database path from SQLite URL
                db_path = self.db_url.replace('sqlite:///', '').replace('sqlite://', '')
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
                self.conn = sqlite3.connect(db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
                logging.info(f"Successfully connected to SQLite database: {db_path}")
            else:
                # Try PostgreSQL connection
                import psycopg2
                from psycopg2.extras import execute_values
                from pgvector.psycopg2 import register_vector
                self.conn = psycopg2.connect(self.db_url)
                register_vector(self.conn)
                logging.info("Successfully connected to PostgreSQL database.")
        except Exception as e:
            logging.error(f"Could not connect to the database: {e}")
            raise

    def _initialize_schema(self):
        """Ensure the required table for keyword vectors exists."""
        cur = self.conn.cursor()
        
        try:
            if self.db_url.startswith('sqlite:'):
                # SQLite schema - execute statements separately
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS keyword_vectors (
                        id TEXT PRIMARY KEY,
                        job_id TEXT NOT NULL,
                        vector TEXT NOT NULL,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON keyword_vectors (job_id)")
            else:
                # PostgreSQL schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS keyword_vectors (
                        id VARCHAR(255) PRIMARY KEY,
                        job_id VARCHAR(255) NOT NULL,
                        vector vector(384) NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON keyword_vectors (job_id)")
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Schema initialization failed: {e}")
            raise
        finally:
            cur.close()

    def upsert_keywords(self, job_id: str, keywords_data: List[Dict[str, Any]]):
        """
        Insert or update keyword vectors in the database.
        `keywords_data` should be a list of dicts with keys: 'id', 'vector', 'metadata'.
        """
        if not keywords_data:
            return

        cur = self.conn.cursor()
        
        try:
            if self.db_url.startswith('sqlite:'):
                # SQLite upsert
                for item in keywords_data:
                    vector_str = json.dumps(item['vector'])
                    metadata_str = json.dumps(item['metadata'])
                    
                    cur.execute("""
                        INSERT OR REPLACE INTO keyword_vectors (id, job_id, vector, metadata)
                        VALUES (?, ?, ?, ?)
                    """, (item['id'], job_id, vector_str, metadata_str))
            else:
                # PostgreSQL upsert
                from psycopg2.extras import execute_values
                data_to_insert = [
                    (
                        item['id'],
                        job_id,
                        np.array(item['vector']),
                        json.dumps(item['metadata'])
                    )
                    for item in keywords_data
                ]
                
                upsert_query = """
                INSERT INTO keyword_vectors (id, job_id, vector, metadata)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    vector = EXCLUDED.vector,
                    metadata = EXCLUDED.metadata;
                """
                execute_values(cur, upsert_query, data_to_insert, template=None, page_size=100)
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Database upsert failed: {e}")
            raise
        finally:
            cur.close()