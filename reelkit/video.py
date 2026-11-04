"""Turn the poster into a Reel (MP4): the whole poster, full 9:16, intro animation, background music.
Copied from InstagramFacebookAutomation/src/video_builder.py."""
import subprocess
from pathlib import Path



def _run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{result.stderr[-3000:]}")


def media_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def pick_music(mood: str = "") -> Path | None:
    """A track from assets/music that suits the news mood (see src/music.py)."""
    from .music import pick_track
    return pick_track(mood)


# Reel length by news mood (seconds): longer for posts with more to read
# short reels are watched to the end and loop, which Instagram rewards most
MOOD_SECONDS = {"breaking": 9, "money": 10, "info": 11, "happy": 9}


def reel_seconds(mood: str, n_points: int = 0) -> float:
    """Length of the reel: longer when there is more to read."""
    return MOOD_SECONDS.get(mood, 10) + (2 if n_points > 4 else 0)


def build_video(image: Path, vcfg: dict, out_path: Path, music: Path | None = None,
                intro_dir: Path | None = None, seconds: float | None = None) -> Path:
    """Reel from the card image; with intro_dir, the animated intro frames play first. The poster fills the
    whole 9:16 frame as it is: no zoom, no pan, no borders (an image of another shape is cropped to fill)."""
    seconds, fps = float(seconds or vcfg["seconds"]), int(vcfg["fps"])
    intro_frames = sorted(intro_dir.glob("f*.jpg")) if intro_dir else []
    video_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p"
    args = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(image)]

    video_inputs = 1
    if intro_frames:
        # intro frames first, then the finished card, joined into one stream
        args += ["-framerate", str(fps), "-i", str(intro_dir / "f%04d.jpg")]
        video_inputs = 2
        video_filter = f"{video_filter}[z];[1:v]scale=1080:1920,format=yuv420p,setsar=1[i];[i][z]concat=n=2:v=1:a=0"
    audio_in = video_inputs

    if music:
        # the strongest stretch from the middle of the song (chorus / drop), not its intro
        from .music import best_start
        start = best_start(music, seconds)
        print(f"   Music from {int(start // 60)}:{start % 60:04.1f}")
        args += ["-ss", f"{start:.2f}", "-i", str(music)]
        audio_filter = (
            f"[{audio_in}:a]volume={vcfg['music_volume']},afade=t=in:d=0.5,"
            f"afade=t=out:st={seconds - 1.5:.2f}:d=1.5[a]"
        )
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        audio_filter = f"[{audio_in}:a]anull[a]"

    args += [
        "-filter_complex", f"[0:v]{video_filter},setsar=1[v];{audio_filter}",
        "-map", "[v]", "-map", "[a]", "-t", f"{seconds:.2f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-r", str(fps),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", str(out_path),
    ]
    _run(args)
    return out_path


def cover_frame(video: Path, out_path: Path) -> tuple[Path, float]:
    """The frame 2.5 s before the end (the finished poster) as the cover; returns (cover, its time in s)."""
    at = max(0.0, media_duration(video) - 2.5)
    _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "2",
          str(out_path)])
    return out_path, at
