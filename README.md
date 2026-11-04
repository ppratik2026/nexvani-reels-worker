# Reels worker

Turns every published story into a 9:16 news reel in the **brand reel style of
[InstagramFacebookAutomation](https://github.com/ppratik2026/InstagramFacebookAutomation)** and uploads it to the
website, which posts it to Instagram, Facebook, YouTube Shorts and X (WhatsApp Channel and Snapchat get it in the
dashboard's share queue), with the story link as the first comment.

What is copied from that project (in `reelkit/`, marked in each file):

| Part | Source |
|---|---|
| Poster layout, colours per category, the 29 fact layouts used one after another | `src/brand.py`, `config.yaml` (`card.row_styles`) |
| Intro animation (headline glow, badge slam, cards pop/slide in) | `src/card.py` (`ANIM_CSS`, `ANIM_JS`, `BRAND_STEPS`) |
| Drawn cartoon scenes and 3D icons | `src/scenes.py`, `src/icons.py`, `assets/icons` |
| Music (same tracks), picked by the story's mood, strongest part of the song | `src/music.py`, `assets/music` |
| Video: poster full 9:16, intro first, music fade in/out, cover from the finished poster | `src/video_builder.py`, `main.py` |

Changes for this site: labels in the site's language (English; Hindi built in), the site's sections
(World, Business, Technology…) each with a look, the fonts bundled in `assets/fonts` (no Google Fonts request),
and the story text comes from the website (Gemini writes a short reel script for every published story).

## Flow

```
website: story published → Gemini reel script → queue
worker:  GET /api/reels/queue → draw scene → poster + intro frames (Playwright) → MP4 + music (FFmpeg)
         → POST /api/reels/upload
website: Instagram Reel · Facebook Reel · YouTube Short · X video · share queue → first comment with the story link
```

## Run it

Needs Python 3.10+, FFmpeg and Chromium (Playwright).

```bash
cd reels
pip install -r requirements.txt
python -m playwright install --with-deps chromium     # or set CHROMIUM_PATH to an installed Chrome
python worker.py --sample out/                        # demo reel, no website needed
SITE_URL=https://nexvanimedia.com REELS_SECRET=... python worker.py            # one round
SITE_URL=https://nexvanimedia.com REELS_SECRET=... python worker.py --loop 5   # keep running, every 5 minutes
```

Where to run it:

- **On the website's server (recommended, free):** run `python worker.py --loop 5` as a service next to the site.
- **GitHub Actions:** `.github/workflows/reels.yml` runs every 2 hours and makes up to 10 waiting reels per run
  (`REELS_LIMIT`). Add the repository secrets `SITE_URL` and `REELS_SECRET`. On a private repository this uses
  Actions minutes (2,000 free a month): about 3 minutes of setup per run plus under a minute per reel.

`ROW_STYLE=neon python worker.py --sample out/` forces one fact layout, to preview it.

## Notes

- The music is the same six tracks as the Instagram automation. Use only music you have the rights to; Instagram
  can mute reels with copyrighted songs.
- Instagram does not make links clickable in captions or comments. The comment still shows the link (people can
  copy it); the bio link and story link stickers are the clickable places on Instagram. On Facebook, YouTube and X
  the link in the comment is clickable.
