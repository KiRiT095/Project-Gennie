import unittest

from app.memory.manager import MemoryManager


class FakeStore:
    available = True

    def __init__(self):
        self.saved = []

    def upsert_memory(self, **kwargs):
        self.saved.append(kwargs)

    def list_memories(self):
        return []

    def forget_memories(self, phrase):
        return 0


class FakeProvider:
    def chat(self, messages, *, response_format=None):
        raise AssertionError("The obvious-fact path should not make a second model call.")


class MemoryManagerTests(unittest.TestCase):
    def test_obvious_name_is_saved_without_second_inference(self):
        store = FakeStore()
        manager = MemoryManager(store, FakeProvider())
        try:
            manager.schedule_extraction("My name is Aarsh.")
            self.assertEqual(len(store.saved), 1)
            self.assertEqual(store.saved[0]["memory_key"], "user_name")
            self.assertIn("Aarsh", store.saved[0]["content"])
        finally:
            manager.shutdown()

    def test_explicit_secret_is_rejected(self):
        store = FakeStore()
        manager = MemoryManager(store, FakeProvider())
        try:
            with self.assertRaises(ValueError):
                manager.remember_explicit("My API key is abc123")
            self.assertEqual(store.saved, [])
        finally:
            manager.shutdown()

    def test_ordinary_question_does_not_create_memory(self):
        store = FakeStore()
        manager = MemoryManager(store, FakeProvider())
        try:
            manager.schedule_extraction("What is Wireshark?")
            self.assertEqual(store.saved, [])
        finally:
            manager.shutdown()


if __name__ == "__main__":
    unittest.main()
