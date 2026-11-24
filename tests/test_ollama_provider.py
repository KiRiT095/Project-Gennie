import io
import json
import unittest
from unittest.mock import patch

from app.brain.providers.ollama import OllamaProvider


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class OllamaProviderTests(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_uses_native_chat_and_disables_thinking(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeHTTPResponse({"message": {"content": "Hello."}})
        provider = OllamaProvider(model="qwen3:4b")
        result = provider.chat([{"role": "user", "content": "Hi"}])
        self.assertEqual(result, "Hello.")
        request = mocked_urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertFalse(body["think"])
        self.assertFalse(body["stream"])

    @patch("urllib.request.urlopen")
    def test_does_not_return_thinking_block(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeHTTPResponse({
            "message": {"content": "<think>private reasoning</think>Answer."}
        })
        result = OllamaProvider().chat([{"role": "user", "content": "Hi"}])
        self.assertEqual(result, "Answer.")


if __name__ == "__main__":
    unittest.main()
