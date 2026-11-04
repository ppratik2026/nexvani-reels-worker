"""One story -> one reel: drawn scene, brand poster with intro animation, music for the mood, MP4 and cover."""
from datetime import datetime
from pathlib import Path

from . import brand
from .music import pick_track
from .paths import require_tool
from .render import render_brand
from .scenes import BY_CATEGORY, draw_scene
from .story import Story
from .text import mood_of
from .video import build_video, cover_frame, reel_seconds

# The original page's 29 row styles, used one after another (card.row_styles in its config.yaml).
ROW_STYLES = ["cols", "split", "neon", "circles", "strips", "tv", "notes", "capsules", "stats", "keys", "bento",
              "aurora", "hub", "stairs", "arrows", "paper", "magazine", "road", "rope", "puzzle", "train",
              "calendar", "film", "clipboard", "tvs", "balloons", "station", "detective", "stamps"]

VIDEO = {"fps": 30, "intro_seconds": 3.4, "music_volume": 0.9, "seconds": 10}


def next_row_style(last: str | None, styles: list[str] | None = None) -> str:
    styles = styles or ROW_STYLES
    return styles[(styles.index(last) + 1) % len(styles)] if last in styles else styles[0]


def make_reel(story: Story, work_dir: Path, *, handle: str, row_style: str, date: str | None = None,
              intro: bool = True) -> dict:
    """Builds work_dir/reel.mp4 and cover.jpg; returns paths and the look used (for the dashboard)."""
    require_tool("ffmpeg")
    work_dir.mkdir(parents=True, exist_ok=True)
    date = date or datetime.now().strftime("%-d %B %Y")

    scene = story.scene if story.scene else BY_CATEGORY.get(story.category, "city")
    scene_png = draw_scene(scene, story.props, work_dir / "scene.png")
    from .render import WIDTH  # noqa: F401  (render size is fixed at 1080x1920)
    import base64
    scene_url = "data:image/png;base64," + base64.b64encode(scene_png.read_bytes()).decode()

    intro_dir = work_dir / "intro" if intro else None
    card = render_brand(story, work_dir / "card.png", intro_dir, date=date, handle=handle, row_style=row_style,
                        scene_url=scene_url, fps=VIDEO["fps"], intro_seconds=VIDEO["intro_seconds"])

    mood = mood_of(story)
    music = pick_track(mood)
    seconds = reel_seconds(mood, len(story.points))
    video = build_video(card, VIDEO, work_dir / "reel.mp4", music, intro_dir, seconds)
    cover, cover_at = cover_frame(video, work_dir / "cover.jpg")
    look = {"rows": row_style, "scene": scene, "mood": mood, "music": music.stem if music else "", "seconds": seconds,
            "palette": story.category, "label": brand.look_for(story)[0]}
    return {"video": video, "cover": cover, "card": card, "cover_at": cover_at, "look": look}
