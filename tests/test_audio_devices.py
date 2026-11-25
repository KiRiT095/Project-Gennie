import unittest

from app.voice.audio_devices import select_input_device


class FakeSoundDevice:
    def __init__(self, devices):
        self.devices = devices

    def query_devices(self, device=None):
        if device is not None:
            return self.devices[device]
        return self.devices


class AudioDeviceTests(unittest.TestCase):
    def test_prefers_builtin_mac_microphone_over_continuity_mic(self):
        sd = FakeSoundDevice([
            {"name": "Aarsh's iPhone Microphone", "max_input_channels": 1},
            {"name": "Background Music", "max_input_channels": 2},
            {"name": "MacBook Air Microphone", "max_input_channels": 1},
        ])
        self.assertEqual(select_input_device(sd, ""), 2)

    def test_explicit_device_overrides_auto_selection(self):
        sd = FakeSoundDevice([
            {"name": "MacBook Air Microphone", "max_input_channels": 1},
            {"name": "USB Microphone", "max_input_channels": 1},
        ])
        self.assertEqual(select_input_device(sd, "1"), 1)

    def test_invalid_device_value_is_reported(self):
        sd = FakeSoundDevice([])
        with self.assertRaises(ValueError):
            select_input_device(sd, "macbook")


if __name__ == "__main__":
    unittest.main()
