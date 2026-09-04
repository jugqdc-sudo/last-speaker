# -*- coding: utf-8 -*-
"""VOICE · owns how he sounds.
Pitch and tempo per utterance. Register 2σ off his own median = he is not using his own voice
(quoting, imitating, joking). A text-only corpus cannot hear this at all."""
import os
import numpy as np
import parselmouth
from core import tape

# stops · never plays it to him twice


def run(audio, utts, log, z_thr=2.0):
    f0s, rates = [], []
    for u in utts:
        p = tape.slice_to_tmp(audio, u["start"], u["end"])
        try:
            snd = parselmouth.Sound(p)
            pitch = snd.to_pitch(time_step=0.02, pitch_floor=60, pitch_ceiling=400)
            f = pitch.selected_array["frequency"]
            f = f[f > 0]
        finally:
            os.unlink(p)
        f0 = float(np.median(f)) if len(f) > 5 else float("nan")
        dur = u["end"] - u["start"]
        rate = len(u.get("phones", [])) / dur if dur > 0 else float("nan")
        u["f0"], u["rate"] = (round(f0, 1) if f0 == f0 else None), round(rate, 2)
        f0s.append(f0); rates.append(rate)
    f0s, rates = np.array(f0s, dtype=float), np.array(rates, dtype=float)
    ok = ~np.isnan(f0s) & ~np.isnan(rates)
    mf, sf_ = np.nanmedian(f0s), np.nanstd(f0s[ok]) or 1.0
    mr, sr_ = np.nanmedian(rates), np.nanstd(rates[ok]) or 1.0
    shifts = []
    for u, f0, r in zip(utts, f0s, rates):
        if np.isnan(f0) or np.isnan(r): u["register"] = None; continue
        zf, zr = (f0 - mf) / sf_, (r - mr) / sr_
        u["register"] = {"z_pitch": round(float(zf), 2), "z_rate": round(float(zr), 2)}
        if zf >= z_thr or zr >= z_thr or zf <= -z_thr:
            shifts.append({"utt": u["id"], "pos": tape.pos(u["start"]), "f0": u["f0"], "rate": u["rate"],
                           "z_pitch": u["register"]["z_pitch"], "z_rate": u["register"]["z_rate"]})
    log("VOICE", f"his voice: median pitch {mf:.0f} Hz, {mr:.1f} phones/s · {len(shifts)} utterances where the register shifts (pitch up, tempo up: not his usual voice)")
    return {"median_f0": round(float(mf), 1), "median_rate": round(float(mr), 2), "shifts": shifts}
