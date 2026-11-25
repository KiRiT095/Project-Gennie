import unittest
from pathlib import Path

from app.brain.brain import TunaBrain
from app.brain.conversation import Conversation


class FakeProvider:
    def __init__(self):
        self.last_messages = None

    def chat(self, messages, *, response_format=None):
        self.last_messages = messages
        return "A sensible answer."


class FakeStore:
    available = False
    last_error = "not connected"

    def retrieve_memories(self, query, limit=6):
        return []

    def save_exchange(self, conversation_id, user_message, assistant_message):
        pass


class BrainTests(unittest.TestCase):
    def test_responds_with_personality_and_conversation(self):
        provider = FakeProvider()
        conversation = Conversation("test-id")
        brain = TunaBrain(provider, conversation, FakeStore())
        reply = brain.respond("Hello Gennie")
        self.assertEqual(reply, "A sensible answer.")
        self.assertEqual(conversation.messages[-1]["role"], "assistant")
        self.assertIn("You are Gennie", provider.last_messages[0]["content"])

    def test_emoji_are_removed_from_model_replies(self):
        provider = FakeProvider()
        provider.chat = lambda messages, response_format=None: "All right! 🎉🙂  Let's start. 🚀"
        conversation = Conversation("test-id")
        brain = TunaBrain(provider, conversation, FakeStore())
        reply = brain.respond("Let's start")
        self.assertEqual(reply, "All right! Let's start.")
        self.assertEqual(conversation.messages[-1]["content"], reply)

    def test_emoji_only_reply_gets_a_safe_fallback(self):
        provider = FakeProvider()
        provider.chat = lambda messages, response_format=None: "🎉🙂🚀"
        brain = TunaBrain(provider, Conversation("test-id"), FakeStore())
        self.assertEqual(brain.respond("Hello"), "I'm here. What would you like to talk about?")


if __name__ == "__main__":
    unittest.main()
