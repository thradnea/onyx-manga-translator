import sqlite3
import os
import threading
from typing import Union, List, Tuple


class TranslationMemory:
    def __init__(self, db_path="translation_memory.db"):
        self.db_path = db_path
        self._thread_local = threading.local()
        self._create_table()

    def _get_connection(self):
        if not hasattr(self._thread_local, 'conn'):
            try:
                self._thread_local.conn = sqlite3.connect(self.db_path)
            except sqlite3.Error as e:
                print(f"❌ Database connection error on thread {threading.get_ident()}: {e}")
                raise
        return self._thread_local.conn

    def _create_table(self):
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS translations (
                        id INTEGER PRIMARY KEY,
                        source_text TEXT NOT NULL UNIQUE,
                        translated_text TEXT NOT NULL,
                        quality_score INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except sqlite3.Error as e:
            print(f"❌ Error creating table: {e}")

    def lookup(self, source_text: str) -> Union[str, None]:
        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.execute(
                    "SELECT translated_text FROM translations WHERE source_text = ? AND quality_score > 0",
                    (source_text,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"❌ Error looking up translation: {e}")
            return None

    def add_translation(self, source_text: str, translated_text: str):
        try:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    "INSERT OR IGNORE INTO translations (source_text, translated_text) VALUES (?, ?)",
                    (source_text, translated_text)
                )
        except sqlite3.Error as e:
            print(f"❌ Error adding translation: {e}")

    def fetch_all_entries(self, search_term: str = "") -> List[Tuple[int, str, str]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT id, source_text, translated_text FROM translations"
            params_list = []

            if search_term:
                query += " WHERE source_text LIKE ? OR translated_text LIKE ?"
                search_pattern = f"%{search_term}%"
                params_list.extend([search_pattern, search_pattern])

            query += " ORDER BY id DESC"
            cursor.execute(query, tuple(params_list))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"❌ Error fetching all entries: {e}")
            return []

    def update_translation(self, source_text: str, new_translated_text: str):
        try:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    "UPDATE translations SET translated_text = ?, quality_score = 10 WHERE source_text = ?",
                    (new_translated_text, source_text)
                )
            print(f"✅ Updated translation for: {source_text[:30]}...")
        except sqlite3.Error as e:
            print(f"❌ Error updating translation: {e}")

    def delete_entry(self, source_text: str):
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("DELETE FROM translations WHERE source_text = ?", (source_text,))
            print(f"✅ Deleted translation for: {source_text[:30]}...")
        except sqlite3.Error as e:
            print(f"❌ Error deleting entry: {e}")

    def count_entries(self) -> int:
        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.execute("SELECT COUNT(id) FROM translations")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def close(self):
        if hasattr(self._thread_local, 'conn'):
            self._thread_local.conn.close()
            del self._thread_local.conn

    def flush_all(self):
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("DELETE FROM translations")
                try:
                    conn.execute("DELETE FROM sqlite_sequence WHERE name='translations'")
                except sqlite3.Error as e:
                    if "no such table" not in str(e):
                        print(f"⚠️ Could not reset table sequence: {e}")
            print("✅ Database flushed successfully and committed.")
        except sqlite3.Error as e:
            print(f"❌ Error during database flush transaction: {e}")