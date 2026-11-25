"""Local push-to-talk recording, whisper.cpp transcription and macOS speech."""
from __future__ import annotations
import os, shutil, subprocess, tempfile, wave
from pathlib import Path
from PySide6.QtCore import QThread, Signal
class SpeechToTextWorker(QThread):
    transcript=Signal(str); failed=Signal(str); status=Signal(str)
    def __init__(self,root:Path,duration:int=7,device:str="",parent=None): super().__init__(parent); self.root,self.duration,self.device=root,duration,device
    def run(self):
        wav_path=None
        try:
            import numpy as np, sounddevice as sd
            self.status.emit(f"Listening · speak now ({self.duration}s)"); device=int(self.device) if self.device else None
            audio=sd.rec(int(self.duration*16000),samplerate=16000,channels=1,dtype="int16",device=device); sd.wait()
            if np.max(np.abs(audio))<80: raise RuntimeError("I didn't hear anything. Check the microphone and macOS permission.")
            fd,wav_path=tempfile.mkstemp(prefix="gennie-",suffix=".wav"); os.close(fd)
            with wave.open(wav_path,"wb") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000); wf.writeframes(audio.tobytes())
            cli=os.getenv("GENNIE_WHISPER_CLI","") or shutil.which("whisper-cli") or shutil.which("whisper-cpp")
            model=Path(os.getenv("GENNIE_WHISPER_MODEL",str(self.root/"models/stt/ggml-tiny.en.bin"))).expanduser(); model=model if model.is_absolute() else self.root/model
            if not cli: raise RuntimeError("Local speech recognition isn't installed. Run: bash scripts/setup_voice.sh")
            if not model.is_file(): raise RuntimeError(f"Whisper model missing: {model}. Run scripts/setup_voice.sh")
            result=subprocess.run([cli,"-m",str(model),"-f",wav_path,"-nt","-np"],capture_output=True,text=True,timeout=120)
            if result.returncode: raise RuntimeError((result.stderr or result.stdout or "Whisper failed").strip()[-900:])
            text=" ".join(x.strip() for x in result.stdout.splitlines() if x.strip())
            if not text: raise RuntimeError("I couldn't make out the speech. Try again closer to the microphone.")
            self.transcript.emit(text)
        except Exception as exc: self.failed.emit(str(exc))
        finally:
            if wav_path:
                try: os.unlink(wav_path)
                except OSError: pass
class TextToSpeechWorker(QThread):
    finished_speaking=Signal(); failed=Signal(str)
    def __init__(self,text:str,parent=None): super().__init__(parent); self.text=text
    def run(self):
        try:
            if not shutil.which("say"): raise RuntimeError("Local speech output requires macOS 'say'.")
            subprocess.run(["say",self.text],check=True,timeout=180); self.finished_speaking.emit()
        except Exception as exc: self.failed.emit(str(exc))
