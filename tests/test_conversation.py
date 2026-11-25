import unittest

from app.brain.conversation import Conversation


class ConversationTests(unittest.TestCase):
    def test_keeps_only_supported_roles(self):
        conversation = Conversation("test-id", [
            {"role": "user", "content": "hello"},
            {"role": "tool", "content": "ignore me"},
            {"role": "assistant", "content": "hi"},
        ])
        self.assertEqual([item["role"] for item in conversation.messages], ["user", "assistant"])

    def test_bounds_history(self):
        conversation = Conversation("test-id", max_history_messages=2)
        conversation.add("user", "one")
        conversation.add("assistant", "two")
        conversation.add("user", "three")
        self.assertEqual([m["content"] for m in conversation.messages], ["two", "three"])

    def test_prompt_includes_personality_first(self):
        conversation = Conversation("test-id")
        conversation.add("user", "hello")
        self.assertEqual(conversation.prompt_messages("be Gennie")[0], {"role": "system", "content": "be Gennie"})


if __name__ == "__main__":
    unittest.main()
