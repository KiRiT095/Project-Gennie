import unittest

from app.memory.extractor import (
    extract_obvious_memory,
    looks_like_memory_candidate,
    parse_memory_payload,
)


class MemoryExtractorTests(unittest.TestCase):
    def test_candidate_gate_flags_durable_statements(self):
        self.assertTrue(looks_like_memory_candidate("My name is Aarsh."))
        self.assertTrue(looks_like_memory_candidate("I prefer minimal interfaces."))
        self.assertTrue(looks_like_memory_candidate("I'm a cybersecurity student."))

    def test_extracts_obvious_name_without_another_model_call(self):
        memories = extract_obvious_memory("My name is Aarsh.")
        self.assertEqual(memories[0]["key"], "user_name")
        self.assertIn("Aarsh", memories[0]["content"])

    def test_explicit_non_memory_instruction_is_not_a_candidate(self):
        self.assertFalse(looks_like_memory_candidate("Don't remember this."))

    def test_candidate_gate_ignores_ordinary_questions(self):
        self.assertFalse(looks_like_memory_candidate("What is Wireshark?"))
        self.assertFalse(looks_like_memory_candidate("Tell me a joke."))

    def test_valid_memory_payload(self):
        payload = '''{"decision":"save","memories":[{"key":"user_name","category":"core","content":"The user's name is Aarsh.","importance":5,"confidence":0.99}]}'''
        memories = parse_memory_payload(payload)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["key"], "user_name")

    def test_rejects_low_confidence_and_secrets(self):
        payload = '''{"decision":"save","memories":[{"key":"guess","category":"core","content":"Maybe the user's name is Sam.","importance":3,"confidence":0.4},{"key":"token","category":"long_term","content":"The API key is abc123.","importance":5,"confidence":1.0}]}'''
        self.assertEqual(parse_memory_payload(payload), [])

    def test_ignore_decision_saves_nothing(self):
        self.assertEqual(parse_memory_payload('{"decision":"ignore","memories":[]}'), [])


if __name__ == "__main__":
    unittest.main()
