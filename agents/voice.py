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


def fatigue(utts, log, window_min=10.0):
    """How the voice holds up ACROSS one tape - the honest version of a voice budget.

    The serial talks about minutes of usable voice draining week by week. On real tape we
    only have one sitting, so the only thing that can be measured without inventing data is
    what happens INSIDE it: does he speak slower, in shorter bursts, lower, as the hours go?

    Reports the trend and says plainly when there is none. A flat line is a result.
    """
    import numpy as np
    if not utts:
        return {"windows": [], "trend": None}
    end = max(u["end"] for u in utts)
    nwin = max(1, int(end // (window_min * 60)) + 1)
    rows = []
    for w in range(nwin):
        lo, hi = w * window_min * 60, (w + 1) * window_min * 60
        chunk = [u for u in utts if lo <= u["start"] < hi]
        if len(chunk) < 10:
            continue
        rates = [u["rate"] for u in chunk if u.get("rate")]
        f0s = [u["f0"] for u in chunk if u.get("f0")]
        durs = [u["end"] - u["start"] for u in chunk]
        speech = sum(durs)
        rows.append({
            "window": f"{int(lo//60):02d}:00-{int(min(hi,end)//60):02d}:00",
            "utterances": len(chunk),
            "speech_share": round(speech / max(1.0, min(hi, end) - lo), 3),
            "rate": round(float(np.median(rates)), 2) if rates else None,
            "f0": round(float(np.median(f0s)), 1) if f0s else None,
            "utt_seconds": round(float(np.median(durs)), 2),
        })
    trend = None
    if len(rows) >= 3:
        x = np.arange(len(rows), dtype=float)
        out = {}
        for key in ("rate", "speech_share", "utt_seconds"):
            y = np.array([r[key] for r in rows], dtype=float)
            if np.isnan(y).any():
                continue
            slope = float(np.polyfit(x, y, 1)[0])
            rel = slope / max(1e-9, abs(float(y.mean())))
            out[key] = {"per_window": round(slope, 4), "per_window_pct": round(rel * 100, 2)}
        trend = out
        worst = max(out.items(), key=lambda kv: -kv[1]["per_window_pct"]) if out else None
        if worst and worst[1]["per_window_pct"] <= -3.0:
            log("PHON", f"he fades across the tape: {worst[0]} drops {abs(worst[1]['per_window_pct']):.1f}% "
                        f"per {int(window_min)} minutes over {len(rows)} windows")
        else:
            log("PHON", f"no fade across {len(rows)} windows of {int(window_min)} min - he holds the same "
                        f"tempo to the end. a flat line is a result, not a missing measurement")
    return {"windows": rows, "trend": trend, "window_min": window_min}
