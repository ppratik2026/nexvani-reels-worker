"""Reel worker for NexVani Media (nexvanimedia.com).

Asks the website which published stories still need a reel, makes each one in the brand reel style
(InstagramFacebookAutomation), and uploads the MP4 back. The website then posts it to Instagram, Facebook,
YouTube, X and the share queue, with the story link in the first comment.

    SITE_URL=https://nexvanimedia.com REELS_SECRET=... python worker.py            # one round
    python worker.py --loop 10                                                    # every 10 minutes
    python worker.py --sample out/                                                # demo reel, no website
"""
import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import requests

from reelkit import brand
from reelkit.make import ROW_STYLES, make_reel, next_row_style
from reelkit.story import Story


def site() -> tuple[str, str]:
    url = os.environ.get("SITE_URL", "").rstrip("/")
    key = os.environ.get("REELS_SECRET", "")
    if not url or not key:
        raise SystemExit("Set SITE_URL and REELS_SECRET (the same secret as in the website's environment).")
    return url, key


def fetch_music() -> None:
    """The public worker repository has no music: the tracks come from the website (needs the same key)."""
    from reelkit.music import MUSIC_DIR
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    if any(p.suffix.lower() in (".mp3", ".m4a", ".wav", ".aac") for p in MUSIC_DIR.glob("*")):
        return
    url, key = site()
    try:
        names = requests.get(f"{url}/api/reels/music", params={"key": key}, timeout=60).json().get("tracks", [])
        for name in names:
            r = requests.get(f"{url}/api/reels/music", params={"key": key, "name": name}, timeout=120)
            r.raise_for_status()
            (MUSIC_DIR / name).write_bytes(r.content)
        print(f"Music: {len(names)} tracks from the website")
    except Exception as e:   # reels then go out without music
        print(f"Music not loaded ({e}); reels without music", file=sys.stderr)


def post(url: str, *, tries: int = 4, **kw) -> requests.Response:
    """POST to the website, trying again when it is briefly busy (502/503/504, timeout, dropped connection).
    Files must be given as bytes so they can be sent again."""
    for attempt in range(tries):
        try:
            r = requests.post(url, **kw)
            if r.status_code not in (502, 503, 504) or attempt == tries - 1:
                return r
            print(f"   Website busy ({r.status_code}), trying again")
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == tries - 1:
                raise
            print(f"   Website not reachable ({type(e).__name__}), trying again")
        time.sleep(15 * 2 ** attempt)
    raise RuntimeError("unreachable")


def photo_checker(url: str, key: str, article_id: int):
    """Asks the website (Gemini) whether a candidate photo fits the story; any failure counts as a no."""
    def check(image: bytes, mime: str) -> tuple[bool, str]:
        try:
            r = post(f"{url}/api/reels/photo-check", tries=3, params={"key": key}, data={"articleId": str(article_id)},
                     files={"image": ("photo", image, mime.split(";")[0])}, timeout=90)
            r.raise_for_status()
            j = r.json()
            return bool(j.get("ok")), j.get("reason", "")
        except Exception as e:
            return False, f"check failed: {e}"
    return check


def bare_path(poster: Path) -> Path:
    """Where the poster's text-free copy goes (render_poster), sent along as "posterBare"."""
    return poster.with_name(poster.stem + "-bare.jpg")


def poster_files(poster: Path | None) -> dict:
    if not poster:
        return {}
    files = {"poster": ("poster.jpg", poster.read_bytes(), "image/jpeg")}
    bare = bare_path(poster)
    if bare.exists():
        files["posterBare"] = ("poster-bare.jpg", bare.read_bytes(), "image/jpeg")
    return files


def make_poster(story: Story, item: dict, url: str, key: str, use_photos: bool, out_path: Path) -> tuple[Path, str]:
    """The website poster: a Gemini-approved real photo when there is one, else the drawn scene. Returns the file
    and the image credit for the website."""
    from reelkit.photos import find_photo
    from reelkit.poster import render_poster

    photo = None
    known = item.get("photo")
    if use_photos and known and known.get("url"):
        # the website already found and checked a photo when it published the story
        try:
            r = requests.get(known["url"], timeout=60)
            if r.ok and len(r.content) > 10_000:
                photo = {"bytes": r.content, "mime": r.headers.get("content-type", "image/jpeg"), "credit": known["credit"]}
                print(f"   Photo from the website: {known['credit']}")
        except requests.RequestException as e:
            print(f"   Website photo not loaded ({e}); searching")
    if use_photos and not photo:
        photo = find_photo(story.imageQueries or [], " ".join([item["title"], story.headline, story.summary]),
                           check=photo_checker(url, key, item["id"]))
    render_poster(story, out_path, photo=photo, bare_path=bare_path(out_path))
    return out_path, (f"Representative image · {photo['credit']}" if photo else "Illustration: NexVani Media")


def poster_pass(minutes: float = 6) -> int:
    """Posters first: every recent story without a picture gets its poster (a few seconds each), before the
    slower reels. Uses the photo the website already found, else the drawn scene."""
    url, key = site()
    res = requests.get(f"{url}/api/reels/queue", params={"key": key, "posters": "1", "limit": "40"}, timeout=60)
    res.raise_for_status()
    queue = res.json()
    cfg = queue.get("settings", {})
    brand.set_texts(cfg.get("texts"))
    items = queue.get("items", [])
    print(f"Posters: {len(items)} stories without a picture")
    end = time.time() + minutes * 60
    made = 0
    for item in items:
        if time.time() > end:
            print("   Poster time is up; the rest come next run")
            break
        try:
            story = Story.from_script(item["script"], item["category"]["slug"], item["category"]["name"],
                                      item.get("sourceName", ""))
            story.style["color"] = item["category"].get("color", "")
            with tempfile.TemporaryDirectory() as tmp:
                poster, credit = make_poster(story, item, url, key, bool(item.get("photo")) and cfg.get("posterPhotos", True),
                                             Path(tmp) / "poster.jpg")
                up = post(f"{url}/api/reels/upload", params={"key": key}, timeout=120,
                          data={"articleId": str(item["id"]), "posterFirst": "1", "posterCredit": credit},
                          files=poster_files(poster))
                up.raise_for_status()
            made += 1
            print(f"   Poster: {item['title']}")
        except Exception as e:   # a failed poster waits for the story's reel round
            print(f"   Poster failed ({item['title']}): {e}", file=sys.stderr)
    return made


def round_once() -> int:
    url, key = site()
    # REELS_LIMIT: how many waiting stories one round takes (the website caps it at 10).
    limit = os.environ.get("REELS_LIMIT", "3")
    res = requests.get(f"{url}/api/reels/queue", params={"key": key, "limit": limit}, timeout=60)
    res.raise_for_status()
    queue = res.json()
    cfg = queue.get("settings", {})
    brand.set_texts(cfg.get("texts"))
    styles = cfg.get("rowStyles") or ROW_STYLES
    last = cfg.get("lastRowStyle")
    items = queue.get("items", [])
    if not items:
        print("No stories waiting for a reel.")
        return 0

    made = 0
    for item in items:
        want_reel = item.get("reel", True)
        print(f"Making {'reel and poster' if want_reel else 'poster'}: {item['title']}")
        story = Story.from_script(item["script"], item["category"]["slug"], item["category"]["name"],
                                  item.get("sourceName", ""))
        story.style["color"] = item["category"].get("color", "")
        row_style = next_row_style(last, styles)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                # the website poster first; a poster failure never costs the reel
                poster, credit = None, ""
                try:
                    # only the photo the website already chose: searching and checking again here would spend
                    # the website's Gemini quota a second time
                    poster, credit = make_poster(story, item, url, key, bool(item.get("photo")) and cfg.get("posterPhotos", True),
                                                 Path(tmp) / "poster.jpg")
                except Exception as e:
                    print(f"   Poster failed: {e}", file=sys.stderr)
                poster_file = poster_files(poster)
                if not want_reel:
                    up = post(f"{url}/api/reels/upload", params={"key": key}, timeout=120,
                                       data={"articleId": str(item["id"]), "posterOnly": "1", "posterCredit": credit},
                                       files=poster_file or None)
                    up.raise_for_status()
                    made += 1
                    print("   Poster uploaded")
                    continue
                out = make_reel(story, Path(tmp), handle=cfg.get("handle", ""), row_style=row_style,
                                date=item.get("date"))
                video = Path(out["video"]).read_bytes()
                cover = Path(out["cover"]).read_bytes()
                up = post(
                    f"{url}/api/reels/upload",
                    params={"key": key},
                    data={"articleId": str(item["id"]), "look": json.dumps(out["look"]),
                          "coverAt": f"{out['cover_at']:.2f}", "posterCredit": credit},
                    files={"video": ("reel.mp4", video, "video/mp4"), "cover": ("cover.jpg", cover, "image/jpeg"),
                           **poster_file},
                    timeout=300,
                )
                up.raise_for_status()
            last = row_style
            made += 1
            print(f"   Uploaded ({row_style}, {out['look']['music'] or 'no music'})")
        except Exception as e:   # one failed story never stops the others; the site shows the error
            print(f"   Failed: {e}", file=sys.stderr)
            requests.post(f"{url}/api/reels/upload", params={"key": key},
                          data={"articleId": str(item["id"]), "error": str(e)[:500]}, timeout=60)
    return made


def sample(out_dir: Path) -> None:
    """A demo reel from a made-up story, to check the look without the website."""
    story = Story(
        category="world", category_label="World", headline="Peace talks resume in Cairo after ceasefire holds",
        highlight="Cairo", summary="Negotiators met face to face for the first time in three months.",
        facts=[{"label": "Ceasefire", "value": "7 days"}, {"label": "Delegations", "value": "2 sides"},
               {"label": "Next round", "value": "Sunday"}],
        points=["Aid convoys reached cut-off areas", "Draft framework expected within days"],
        mood="breaking", scene="government", props=["handshake", "globe", "document"],
        source_name="Reuters",
    )
    out = make_reel(story, out_dir, handle="@nexvanimedia", row_style=os.environ.get("ROW_STYLE", "cols"))
    print(f"Sample reel: {out['video']}  ({out['look']})")


def poster_samples(out_dir: Path, limit: int = 10) -> None:
    """Website posters for the latest published stories (real photo + brand), to preview the design."""
    url, key = site()
    res = requests.get(f"{url}/api/reels/samples", params={"key": key, "limit": limit}, timeout=240)
    res.raise_for_status()
    out_dir.mkdir(parents=True, exist_ok=True)
    notes = ["# Poster samples", ""]
    for n, item in enumerate(res.json().get("items", []), 1):
        print(f"Poster {n}: {item['title']}")
        story = Story.from_script(item["script"], item["category"]["slug"], item["category"]["name"],
                                  item.get("sourceName", ""))
        story.style["color"] = item["category"].get("color", "")
        name = f"{n:02d}-{item['slug'][:40]}.jpg"
        _, credit = make_poster(story, item, url, key, True, out_dir / name)
        notes += [f"## {n}. {item['title']}", f"- file: {name}",
                  f"- search terms: {', '.join(story.imageQueries or []) or '-'}", f"- image: {credit}", ""]
    (out_dir / "README.md").write_text("\n".join(notes), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--loop", type=float, metavar="MINUTES", help="keep running, one round every N minutes")
    ap.add_argument("--hours", type=float, default=0, help="with --loop: stop after this many hours (0 = never)")
    ap.add_argument("--sample", type=Path, metavar="DIR", help="make a demo reel in DIR and exit")
    ap.add_argument("--poster-samples", type=Path, metavar="DIR",
                    help="make website posters for the 10 latest stories in DIR and exit")
    args = ap.parse_args()
    if args.poster_samples:
        poster_samples(args.poster_samples)
        return
    if args.sample:
        sample(args.sample)
        return
    fetch_music()
    if not args.loop:
        try:
            poster_pass()
        except Exception as e:
            print(f"Poster pass failed: {e}", file=sys.stderr)
        round_once()
        return
    end = time.time() + args.hours * 3600 if args.hours else None
    while end is None or time.time() < end:
        try:
            poster_pass()
            round_once()
        except Exception as e:
            print(f"Round failed: {e}", file=sys.stderr)
        time.sleep(args.loop * 60)


if __name__ == "__main__":
    main()
