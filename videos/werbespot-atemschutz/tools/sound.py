#!/usr/bin/env python3
"""Synthesises the 84 s hybrid-trailer soundtrack and places the bundled SFX on the cuts.

Run from the project root:  python3 tools/sound.py
Writes assets/audio/soundtrack.mp3 (music + sound design, no voice-over).
All times are global seconds and match the scene plan in tools/gen.py.
"""
import os
import subprocess

import numpy as np

SR = 48000
DUR = 87.0
N = int(SR * DUR)
ROOT = os.path.join(os.path.dirname(__file__), "..")
SFX_DIR = "/opt/node22/lib/node_modules/hyperframes/dist/skills/media-use/audio/assets/sfx"
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)
music = [np.zeros(N), np.zeros(N)]  # music bus (gets ducked/stopped), SFX go straight to L/R


def t_arr(n):
    return np.arange(n) / SR


def env_adsr(n, a=0.005, d=0.1, s=0.0, r=0.05):
    e = np.ones(n)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na) if na else 1
    nd = min(nd, n - na)
    if nd > 0:
        e[na:na + nd] = np.linspace(1, s, nd)
    e[na + nd:] = s
    if nr and s > 0:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def add(bus, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    lg = gain * np.sqrt(0.5 * (1 - pan))
    rg = gain * np.sqrt(0.5 * (1 + pan))
    if sig.ndim == 2:
        bus[0][i:i + len(sig)] += sig[:, 0] * lg * 1.414
        bus[1][i:i + len(sig)] += sig[:, 1] * rg * 1.414
    else:
        bus[0][i:i + len(sig)] += sig * lg
        bus[1][i:i + len(sig)] += sig * rg


SFXBUS = [L, R]


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # fine for short signals only
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def onepole_fast(x, cutoff):
    # vectorised one-pole via FFT-domain filter (zero phase, good enough for pads/noise)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X * H, len(x))


def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = (1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)) * (1 / np.sqrt(1 + (f / hi) ** 4))
    return np.fft.irfft(X * H, len(x))


def load_sfx(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(SFX_DIR, name), "-f", "f32le", "-ac", "2",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)


SFX = {n: load_sfx(n + ".mp3") for n in ["click", "click-soft", "key-press", "typing", "whoosh", "whoosh-short",
                                         "whoosh-cinematic", "glitch-1", "impact-bass-1", "impact-bass-2", "notification",
                                         "ping", "riser", "sparkle", "pop"]}


def sfx(name, start, gain=1.0, pan=0.0, length=None):
    s = SFX[name]
    if length:
        s = s[: int(length * SR)].copy()
        fade = min(len(s), int(0.03 * SR))
        s[-fade:] *= np.linspace(1, 0, fade)[:, None]
    add(SFXBUS, start, s, gain, pan)


# ------------------------------------------------------------- instruments
def kick(gain=1.0, f0=150, f1=42, dur=0.45):
    n = int(dur * SR)
    t = t_arr(n)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * gain


def taiko(gain=1.0):
    n = int(0.9 * SR)
    t = t_arr(n)
    f = 58 + 70 * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    nz = bandpass(rng.standard_normal(n), 80, 900) * np.exp(-t * 30) * 0.6
    return (body + nz) * gain


def metal(gain=1.0):
    n = int(0.7 * SR)
    t = t_arr(n)
    parts = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((523, 0.4), (1187, 0.3), (1913, 0.25), (2971, 0.2), (4201, 0.12)))
    nz = bandpass(rng.standard_normal(n), 2000, 9000) * 0.5
    return (parts + nz) * np.exp(-t * 9) * gain


def hat(gain=1.0, dur=0.06):
    n = int(dur * SR)
    t = t_arr(n)
    return bandpass(rng.standard_normal(n), 7000, 16000) * np.exp(-t * 70) * gain


def clap(gain=1.0):
    n = int(0.25 * SR)
    t = t_arr(n)
    return bandpass(rng.standard_normal(n), 900, 5000) * np.exp(-t * 22) * gain


def saw(f, n, detune=0.0):
    t = t_arr(n)
    out = np.zeros(n)
    for d in (-detune, 0.0, detune):
        ph = (f * (1 + d)) * t
        out += 2 * (ph - np.floor(ph + 0.5))
    return out / 3


def pad(freqs, dur, cutoff=900, attack=1.5, release=1.5, detune=0.004):
    n = int(dur * SR)
    x = sum(saw(f, n, detune) for f in freqs) / len(freqs)
    x = onepole_fast(x, cutoff)
    e = np.ones(n)
    na, nr = int(attack * SR), int(release * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return x * e


def pluck(f, dur=0.22, gain=1.0):
    n = int(dur * SR)
    t = t_arr(n)
    x = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3.01 * f * t)
    return x * np.exp(-t * 16) * gain


def bass(f, dur, gain=1.0):
    n = int(dur * SR)
    t = t_arr(n)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * saw(f, n)
    e = np.minimum(1, t / 0.01) * np.exp(-t * 1.2)
    return x * e * gain


def tone(f, dur, gain=1.0, decay=6.0):
    n = int(dur * SR)
    t = t_arr(n)
    return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.004) * np.exp(-t * decay) * gain


def noise_swell(dur, lo, hi, gain=1.0, shape="up"):
    n = int(dur * SR)
    x = bandpass(rng.standard_normal(n), lo, hi)
    e = np.linspace(0, 1, n) ** 2 if shape == "up" else np.sin(np.linspace(0, np.pi, n))
    return x * e * gain


def hz(note):  # midi -> Hz
    return 440 * 2 ** ((note - 69) / 12)


# ------------------------------------------------------------- S1 / S2 (0-15): tension
# radio static + squelch
add(SFXBUS, 0.1, noise_swell(1.35, 400, 3200, 0.10, "bell"), 1.0, -0.3)
for tt in (0.4, 0.62, 0.9, 1.15):
    add(SFXBUS, tt, bandpass(rng.standard_normal(int(0.12 * SR)), 300, 3000) * 0.18, 1.0, 0.2)
add(SFXBUS, 1.42, tone(1800, 0.05, 0.12, 60))  # squelch tail
# sub drone 1.5 -> 14.6
n = int(13.1 * SR)
t = t_arr(n)
drone = (np.sin(2 * np.pi * hz(26) * t) + 0.5 * np.sin(2 * np.pi * hz(38) * t)) * np.minimum(1, t / 2.0) * (0.6 + 0.4 * t / 13.1)
add(music, 1.5, drone, 0.16)
# heartbeat pulse 60 bpm from 1.5 to 8
for b in np.arange(1.5, 8.0, 1.0):
    add(music, b, kick(0.32, 90, 40, 0.35))
    add(music, b + 0.22, kick(0.2, 80, 38, 0.3))
add(music, 5.0, noise_swell(3.0, 300, 6000, 0.10, "up"), 1.0)  # riser into the drive
# blue light relay + cut hits in the gear montage
sfx("click", 1.5, 0.9)
for tt in (2.2, 2.76, 3.32, 4.3, 5.0):
    sfx("whoosh-short", tt - 0.05, 0.45, pan=-0.2)
    add(SFXBUS, tt, kick(0.3, 120, 45, 0.3))
sfx("click", 2.45, 0.8)  # chin strap
add(SFXBUS, 2.9, noise_swell(0.5, 300, 2500, 0.25, "bell"))  # breath into mask
add(SFXBUS, 3.42, noise_swell(0.35, 2000, 9000, 0.35, "bell"), 1.0, 0.2)  # valve hiss
sfx("key-press", 3.45, 0.7)
sfx("click", 4.55, 0.8)  # PTT
# siren doppler on the drive 5-8
n = int(3.0 * SR)
t = t_arr(n)
f = 650 + 220 * np.sign(np.sin(2 * np.pi * 0.9 * t))
f *= 1 + 0.06 * (1.5 - t) / 1.5
siren = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, np.pi, n)) * 0.07
add(SFXBUS, 5.0, siren, 1.0, 0.3)
add(SFXBUS, 5.0, onepole_fast(rng.standard_normal(n), 900) * np.linspace(0.3, 0.5, n) * 0.25)  # tyres on wet road
add(SFXBUS, 6.0, noise_swell(0.8, 150, 1200, 0.35, "bell"))  # puddle splash (slow-mo)
sfx("whoosh", 7.72, 0.9, pan=-0.5)
# S2 8-15: taiko drive 92 bpm
beat = 60 / 92
for i, b in enumerate(np.arange(8.0, 14.6, beat)):
    add(music, b, taiko(0.4 + 0.3 * (b - 8) / 6.6))
    if i % 2 == 1:
        add(music, b + beat / 2, metal(0.12), 1.0, 0.4 if i % 4 == 1 else -0.4)
    if b > 11.5:
        add(music, b + beat / 2, taiko(0.35))
add(music, 8.0, pad([hz(50), hz(53), hz(57)], 6.6, 600, 2.0, 0.4), 0.25)
for tt in (9.5, 10.0, 10.5, 11.0, 11.5):
    add(SFXBUS, tt, kick(0.45, 110, 45, 0.25))
add(SFXBUS, 9.5, noise_swell(0.3, 200, 3000, 0.3, "bell"))  # door
add(SFXBUS, 10.05, noise_swell(0.5, 120, 900, 0.4, "bell"))  # boot splash
add(SFXBUS, 10.5, noise_swell(0.25, 1500, 7000, 0.35, "up"))  # zip
add(SFXBUS, 11.0, noise_swell(0.4, 200, 1500, 0.3, "bell"))  # rope
for b in np.arange(12.0, 14.6, 0.42):
    add(SFXBUS, b, kick(0.18, 70, 35, 0.2), 1.0, 0.1)  # footsteps
add(SFXBUS, 8.0, noise_swell(6.6, 80, 700, 0.18, "bell"))  # fire roar
# freeze 14.6: music stops, breath through mask
add(SFXBUS, 14.6, noise_swell(0.4, 300, 2000, 0.3, "bell"))
add(SFXBUS, 14.6, tone(55, 0.6, 0.3, 4))

# ------------------------------------------------------------- S3 (15-23): questions
for i, tt in enumerate((15.0, 16.2, 17.4, 18.6, 19.8)):
    sfx("impact-bass-2", tt, 0.2, length=1.0)
    add(SFXBUS, tt + 0.05, bandpass(rng.standard_normal(int(0.25 * SR)), 300, 3000) * 0.12, 1.0, -0.4 + i * 0.2)
# accelerating clock tick
tt = 15.0
gap = 0.5
while tt < 22.0:
    add(music, tt, hat(0.35, 0.03), 1.0, 0.3)
    tt += gap
    gap = max(0.09, gap * 0.94)
n = int(7.0 * SR)
t = t_arr(n)
cluster = pad([hz(62), hz(63), hz(65.5), hz(68)], 7.0, 1400, 2.5, 0.2, 0.01)
add(music, 15.0, cluster, 0.12)
add(music, 15.0, drone[: int(7 * SR)] * np.linspace(0.6, 1.0, int(7 * SR)), 0.14)
sfx("glitch-1", 21.75, 0.4, length=0.25)
sfx("impact-bass-1", 21.9, 0.45, length=1.4)

# ------------------------------------------------------------- S4 (23-30): reveal
add(SFXBUS, 23.65, tone(1046, 0.9, 0.35, 4.5))
sfx("sparkle", 23.9, 0.45, pan=0.2)
add(music, 23.3, pad([hz(50), hz(57), hz(62), hz(65)], 6.9, 1500, 2.0, 0.8), 0.32)
for i, tt in enumerate(np.arange(24.0, 30.0, 0.46875)):
    add(music, tt, pluck(hz([74, 77, 81, 77][i % 4]), 0.3, 0.12), 1.0, -0.3 if i % 2 else 0.3)
sfx("pop", 24.7, 0.35)
sfx("whoosh-cinematic", 26.4, 0.8, length=2.2)
sfx("whoosh", 29.6, 0.7)

# ------------------------------------------------------------- 30-75: 128 bpm electronic groove
B = 60 / 128
prog = [(38, [62, 65, 69]), (41, [65, 69, 72]), (46, [62, 65, 70]), (36, [60, 64, 67])]  # Dm F Bb C


def groove(t0, t1, kick_on=True, hats=True, arp=False, bassline=True, gain=1.0):
    bar = 4 * B
    for bi, bs in enumerate(np.arange(t0, t1 - 1e-6, bar)):
        root, chord = prog[bi % 4]
        if bassline:
            for k in range(8):
                st = bs + k * B / 2
                if st < t1:
                    add(music, st, bass(hz(root), B / 2 * 0.95, 0.38 * gain))
        for k in range(4):
            st = bs + k * B
            if st >= t1:
                break
            if kick_on:
                add(music, st, kick(1.0 * gain))
            if k in (1, 3):
                add(music, st, clap(0.18 * gain))
            if hats:
                add(music, st + B / 2, hat(0.22 * gain), 1.0, 0.25)
                add(music, st + B / 4, hat(0.08 * gain), 1.0, -0.25)
                add(music, st + 3 * B / 4, hat(0.08 * gain), 1.0, -0.25)
        if arp:
            notes = chord + [chord[0] + 12]
            for k in range(16):
                st = bs + k * B / 4
                if st < t1:
                    add(music, st, pluck(hz(notes[k % 4] + 12), 0.2, 0.07 * gain), 1.0, 0.35 if k % 2 else -0.35)


groove(30.0, 37.0, arp=False)
groove(37.0, 51.0, arp=True)
groove(51.0, 57.0, kick_on=True, hats=False, arp=False, gain=0.55)
groove(57.0, 63.0, arp=True, gain=0.9)
add(music, 30.0, pad([hz(50), hz(57), hz(62), hz(65)], 21.0, 1100, 1.0, 1.0), 0.16)
add(music, 51.0, pad([hz(50), hz(57), hz(62)], 12.0, 900, 1.0, 1.0), 0.14)
# chaos side of the split screen: detuned piano-ish stabs growing
for i, tt in enumerate(np.arange(57.4, 61.0, 0.42)):
    add(SFXBUS, tt, pluck(hz(60 + (i * 5) % 11) * 1.013, 0.4, 0.08 + 0.02 * i), 1.0, -0.6)
# 63-68 breathing pad
add(music, 63.0, pad([hz(50), hz(57), hz(62), hz(69)], 5.4, 1800, 0.6, 1.2), 0.42)
# 68-75 orchestral build
add(music, 68.0, pad([hz(38), hz(50), hz(57), hz(62), hz(65), hz(69)], 7.2, 2200, 2.5, 0.2, 0.006), 0.42)
for b in np.arange(68.0, 72.0, 60 / 92):
    add(music, b, taiko(0.5))
sfx("riser", 64.6, 0.55)
for tt in (72.0, 72.4, 72.8, 73.2, 73.6, 74.0):
    add(music, tt, taiko(0.8))
    add(music, tt, kick(0.7))

# app sounds 30-68
for tt in (30.25, 34.55, 35.55, 54.3, 55.25, 63.5):
    sfx("click", tt, 0.8)
sfx("typing", 31.2, 0.4, length=0.8)
sfx("typing", 33.55, 0.4, length=0.6)
add(SFXBUS, 32.25, noise_swell(0.4, 1500, 8000, 0.25, "bell"))  # gauge morph swish
sfx("impact-bass-1", 35.55, 0.75, length=1.2)
sfx("whoosh", 36.72, 0.7)
for i in range(5):
    add(SFXBUS, 37.35 + i * 0.62, tone(1568, 0.15, 0.10, 30), 1.0, -0.5 if i < 2 else 0.5)
sfx("whoosh-short", 41.5, 0.6)
sfx("whoosh", 43.0, 0.6, pan=0.5)
sfx("key-press", 43.4, 0.6)
sfx("key-press", 43.6, 0.6)
sfx("click", 43.75, 0.8)
for i in range(6):
    add(SFXBUS, 43.4 + i * 0.82, tone(1318, 0.2, 0.10, 20), 1.0, -0.4)
for tt in (45.0, 46.22, 47.15):
    add(SFXBUS, tt, kick(0.4, 140, 50, 0.2))
add(SFXBUS, 48.8, noise_swell(1.2, 500, 6000, 0.25, "up"))  # timelapse
for k in range(2):  # the app's own warn beep (660 Hz)
    add(SFXBUS, 50.0 + k * 0.28, tone(660, 0.2, 0.25, 8))
sfx("notification", 50.05, 0.5, length=1.2)
sfx("whoosh", 50.72, 0.7)
for tt in (51.8, 54.3):  # radio squelch + static under the radio lines
    add(SFXBUS, tt, bandpass(rng.standard_normal(int(0.9 * SR)), 300, 3000) * np.linspace(0.12, 0.05, int(0.9 * SR)), 1.0, -0.4)
    add(SFXBUS, tt + 0.9, tone(1800, 0.05, 0.1, 60), 1.0, -0.4)
for i in range(6):
    add(SFXBUS, 56.0 + i * 0.15, tone(988, 0.12, 0.10, 30), 1.0, -0.3 + i * 0.12)
sfx("whoosh-cinematic", 60.8, 0.55, length=1.3)
sfx("whoosh", 63.75, 0.5)
for i in range(6):
    add(SFXBUS, 64.6 + i * 0.08, hat(0.15, 0.03))
sfx("whoosh", 67.55, 0.6)
for tt in (72.0, 72.4, 72.8, 73.2, 73.6, 74.0):
    sfx("impact-bass-2", tt, 0.35, length=0.4)

# ------------------------------------------------------------- 75-84: final words + end card
for tt, ch in ((75.2, [50, 57, 62, 65]), (76.8, [46, 53, 58, 62]), (78.4, [48, 55, 60, 64])):
    sfx("impact-bass-1", tt - 0.05, 0.3, length=1.6)
    add(music, tt - 0.05, pad([hz(c) for c in ch] + [hz(ch[0] - 12)], 1.55, 2600, 0.01, 0.4, 0.006), 0.25)
    add(music, tt - 0.05, taiko(0.35))
add(music, 78.4, pad([hz(38), hz(50), hz(57), hz(62), hz(66)], 1.6, 3000, 0.01, 0.3, 0.006), 0.15)
# hard stop at 80.0 handled by the music gate below
n = int(3.5 * SR)
t = t_arr(n)
swell = np.sin(2 * np.pi * hz(26) * t) * np.minimum(1, t / 1.5) * np.exp(-t * 0.5)
add(SFXBUS, 80.5, swell, 0.35)
add(SFXBUS, 80.5, tone(1046, 1.2, 0.18, 3))
sfx("sparkle", 80.9, 0.35)
add(SFXBUS, 85.4, noise_swell(1.2, 300, 2000, 0.18, "bell"))  # final breath

# ------------------------------------------------------------- music gates (silences)
gate = np.ones(N)
for a, b in ((14.6, 15.0), (22.35, 23.25), (80.0, 87.0)):
    ia, ib = int(a * SR), int(b * SR)
    fa = int(0.02 * SR)
    gate[ia - fa:ia] = np.minimum(gate[ia - fa:ia], np.linspace(1, 0, fa))
    gate[ia:ib] = 0
# ------------------------------------------------------------- voice-over (ElevenLabs takes in assets/vo)
# (file, global start of the file, segment start, segment end, tempo)
VO = [
    ("vo-01", 10.96, None, None, 1.0), ("vo-02", 13.6, None, None, 1.0), ("vo-03", 15.4, None, None, 1.0),
    ("vo-04", 21.9, None, None, 1.0), ("vo-05", 24.4, None, None, 1.0), ("vo-06", 28.8, None, None, 1.0),
    ("vo-07", 31.5, None, None, 1.0), ("vo-08", 32.4, None, None, 1.0), ("vo-09", 34.48, None, None, 1.0),
    ("vo-10", 35.9, None, None, 1.0), ("vo-11", 38.2, None, None, 1.0), ("vo-12", 43.1, None, None, 1.0),
    ("vo-13", 45.0, None, None, 1.0), ("vo-14", 48.05, None, None, 1.1), ("vo-15a", 55.3, None, None, 1.0),
    ("funk-2", 51.85, None, None, 1.0), ("funk-3", 54.35, None, None, 1.0), ("vo-16", 58.0, None, None, 1.0), ("vo-17", 63.7, None, None, 1.0),
    ("vo-18", 70.72, None, None, 1.0),
    ("vo-19", 75.13, 0.0, 1.1, 1.0), ("vo-19", 76.77, 1.2, 2.45, 1.0), ("vo-19", 78.36, 2.55, 4.75, 1.0),
    ("vo-20", 80.76, None, None, 1.0),
]
VO.append(("funk-1", 0.05, None, None, 1.0))
VO_TARGET = -16.0


def measure_lufs(path):
    out = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    vals = [ln.split()[1] for ln in out.splitlines() if ln.strip().startswith("I:")]
    return float(vals[-1]) if vals else -20.0


vo_bus = [np.zeros(N), np.zeros(N)]
for name, start, a, b, tempo in VO:
    path = os.path.join(ROOT, "assets", "vo", name + ".mp3")
    gain_db = VO_TARGET - measure_lufs(path) + (6.0 if name.startswith("funk") else 0.0)
    chain = "highpass=f=85,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=1"
    if name.startswith("funk"):
        chain = "highpass=f=300,lowpass=f=3000,acrusher=bits=10:mix=0.25,acompressor=threshold=-25dB:ratio=6"
    if tempo != 1.0:
        chain += f",atempo={tempo}"
    chain += f",volume={gain_db:.2f}dB"
    cmd = ["ffmpeg", "-v", "error"]
    if a is not None:
        cmd += ["-ss", str(a), "-t", str(b - a)]
    cmd += ["-i", path, "-af", chain, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    v = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    fade = min(len(v), int(0.012 * SR))
    v[:fade] *= np.linspace(0, 1, fade)
    v[-fade:] *= np.linspace(1, 0, fade)
    if name.startswith("funk"):
        v = v * 0.7 + bandpass(rng.standard_normal(len(v)), 300, 3000) * 0.02
    add(vo_bus, start, v, 1.0)

# sidechain ducking: music down ~8 dB, sound design down ~4 dB while the voice speaks
env = np.abs(vo_bus[0]) + np.abs(vo_bus[1])
k = int(0.03 * SR)
env = np.convolve(env, np.ones(k) / k, mode="same")
env = np.minimum(1.0, env / (np.percentile(env[env > 1e-4], 60) + 1e-9))
rel = np.exp(-1 / (0.35 * SR))
duck = np.empty(N)
acc = 0.0
for i in range(0, N, 64):  # attack instantly, release over ~350 ms (block-wise for speed)
    target = env[i:i + 64].max()
    acc = target if target > acc else acc * rel ** 64
    duck[i:i + 64] = acc
L *= 1 - 0.75 * duck
R *= 1 - 0.75 * duck
L += music[0] * gate * (1 - 0.82 * duck)
R += music[1] * gate * (1 - 0.82 * duck)
L += vo_bus[0] * 3.2
R += vo_bus[1] * 3.2

# ------------------------------------------------------------- master
mix = np.stack([L, R], axis=1)
mix /= max(1e-9, np.max(np.abs(mix)))
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix *= 0.89 / max(1e-9, np.max(np.abs(mix)))
os.makedirs(os.path.join(ROOT, "assets", "audio"), exist_ok=True)
raw = os.path.join(ROOT, "assets", "audio", "_mix.f32")
mix.astype(np.float32).tofile(raw)
out = os.path.join(ROOT, "assets", "audio", "soundtrack.mp3")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw,
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), "-b:a", "256k", out], check=True)
os.remove(raw)
print("wrote", out)
