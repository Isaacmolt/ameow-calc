"""Music-box 'Happy Birthday' (public domain melody) timed to film.html.

Beat = 0.5 s, melody starts at 0.5 s so each phrase lands on a scene:
  phrase 1  0.5 – 3.5   grapes pop in on each note
  phrase 2  3.5 – 6.5   macro shot
  phrase 3  6.5 – 10.0  split layout (high G at 7.0 = first character)
  phrase 4 10.0 – 13.5  hero shot, then a chime for the polaroid / logo
Usage: python3 music.py out.wav
"""
import sys, wave
import numpy as np

SR = 44100
DUR = 15.0
N = int(SR * DUR)
out = np.zeros((N, 2))

def hz(name):
    notes = {'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2, 'A': 0, 'B': 2}
    return 440 * 2 ** ((notes[name[0]] + 12 * (int(name[1]) - 4)) / 12)

def add(sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    n = min(len(sig), N - i)
    if n <= 0:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:i + n, 0] += sig[:n] * l * gain
    out[i:i + n, 1] += sig[:n] * r * gain

def musicbox(f, length=2.6, decay=2.8):
    t = np.arange(int(SR * length)) / SR
    # tine partials are slightly inharmonic — that's the music-box sparkle
    parts = [(1, 1.0), (2.0, .32), (3.01, .10), (4.2, .07), (5.4, .03)]
    s = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * decay * (1 + .6 * k)) for k, (m, a) in enumerate(parts))
    s += .05 * np.sin(2 * np.pi * f * 7.1 * t) * np.exp(-t * 40)       # click of the pin
    att = np.clip(t / .004, 0, 1)
    return s * att

def pad(freqs, length, fade=.6):
    t = np.arange(int(SR * length)) / SR
    s = sum(np.sin(2 * np.pi * f * t + .3 * np.sin(2 * np.pi * .4 * t)) +
            .25 * np.sin(2 * np.pi * f * 2.002 * t) for f in freqs) / len(freqs)
    env = np.minimum(1, t / fade) * np.minimum(1, (length - t) / fade)
    return s * env

# ---- melody ----
melody = [
    ('G4', .75), ('G4', .25), ('A4', 1), ('G4', 1), ('C5', 1), ('B4', 2),
    ('G4', .75), ('G4', .25), ('A4', 1), ('G4', 1), ('D5', 1), ('C5', 2),
    ('G4', .75), ('G4', .25), ('G5', 1), ('E5', 1), ('C5', 1), ('B4', 1), ('A4', 2),
    ('F5', .75), ('F5', .25), ('E5', 1), ('C5', 1), ('D5', 1), ('C5', 3),
]
BEAT, t = .5, .5
rng = np.random.default_rng(3)
for i, (n, d) in enumerate(melody):
    human = rng.normal(0, .006)                      # tiny timing drift, like a real box
    add(musicbox(hz(n), length=max(2.2, d * BEAT + 1.8)), t + human, pan=rng.uniform(-.25, .25), gain=.34)
    add(musicbox(hz(n) * 2, length=1.2, decay=5), t + human + .002, pan=.4, gain=.05)  # octave shimmer
    t += d * BEAT

# ---- soft harmony underneath ----
chords = [(1.0, 1.5, ['C3', 'E3', 'G3']), (2.5, 1.5, ['G2', 'D3', 'B3']), (4.0, 1.5, ['G2', 'B2', 'F3']),
          (5.5, 1.5, ['C3', 'E3', 'G3']), (7.0, 1.5, ['C3', 'E3', 'G3']), (8.5, 1.5, ['F2', 'C3', 'A3']),
          (10.0, 1.0, ['F2', 'A2', 'C3']), (10.5, 1.0, ['C3', 'E3', 'G3']), (11.5, .5, ['G2', 'B2', 'D3']),
          (12.0, 3.0, ['C3', 'G3', 'E4'])]
for t0, d, ns in chords:
    add(pad([hz(n) for n in ns], d + .7), t0 - .1, gain=.07)

# ---- low music-box bass on downbeats ----
for t0, n in [(1.0, 'C3'), (2.5, 'G2'), (4.0, 'G2'), (5.5, 'C3'), (7.0, 'C3'), (8.5, 'F2'), (10.5, 'C3'), (11.5, 'G2'), (12.0, 'C3')]:
    add(musicbox(hz(n), 2.5, 2.0), t0, gain=.16)

# ---- transition swells (filtered noise) ----
def swell(t0, length, peak=.6):
    n = int(SR * length)
    x = rng.normal(0, 1, n)
    k = 400                                            # moving-average low-pass
    x = np.convolve(x, np.ones(k) / k, mode='same') * 12
    tt = np.linspace(0, 1, n)
    env = np.sin(np.pi * np.clip(tt / peak, 0, 1) / 2) ** 2 * np.clip((1 - tt) / (1 - peak), 0, 1)
    add(x * env, t0, gain=.05)
for t0, l in [(2.7, .9), (5.6, 1.2), (9.3, 1.0), (12.8, 1.1)]:
    swell(t0, l)

# ---- polaroid chime ----
for i, n in enumerate(['C6', 'E6', 'G6', 'C7']):
    add(musicbox(hz(n), 2.0, 3.2), 13.95 + i * .075, pan=-.4 + i * .27, gain=.11)

# ---- reverb: convolve with a decaying stereo noise tail ----
ir_len = int(SR * 2.2)
tt = np.arange(ir_len) / SR
wet = np.zeros_like(out)
for ch in range(2):
    ir = rng.normal(0, 1, ir_len) * np.exp(-tt / .55)
    ir[:int(.012 * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    L = N + ir_len
    F = 1 << (L - 1).bit_length()
    wet[:, ch] = np.fft.irfft(np.fft.rfft(out[:, ch], F) * np.fft.rfft(ir, F), F)[:N]
mix = out * .78 + wet * .42

# fades + normalise
fi, fo = int(.02 * SR), int(.9 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
mix /= np.max(np.abs(mix)) / .89

with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
