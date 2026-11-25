"""Local Sherpa-ONNX wake-word worker for Gennie.

The bundled GigaSpeech KWS encoder is a Zipformer2 model. We construct the
native Sherpa config explicitly so the runtime does not misclassify it as the
older Zipformer architecture (which expects different ONNX metadata).
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal


SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1600


def build_keyword_spotter(model_dir: Path, keywords_file: Path, threshold: float = 0.25):
    """Build a GigaSpeech Zipformer2 KWS model with an explicit model type."""
    try:
        from sherpa_onnx.lib._sherpa_onnx import (
            FeatureExtractorConfig,
            KeywordSpotter as NativeKeywordSpotter,
            KeywordSpotterConfig,
            OnlineModelConfig,
            OnlineTransducerModelConfig,
            ProviderConfig,
        )
    except ImportError as exc:
        raise RuntimeError(
            "This sherpa-onnx installation does not expose its native KWS config. "
            "Reinstall the project voice dependencies with: "
            "python -m pip install --upgrade --force-reinstall sherpa-onnx"
        ) from exc

    paths = {
        "tokens": model_dir / "tokens.txt",
        "encoder": model_dir / "encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "decoder": model_dir / "decoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "joiner": model_dir / "joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Wake-word model files are missing: " + ", ".join(missing))
    if not keywords_file.is_file():
        raise FileNotFoundError(f"Wake-word keyword file is missing: {keywords_file}")

    transducer = OnlineTransducerModelConfig(
        encoder=str(paths["encoder"]),
        decoder=str(paths["decoder"]),
        joiner=str(paths["joiner"]),
    )
    provider = ProviderConfig(provider="cpu", device=0)
    online_model = OnlineModelConfig(
        transducer=transducer,
        tokens=str(paths["tokens"]),
        num_threads=2,
        provider_config=provider,
        # Critical fix: this ONNX model is Zipformer2, not legacy Zipformer.
        model_type="zipformer2",
        modeling_unit="bpe",
    )
    feature_config = FeatureExtractorConfig(
        sampling_rate=SAMPLE_RATE,
        feature_dim=80,
    )
    config = KeywordSpotterConfig(
        feat_config=feature_config,
        model_config=online_model,
        max_active_paths=4,
        num_trailing_blanks=1,
        keywords_score=1.0,
        keywords_threshold=threshold,
        keywords_file=str(keywords_file),
    )
    return NativeKeywordSpotter(config)


class WakeWordWorker(QThread):
    detected = Signal(str)
    status = Signal(str)
    failed = Signal(str)

    def __init__(self, project_root: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        default_model = (
            self.project_root / "models" / "wakeword"
            / "sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01"
        )
        model_value = Path(os.getenv("GENNIE_WAKE_MODEL_DIR", str(default_model))).expanduser()
        keywords_value = Path(
            os.getenv("GENNIE_KEYWORDS_FILE", str(self.project_root / "models" / "wakeword" / "keywords.txt"))
        ).expanduser()
        self.model_dir = model_value if model_value.is_absolute() else self.project_root / model_value
        self.keywords_file = keywords_value if keywords_value.is_absolute() else self.project_root / keywords_value
        self.threshold = float(os.getenv("GENNIE_WAKE_THRESHOLD", "0.25"))
        self.device = os.getenv("GENNIE_MIC_DEVICE", "").strip()

    def run(self) -> None:
        try:
            import numpy as np
            import sounddevice as sd

            spotter = build_keyword_spotter(
                self.model_dir, self.keywords_file, self.threshold
            )
            stream = spotter.create_stream()
            device = int(self.device) if self.device else None
            self.status.emit(
                "Local wake-word listener active — say ‘Gennie’. Audio stays on this device."
            )

            with sd.InputStream(
                device=device,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=CHUNK_SAMPLES,
            ) as microphone:
                while not self.isInterruptionRequested():
                    samples, overflowed = microphone.read(CHUNK_SAMPLES)
                    if overflowed:
                        self.status.emit(
                            "Microphone buffer overflow; a short audio segment may have been skipped."
                        )
                    stream.accept_waveform(
                        SAMPLE_RATE,
                        np.asarray(samples, dtype=np.float32).reshape(-1),
                    )
                    while spotter.is_ready(stream):
                        spotter.decode_stream(stream)
                    result = spotter.get_result(stream)
                    keyword = (
                        result if isinstance(result, str)
                        else getattr(result, "keyword", "")
                    )
                    if keyword:
                        # Notify the UI, then reset immediately to avoid repeat triggers.
                        self.detected.emit(str(keyword))
                        reset = getattr(spotter, "reset", None) or getattr(
                            spotter, "reset_stream", None
                        )
                        if reset is None:
                            raise RuntimeError(
                                "This Sherpa-ONNX build does not expose reset/reset_stream."
                            )
                        reset(stream)
                        # The ASR worker needs exclusive access to this microphone.
                        # Leaving this loop alive prevents the command recorder from starting.
                        break

            self.status.emit("Wake-word listener stopped.")
        except Exception as exc:
            self.failed.emit(f"Wake-word listener unavailable: {exc}")
