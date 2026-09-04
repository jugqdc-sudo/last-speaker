# -*- coding: utf-8 -*-
"""SCOUT · owns the tapes, the cuts.
Cuts the tape into utterances by voice activity (silero-vad). Interprets nothing."""
import torch
from silero_vad import load_silero_vad, get_speech_timestamps
from core.tape import SR

# stops · never names a meaning


def run(audio, log):
    model = load_silero_vad()
    wav = torch.from_numpy(audio)
    ts = get_speech_timestamps(
        wav, model, sampling_rate=SR,
        min_speech_duration_ms=400, max_speech_duration_s=12,
        min_silence_duration_ms=350, speech_pad_ms=60, return_seconds=True,
    )
    utts = [{"id": i, "start": round(t["start"], 2), "end": round(t["end"], 2)} for i, t in enumerate(ts)]
    spoken = sum(u["end"] - u["start"] for u in utts)
    log("SCOUT", f"cut the tape into {len(utts)} utterances · {spoken/60:.1f} min of speech in {len(audio)/SR/60:.1f} min of tape")
    return utts
