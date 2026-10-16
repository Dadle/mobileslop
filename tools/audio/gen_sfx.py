#!/usr/bin/env python3
"""Procedurally generates all sound effects + a music loop for Lane Rush as 16-bit WAV.
Run: python3 tools/audio/gen_sfx.py  (writes to assets/audio/)"""
import os, sys, math
import numpy as np
import wave

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "audio")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

def t(dur):
    return np.arange(int(SR * dur)) / SR

def env(n, a=0.005, d=0.1, s=0.0, r=0.05, hold=0.0):
    """ADSR envelope with n samples."""
    a_n, d_n, r_n, h_n = int(a * SR), int(d * SR), int(r * SR), int(hold * SR)
    s_n = max(0, n - a_n - d_n - r_n - h_n)
    e = np.concatenate([
        np.linspace(0, 1, a_n, endpoint=False),
        np.ones(h_n),
        np.linspace(1, s, d_n, endpoint=False),
        np.full(s_n, s),
        np.linspace(s, 0, r_n),
    ])
    if len(e) < n:
        e = np.concatenate([e, np.zeros(n - len(e))])
    return e[:n]

def lowpass(x, cutoff, order=2):
    # simple one-pole IIR applied `order` times
    rc = 1.0 / (2 * math.pi * cutoff)
    dt = 1.0 / SR
    alpha = dt / (rc + dt)
    y = x.copy()
    for _ in range(order):
        out = np.empty_like(y)
        acc = 0.0
        for i in range(len(y)):
            acc += alpha * (y[i] - acc)
            out[i] = acc
        y = out
    return y

def lowpass_fast(x, cutoff):
    # FFT-based brickwall-ish lowpass (cheap for long signals)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1.0 / (1.0 + (f / cutoff) ** 4)
    return np.fft.irfft(X, n=len(x))

def highpass_fast(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1.0 - 1.0 / (1.0 + (f / max(cutoff, 1)) ** 4)
    return np.fft.irfft(X, n=len(x))

def noise(dur):
    return rng.uniform(-1, 1, int(SR * dur))

def sine(freq, dur, phase=0.0):
    return np.sin(2 * math.pi * freq * t(dur) + phase)

def sweep(f0, f1, dur, curve=1.0):
    tt = t(dur)
    k = (tt / dur) ** curve
    f = f0 + (f1 - f0) * k
    ph = 2 * math.pi * np.cumsum(f) / SR
    return np.sin(ph)

def square(freq, dur, duty=0.5):
    return np.where((t(dur) * freq) % 1.0 < duty, 1.0, -1.0)

def saw(freq, dur):
    return 2.0 * ((t(dur) * freq) % 1.0) - 1.0

def normalize(x, peak=0.9):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak

def soft_clip(x, drive=1.5):
    return np.tanh(x * drive) / math.tanh(drive)

def write(name, x, peak=0.9):
    x = normalize(x, peak)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", path, f"{len(x)/SR:.2f}s")

def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += p
    return out

def add_at(out, start, s):
    end = min(len(out), start + len(s))
    if end > start:
        out[start:end] += s[: end - start]

def pad(x, dur):
    n = int(SR * dur)
    return np.concatenate([x, np.zeros(max(0, n - len(x)))])[:n]

# ---------------------------------------------------------------- SFX
def gunshot():
    dur = 0.22
    n = int(SR * dur)
    crack = noise(dur) * env(n, a=0.0005, d=0.03, s=0.0, r=0.01)
    body = lowpass_fast(noise(dur), 900) * env(n, a=0.001, d=0.12, s=0.1, r=0.06) * 2.0
    thump = sweep(180, 50, dur) * env(n, a=0.001, d=0.08, s=0.0, r=0.05) * 1.3
    return soft_clip(mix(crack, body, thump), 2.5)

def gunshot_heavy():
    dur = 0.3
    n = int(SR * dur)
    crack = noise(dur) * env(n, a=0.0005, d=0.04, s=0.0, r=0.02)
    body = lowpass_fast(noise(dur), 600) * env(n, a=0.001, d=0.18, s=0.1, r=0.08) * 2.5
    thump = sweep(120, 40, dur) * env(n, a=0.001, d=0.12, s=0.0, r=0.08) * 1.8
    return soft_clip(mix(crack, body, thump), 3.0)

def zombie_hit():
    dur = 0.18
    n = int(SR * dur)
    squish = lowpass_fast(noise(dur), 1500) * env(n, a=0.002, d=0.08, s=0.0, r=0.05)
    tone = sweep(300, 90, dur) * env(n, a=0.002, d=0.1, s=0, r=0.03) * 0.6
    return soft_clip(mix(squish, tone), 2.0)

def zombie_die():
    dur = 0.75
    n = int(SR * dur)
    tt = t(dur)
    f = 140 + 25 * np.sin(2 * math.pi * 9 * tt) - 60 * tt
    ph = 2 * math.pi * np.cumsum(f) / SR
    growl = (np.sin(ph) + 0.5 * np.sin(2 * ph + 0.3) + 0.3 * np.sin(3.01 * ph)) * env(n, a=0.02, d=0.3, s=0.5, r=0.3)
    breath = lowpass_fast(noise(dur), 1200) * env(n, a=0.01, d=0.4, s=0.3, r=0.3) * 0.6
    splat = lowpass_fast(noise(dur), 700) * env(n, a=0.001, d=0.1, s=0, r=0.05) * 1.2
    return soft_clip(mix(growl, breath, splat), 2.0)

def zombie_groan(seed):
    r = np.random.default_rng(seed)
    dur = 1.2
    n = int(SR * dur)
    tt = t(dur)
    base = 90 + r.uniform(-15, 25)
    f = base + 12 * np.sin(2 * math.pi * (5 + r.uniform(0, 3)) * tt) + 30 * np.sin(2 * math.pi * 0.6 * tt)
    ph = 2 * math.pi * np.cumsum(f) / SR
    v = np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.35 * np.sin(3 * ph) + 0.2 * np.sin(4 * ph)
    v = lowpass_fast(v, 900) * env(n, a=0.15, d=0.4, s=0.6, r=0.4)
    breath = lowpass_fast(noise(dur), 800) * env(n, a=0.2, d=0.5, s=0.4, r=0.4) * 0.35
    return soft_clip(mix(v, breath), 1.5)

def brute_roar():
    dur = 1.4
    n = int(SR * dur)
    tt = t(dur)
    f = 60 + 10 * np.sin(2 * math.pi * 7 * tt) + 20 * np.sin(2 * math.pi * 0.8 * tt)
    ph = 2 * math.pi * np.cumsum(f) / SR
    v = np.sin(ph) + 0.8 * np.sin(2 * ph) + 0.5 * np.sin(3 * ph) + 0.3 * np.sin(5 * ph)
    v = lowpass_fast(v, 700) * env(n, a=0.08, d=0.5, s=0.7, r=0.5)
    gr = lowpass_fast(noise(dur), 500) * env(n, a=0.05, d=0.6, s=0.5, r=0.5) * 0.7
    return soft_clip(mix(v, gr), 2.5)

def crate_hit():
    dur = 0.12
    n = int(SR * dur)
    knock = sweep(420, 180, dur) * env(n, a=0.001, d=0.05, s=0.0, r=0.03)
    wood = highpass_fast(lowpass_fast(noise(dur), 3500), 500) * env(n, a=0.0005, d=0.03, s=0, r=0.02) * 0.8
    return soft_clip(mix(knock, wood), 1.5)

def crate_break():
    dur = 0.5
    n = int(SR * dur)
    crunch = lowpass_fast(noise(dur), 2500) * env(n, a=0.001, d=0.2, s=0.15, r=0.2)
    # several wood knocks
    out = crunch
    for i, dly in enumerate([0.0, 0.04, 0.09, 0.15, 0.22]):
        k = sweep(380 - i * 40, 150, 0.1) * env(int(SR * 0.1), a=0.001, d=0.05, s=0, r=0.03)
        out = mix(out, pad(np.concatenate([np.zeros(int(SR * dly)), k]), dur) * 0.8)
    thump = sweep(150, 50, dur) * env(n, a=0.001, d=0.15, s=0, r=0.1)
    return soft_clip(mix(out, thump), 2.0)

def powerup():
    notes = [523.25, 659.25, 783.99, 1046.5, 1318.5]
    step = 0.07
    dur = step * len(notes) + 0.45
    out = np.zeros(int(SR * dur))
    for i, f in enumerate(notes):
        seg = 0.4
        s = (sine(f, seg) + 0.4 * sine(f * 2, seg) + 0.2 * square(f, seg) * 0.3) * env(int(SR * seg), a=0.004, d=0.25, s=0.1, r=0.1)
        start = int(SR * step * i)
        add_at(out, start, s * (0.7 + 0.1 * i))
    shimmer = highpass_fast(noise(dur), 6000) * env(len(out), a=0.1, d=0.3, s=0, r=0.2) * 0.15
    return soft_clip(mix(out, shimmer), 1.3)

def heal():
    notes = [392.0, 523.25, 659.25, 783.99]
    out = np.zeros(int(SR * 0.9))
    for i, f in enumerate(notes):
        seg = 0.5
        s = (sine(f, seg) + 0.3 * sine(f * 3, seg)) * env(int(SR * seg), a=0.01, d=0.3, s=0.2, r=0.15)
        start = int(SR * 0.09 * i)
        add_at(out, start, s)
    return soft_clip(out, 1.2)

def shield_on():
    dur = 0.6
    n = int(SR * dur)
    s = sweep(200, 900, dur, curve=0.5) * env(n, a=0.01, d=0.3, s=0.3, r=0.2)
    s2 = sweep(400, 1800, dur, curve=0.5) * env(n, a=0.01, d=0.3, s=0.3, r=0.2) * 0.4
    return soft_clip(mix(s, s2), 1.3)

def nuke():
    dur = 1.3
    n = int(SR * dur)
    boom = lowpass_fast(noise(dur), 350) * env(n, a=0.002, d=0.6, s=0.3, r=0.5) * 2.5
    sub = sweep(90, 30, dur) * env(n, a=0.002, d=0.5, s=0.2, r=0.4) * 1.5
    crack = noise(0.1) * env(int(SR * 0.1), a=0.0005, d=0.05, s=0, r=0.03)
    return soft_clip(mix(boom, sub, pad(crack, dur)), 3.0)

def player_hurt():
    dur = 0.4
    n = int(SR * dur)
    thud = sweep(160, 50, dur) * env(n, a=0.001, d=0.15, s=0, r=0.1) * 1.5
    bite = lowpass_fast(noise(dur), 1800) * env(n, a=0.001, d=0.08, s=0.1, r=0.1)
    tone = square(110, dur, 0.3) * env(n, a=0.001, d=0.2, s=0, r=0.1) * 0.25
    return soft_clip(mix(thud, bite, tone), 2.0)

def game_over():
    notes = [392.0, 349.23, 311.13, 261.63, 196.0]
    out = np.zeros(int(SR * 2.4))
    for i, f in enumerate(notes):
        seg = 0.8 if i < len(notes) - 1 else 1.4
        s = (saw(f, seg) * 0.5 + sine(f, seg)) * env(int(SR * seg), a=0.01, d=0.5, s=0.4, r=0.3)
        s = lowpass_fast(s, 1800)
        start = int(SR * 0.28 * i)
        add_at(out, start, s)
    return soft_clip(out, 1.5)

def ui_click():
    dur = 0.08
    n = int(SR * dur)
    return sine(1200, dur) * env(n, a=0.001, d=0.04, s=0, r=0.03)

def footstep(seed):
    r = np.random.default_rng(seed)
    dur = 0.09
    n = int(SR * dur)
    s = lowpass_fast(noise(dur), 900 + r.uniform(-200, 200)) * env(n, a=0.001, d=0.05, s=0, r=0.03)
    return soft_clip(s, 1.3)

def tap_start():
    notes = [523.25, 783.99]
    out = np.zeros(int(SR * 0.5))
    for i, f in enumerate(notes):
        seg = 0.3
        s = sine(f, seg) * env(int(SR * seg), a=0.005, d=0.2, s=0.1, r=0.1)
        start = int(SR * 0.1 * i)
        add_at(out, start, s)
    return out

def plasma():
    dur = 0.28
    n = int(SR * dur)
    body = sweep(1400, 350, dur, curve=0.6) * env(n, a=0.002, d=0.12, s=0.2, r=0.1)
    shimmer = sweep(2800, 900, dur, curve=0.5) * env(n, a=0.002, d=0.08, s=0.1, r=0.08) * 0.5
    hiss = highpass_fast(noise(dur), 3000) * env(n, a=0.001, d=0.05, s=0, r=0.05) * 0.3
    return soft_clip(mix(body, shimmer, hiss), 1.6)

def rail():
    dur = 0.4
    n = int(SR * dur)
    crack = noise(dur) * env(n, a=0.0005, d=0.02, s=0.0, r=0.01) * 1.2
    zap = sweep(3000, 200, dur, curve=0.35) * env(n, a=0.001, d=0.18, s=0.1, r=0.15)
    hum = (sine(90, dur) + 0.5 * sine(180, dur)) * env(n, a=0.005, d=0.2, s=0.3, r=0.15) * 0.8
    return soft_clip(mix(crack, zap, hum), 2.2)

def launcher():
    dur = 0.35
    n = int(SR * dur)
    thump = sweep(140, 45, dur) * env(n, a=0.001, d=0.15, s=0.1, r=0.15) * 1.6
    puff = lowpass_fast(noise(dur), 1200) * env(n, a=0.002, d=0.12, s=0.1, r=0.15)
    click = noise(0.03) * env(int(SR * 0.03), a=0.0005, d=0.02, s=0, r=0.01)
    return soft_clip(mix(thump, puff, pad(click, dur)), 2.0)

def explosion():
    dur = 0.9
    n = int(SR * dur)
    boom = lowpass_fast(noise(dur), 450) * env(n, a=0.002, d=0.35, s=0.25, r=0.4) * 2.2
    sub = sweep(110, 35, dur) * env(n, a=0.002, d=0.3, s=0.2, r=0.35) * 1.4
    crack = noise(0.08) * env(int(SR * 0.08), a=0.0005, d=0.04, s=0, r=0.03) * 0.9
    debris = highpass_fast(noise(dur), 2500) * env(n, a=0.05, d=0.3, s=0.1, r=0.3) * 0.25
    return soft_clip(mix(boom, sub, pad(crack, dur), debris), 2.8)

def boss_alarm():
    out = np.zeros(int(SR * 1.6))
    for i in range(3):
        seg = 0.4
        s = (square(220, seg, 0.5) * 0.4 + saw(110, seg) * 0.5) * env(int(SR * seg), a=0.01, d=0.2, s=0.5, r=0.1)
        s = lowpass_fast(s, 1500)
        add_at(out, int(SR * 0.5 * i), s)
    return soft_clip(out, 1.5)

# ---------------------------------------------------------------- MUSIC LOOP (driving minor synth loop, 8 bars @ 128bpm)
def music():
    bpm = 128.0
    beat = 60.0 / bpm
    bars = 8
    dur = bars * 4 * beat
    n = int(SR * dur)
    out = np.zeros(n)

    # chord progression (A minor): Am - F - C - G  twice (two bars each)
    roots = [110.0, 87.31, 65.41 * 2, 98.0]  # A2, F2, C3, G2
    prog = [roots[(b // 2) % 4] for b in range(bars)]

    # bass: 8th-note pulsing saw
    for b in range(bars):
        root = prog[b]
        for e in range(8):
            start = int(SR * (b * 4 + e * 0.5) * beat)
            seg = beat * 0.45
            f = root if e % 4 != 3 else root * 1.5
            s = lowpass_fast(saw(f, seg) + 0.5 * square(f * 0.5, seg, 0.4), 600) * env(int(SR * seg), a=0.004, d=0.15, s=0.6, r=0.05)
            add_at(out, start, s * 0.45)

    # pads: soft detuned saws on chord tones
    for b in range(bars):
        root = prog[b] * 2
        seg = beat * 4
        chord = [root, root * (6 / 5 if root in (220.0, 196.0) else 5 / 4), root * 1.5]
        for f in chord:
            s = (saw(f, seg) + saw(f * 1.004, seg) + saw(f * 0.996, seg)) / 3
            s = lowpass_fast(s, 1100) * env(int(SR * seg), a=0.3, d=0.5, s=0.7, r=0.4)
            start = int(SR * b * 4 * beat)
            add_at(out, start, s * 0.14)

    # arpeggio lead (16th notes)
    arp_pat = [0, 2, 1, 2, 0, 2, 1, 3]
    for b in range(bars):
        root = prog[b] * 4
        tones = [root, root * (6 / 5 if root in (440.0, 392.0) else 5 / 4), root * 1.5, root * 2]
        for e in range(16):
            if b % 2 == 0 and e % 2 == 1:
                continue
            start = int(SR * (b * 4 + e * 0.25) * beat)
            seg = beat * 0.22
            f = tones[arp_pat[e % 8]]
            s = (square(f, seg, 0.25) * 0.5 + sine(f, seg)) * env(int(SR * seg), a=0.003, d=0.12, s=0.2, r=0.05)
            add_at(out, start, s * 0.16)

    # drums: kick on each beat, snare on 2 & 4, hats on 8ths
    kick = sweep(150, 40, 0.25) * env(int(SR * 0.25), a=0.001, d=0.12, s=0, r=0.08)
    snare = mix(highpass_fast(noise(0.2), 1500) * env(int(SR * 0.2), a=0.001, d=0.1, s=0, r=0.08), sweep(220, 150, 0.15) * env(int(SR * 0.15), a=0.001, d=0.06, s=0, r=0.05) * 0.6)
    hat = highpass_fast(noise(0.06), 7000) * env(int(SR * 0.06), a=0.001, d=0.03, s=0, r=0.02)
    for b in range(bars):
        for e in range(8):
            start = int(SR * (b * 4 + e * 0.5) * beat)
            add_at(out, start, hat * (0.35 if e % 2 == 0 else 0.22))
            if e % 2 == 0:
                add_at(out, start, kick * 1.1)
            if e in (2, 6):
                add_at(out, start, snare * 0.8)
    return soft_clip(out, 1.4)

def menu_music():
    bpm = 96.0
    beat = 60.0 / bpm
    bars = 4
    dur = bars * 4 * beat
    out = np.zeros(int(SR * dur))
    roots = [110.0, 130.81, 98.0, 87.31]
    for b in range(bars):
        root = roots[b] * 2
        seg = beat * 4
        chord = [root, root * 1.2, root * 1.5, root * 2]
        for f in chord:
            s = (saw(f, seg) + saw(f * 1.005, seg)) / 2
            s = lowpass_fast(s, 900) * env(int(SR * seg), a=0.5, d=0.6, s=0.7, r=0.6)
            start = int(SR * b * 4 * beat)
            add_at(out, start, s * 0.12)
        bass = lowpass_fast(saw(root / 2, seg), 300) * env(int(SR * seg), a=0.02, d=0.6, s=0.6, r=0.4)
        add_at(out, start, bass * 0.3)
    return soft_clip(out, 1.3)

if __name__ == "__main__":
    write("gunshot", gunshot(), 0.8)
    write("gunshot_heavy", gunshot_heavy(), 0.85)
    write("zombie_hit", zombie_hit(), 0.7)
    write("zombie_die", zombie_die(), 0.8)
    for i in range(3):
        write(f"zombie_groan_{i}", zombie_groan(100 + i), 0.6)
    write("brute_roar", brute_roar(), 0.85)
    write("crate_hit", crate_hit(), 0.7)
    write("crate_break", crate_break(), 0.8)
    write("powerup", powerup(), 0.8)
    write("heal", heal(), 0.7)
    write("shield_on", shield_on(), 0.7)
    write("nuke", nuke(), 0.9)
    write("player_hurt", player_hurt(), 0.85)
    write("game_over", game_over(), 0.8)
    write("ui_click", ui_click(), 0.6)
    write("plasma", plasma(), 0.7)
    write("rail", rail(), 0.85)
    write("launcher", launcher(), 0.85)
    write("explosion", explosion(), 0.9)
    write("boss_alarm", boss_alarm(), 0.8)
    write("tap_start", tap_start(), 0.7)
    for i in range(2):
        write(f"footstep_{i}", footstep(50 + i), 0.5)
    write("music_loop", music(), 0.85)
    write("menu_loop", menu_music(), 0.8)
