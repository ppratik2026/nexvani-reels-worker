"""Background music for the reels: a track that suits the news mood, and its strongest part (not the intro).

The energy of each track is measured from its audio (loudness every half second), so no tagging is needed:
breaking news gets the most intense tracks, information posts the calmer ones, and the reel uses the most
energetic stretch from the middle of the song, e.g. the chorus or a drop.
"""
import array
import random
import subprocess
from functools import cache
from pathlib import Path

from .paths import ASSETS

MUSIC_DIR = ASSETS / "music"
STEP = 0.5          # seconds per energy value
RATE = 8000         # decode rate: plenty to measure loudness

# which part of the energy ranking suits each mood (0 = calmest track, 1 = most intense)
MOOD_RANGE = {"breaking": (0.5, 1.0), "money": (0.3, 1.0), "happy": (0.3, 1.0), "info": (0.0, 0.7)}


def tracks() -> list[Path]:
    return sorted(p for p in MUSIC_DIR.glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".aac"))


@cache
def energy(track: Path) -> tuple[float, ...]:
    """Loudness (RMS) of every STEP seconds of the track."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(track), "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"],
        capture_output=True, check=True,
    ).stdout
    samples = array.array("h", raw[: len(raw) // 2 * 2])
    size = int(RATE * STEP)
    out = []
    for i in range(0, len(samples) - size + 1, size):
        chunk = samples[i:i + size]
        out.append((sum(s * s for s in chunk[::4]) / (size // 4)) ** 0.5)   # every 4th sample is enough
    return tuple(out)


def pick_track(mood: str = "") -> Path | None:
    """A random track among those whose overall intensity suits the mood."""
    found = tracks()
    if len(found) <= 1:
        return found[0] if found else None
    ranked = sorted(found, key=lambda t: _intensity(energy(t)))
    low, high = MOOD_RANGE.get(mood, (0.0, 1.0))
    n = len(ranked)
    suitable = ranked[int(low * n):max(int(low * n) + 1, round(high * n))]
    return random.choice(suitable)


def _intensity(values: tuple[float, ...]) -> float:
    """Loud and punchy tracks score high: average loudness plus how much it moves."""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    swing = sum(abs(b - a) for a, b in zip(values, values[1:])) / max(1, len(values) - 1)
    return mean + 2 * swing


def best_start(track: Path, seconds: float) -> float:
    """Start time (s) of the strongest `seconds`-long stretch in the middle of the track (15%-90%),
    nudged to begin just where the energy rises, so the reel opens on the build-up into it."""
    values = energy(track)
    window = max(1, int(seconds / STEP))
    if len(values) <= window + 4:
        return 0.0
    first, last = int(len(values) * 0.15), int(len(values) * 0.9) - window
    if last <= first:
        return 0.0
    best, best_score = first, -1.0
    total = sum(values[first:first + window])
    for i in range(first, last + 1):
        if i > first:
            total += values[i + window - 1] - values[i - 1]
        before = values[max(0, i - 4):i]
        rise = (sum(values[i:i + 4]) / 4) - (sum(before) / len(before) if before else 0)
        score = total / window + 0.5 * max(0.0, rise)
        if score > best_score:
            best, best_score = i, score
    return round(max(0.0, best * STEP - 1.0), 2)   # a second of run-up before the strong part
