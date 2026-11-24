import unittest
from unittest.mock import patch

from app.database.postgres import PostgresStore, SCHEMA_SQL


class PostgresStoreTests(unittest.TestCase):
    def test_schema_contains_separate_conversation_and_memory_tables(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS tuna_conversations", SCHEMA_SQL)
        self.assertIn("CREATE TABLE IF NOT EXISTS tuna_messages", SCHEMA_SQL)
        self.assertIn("CREATE TABLE IF NOT EXISTS tuna_memories", SCHEMA_SQL)

    def test_search_query_keeps_relevant_terms_and_uses_or(self):
        query = PostgresStore._build_search_query("What's my name?")
        self.assertIn("name:*", query)
        self.assertNotIn("what", query)
        self.assertNotIn("my", query)

    @patch("app.database.postgres.PostgresStore._connect", side_effect=RuntimeError("offline"))
    def test_initialize_degrades_cleanly_when_database_is_offline(self, _connect):
        store = PostgresStore()
        self.assertFalse(store.initialize())
        self.assertFalse(store.available)
        self.assertIn("offline", store.last_error)


if __name__ == "__main__":
    unittest.main()
