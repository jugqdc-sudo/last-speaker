# -*- coding: utf-8 -*-
"""The tape: loading audio, slicing chunks, formatting positions.
Every agent goes through tape, so every finding carries a position you can go and listen to."""
import os, tempfile
import numpy as np
import soundfile as sf

SR = 16000


def load(path, limit_min=None):
    """wav → float32 mono 16k. limit_min keeps only the first N minutes (for quick runs)."""
    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SR:
        raise SystemExit(f"need {SR} Hz, file is {sr}. Re-encode: ffmpeg -i in -ac 1 -ar 16000 out.wav")
    if limit_min:
        audio = audio[: int(limit_min * 60 * SR)]
    return audio


def slice_(audio, start, end):
    return audio[int(start * SR): int(end * SR)]


def slice_to_tmp(audio, start, end):
    """A chunk of tape into a temp wav (allosaurus and praat read files)."""
    fd, p = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(p, slice_(audio, start, end), SR)
    return p


def pos(sec):
    """A tape position the way the log writes it: 01:12:03."""
    sec = int(sec)
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def hours(sec):
    return round(sec / 3600, 2)
