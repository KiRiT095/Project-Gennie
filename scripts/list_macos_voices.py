"""List the speech voices installed on macOS and show Gennie's current choice."""
from app.voice.text_to_speech import choose_voice, list_macos_voices

voices = list_macos_voices()
if not voices:
    print("No macOS `say` voices found (this utility is intended for macOS).")
else:
    selected = choose_voice()
    print("Installed macOS voices:")
    for name, locale in voices:
        marker = "  < Gennie's current choice" if name == selected else ""
        print(f"  {name} ({locale}){marker}")
    print("\nSet GENNIE_TTS_VOICE in .env to choose a different installed voice.")
