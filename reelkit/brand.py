"""Copied from InstagramFacebookAutomation/src/brand.py (the page's brand reel template), adapted for
NexVani Media: category looks for its sections and labels in the site's language.

The page's one brand template: the same layout on every post, only the category colour changes, so the
profile grid looks like one page.

Fixed zones on the 1080x1920 reel (the profile grid shows only the middle 1080x1440, from y=240 to 1680):
  0-230     brand bar: category and date (cut off in the grid)
  236-588   headline, its key word highlighted
  596-742   "what happened" summary
  750-1270  the story's 3D cut-out (or a big 3D icon) on a glow, with the key number as a badge
  1278-1670 always three rows of the same height: icon, label, value
  1700-1920 follow line, source and handle (Instagram's buttons cover this part)
Every text box keeps its size; long text only gets a smaller font.
"""
import re

from .icons import available, icon_img, icon_key
from .text import esc, highlight_numbers

# category slug -> (icon, background top, background bottom, accent, value colour on the white rows)
# The first five are the original page's looks; the rest are the site's sections in the same spirit.
LOOKS = {
    "government": ("govt", "#1a237e", "#070b33", "#ff9933", "#1a237e"),
    "politics": ("vote", "#4a1676", "#1b0630", "#ffb347", "#4a1676"),
    "crime": ("police", "#1c1c1c", "#000000", "#ff2b2b", "#c40000"),
    "trending": ("fire", "#0a3d91", "#020f2b", "#00e5ff", "#0a3d91"),
    "good_news": ("trophy", "#0d5c34", "#03231a", "#ffe14d", "#0d6b3a"),
    "world": ("globe", "#0a3d91", "#020f2b", "#00e5ff", "#0a3d91"),
    "india": ("govt", "#b34700", "#3d1600", "#ffd166", "#b34700"),
    "crypto": ("coin", "#5c3d00", "#1c1200", "#ffc93c", "#7a5200"),
    "stock-market": ("chart_up", "#0b4d2e", "#021a10", "#3ddc84", "#0b5c36"),
    "share-market": ("chart_up", "#0b4d2e", "#021a10", "#3ddc84", "#0b5c36"),
    "markets": ("chart_up", "#0b4d2e", "#021a10", "#3ddc84", "#0b5c36"),
    "business": ("chart_up", "#0d4f5c", "#031c22", "#ffd166", "#0d4f5c"),
    "technology": ("phone", "#1a237e", "#070b33", "#00e5ff", "#1a237e"),
    "science": ("bulb", "#3a0ca3", "#10002b", "#ffd60a", "#3a0ca3"),
    "health": ("hospital", "#0d5c34", "#03231a", "#7cff6b", "#0d6b3a"),
    "sports": ("trophy", "#7a1d00", "#2b0a00", "#ffb703", "#9a2a00"),
    "climate": ("sun", "#0d5c34", "#03231a", "#ffe14d", "#0d6b3a"),
    "entertainment": ("star", "#5a0f4a", "#1f0019", "#ffb3ec", "#7a1466"),
}

# Words printed on the poster; set_texts() switches them to the site's language.
TEXT = {
    "what": "What happened?",
    "follow": "👉 Follow {handle} for more news",
    "source": "Source:",
    "point": "Point {n}",
    "before": "Before",
    "now": "Now",
    "change": "Change",
    "just_now": "just now",
}


def set_texts(texts: dict | None) -> None:
    TEXT.update({k: v for k, v in (texts or {}).items() if k in TEXT and v})


def _shade(hex_color: str, factor: float) -> str:
    """The colour darkened (factor < 1) towards black."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(c * factor))) for c in (r, g, b)))


def look_for(story) -> tuple[str, str, str, str, str, str]:
    """(label, icon, top, bottom, accent, value) for the story's category; an unknown category gets a look made
    from its own colour (story.style["color"]) or the World look."""
    label = story.category_label or story.category
    if story.category in LOOKS:
        return (label, *LOOKS[story.category])
    color = (story.style or {}).get("color")
    if color and len(color) == 7:
        return (label, icon_key(label, "pin"), _shade(color, .55), _shade(color, .18), "#ffd166", _shade(color, .7))
    return (label, *LOOKS["world"])

FONT = "Baloo Bhai 2"
BODY_FONT = "Hind Vadodara"

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1920px; overflow: hidden; }
body { font-family: '%(body)s', 'Noto Sans Gujarati', sans-serif; color: #fff; position: relative;
  background: radial-gradient(ellipse at 50%% 55%%, %(top)s 0%%, %(bottom)s 75%%); }
body::before { content: ""; position: absolute; inset: 0; opacity: .07;
  background: repeating-linear-gradient(135deg, #fff 0 2px, transparent 2px 46px); }
.zone { position: absolute; left: 44px; right: 44px; }
[data-fit] { overflow: hidden; }

.bar { top: 60px; height: 130px; display: flex; align-items: center; justify-content: space-between; }
.chip { display: flex; align-items: center; gap: 14px; background: %(accent)s; color: #111; border-radius: 60px;
  padding: 10px 34px 10px 14px; font: 800 44px/1.1 '%(font)s', sans-serif; }
.chip .ic { width: 70px; height: 70px; }
.date { font: 700 36px/1.2 '%(body)s', sans-serif; opacity: .9; text-align: right; }

.hl { top: 236px; height: 352px; display: flex; align-items: center; justify-content: center; text-align: center;
  font-family: '%(font)s', sans-serif; font-weight: 800; line-height: 1.12; text-wrap: balance;
  text-shadow: 0 6px 0 rgba(0,0,0,.35), 0 0 40px rgba(0,0,0,.4); }
.hl .hi { color: %(accent)s; }

.sum { top: 596px; height: 146px; background: rgba(255,255,255,.12); border: 2px solid rgba(255,255,255,.25);
  border-radius: 26px; padding: 14px 26px; display: flex; align-items: center; font-weight: 600; line-height: 1.32; }
.sum b { color: %(accent)s; margin-right: 8px; font-weight: 800; }
.sum .num { color: %(accent)s; font-weight: 800; }

.hero { top: 750px; height: 520px; display: flex; align-items: center; justify-content: center; }
.glow { position: absolute; width: 560px; height: 560px; border-radius: 50%%;
  background: radial-gradient(circle, rgba(255,255,255,.55) 0%%, %(accent)s55 35%%, transparent 70%%); }
.hero .obj { position: relative; max-width: 78%%; max-height: 100%%; object-fit: contain;
  filter: drop-shadow(0 30px 30px rgba(0,0,0,.55)); }
/* the scene has no frame: it spans the full width and fades into the background at every edge */
.hero.has-scene { left: 0; right: 0; top: 700px; height: 640px; z-index: 0; }
.hero .scene { position: absolute; inset: 0; background: center/cover no-repeat;
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%%, #000 22%%, #000 72%%, transparent 100%%),
                      linear-gradient(to right, transparent 0%%, #000 9%%, #000 91%%, transparent 100%%);
  -webkit-mask-composite: source-in; mask-composite: intersect; }
.hero.has-scene .badge { left: 44px; bottom: 96px; z-index: 2; }
.sum, .rows, .hl { z-index: 1; }
.hero .icon-big { position: relative; width: 420px; height: 420px; filter: drop-shadow(0 30px 30px rgba(0,0,0,.5)); }
.badge { position: absolute; left: 0; bottom: 18px; max-width: 470px; background: %(accent)s; color: #111;
  border-radius: 24px; padding: 12px 28px 16px; transform: rotate(-4deg); box-shadow: 0 16px 30px rgba(0,0,0,.45);
  text-align: center; }
.badge small { display: block; font: 700 32px/1.15 '%(body)s', sans-serif; }
.badge b { display: block; font: 800 84px/1 '%(font)s', sans-serif; white-space: nowrap; }

.rows { top: 1278px; height: 392px; overflow: visible; }
/* short facts: three tiles side by side, a round icon popping out of each */
.tiles { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; align-items: end;
  padding-bottom: 8px; }
.tile { position: relative; height: 300px; border-radius: 34px; background: linear-gradient(170deg, #fff 55%%, #f3f3f3);
  border-bottom: 12px solid %(accent)s; box-shadow: 0 18px 30px rgba(0,0,0,.35); padding: 72px 14px 12px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #161616; }
.tile:nth-child(1) { transform: rotate(-3deg); }
.tile:nth-child(2) { transform: translateY(-26px); }
.tile:nth-child(3) { transform: rotate(3deg); }
.tile .ic { position: absolute; top: -56px; left: 50%%; margin-left: -60px; width: 120px; height: 120px; padding: 14px;
  border-radius: 50%%; background: radial-gradient(circle at 35%% 30%%, #fff, %(accent)s); border: 6px solid #fff;
  box-shadow: 0 10px 20px rgba(0,0,0,.3); }
.tile .txt { width: 100%%; height: 190px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.tile strong { color: %(value)s; font-family: '%(font)s', sans-serif; font-weight: 800; }
.tile small { display: block; color: #555; font-weight: 700; font-size: .55em; margin-top: 6px; }
/* longer lines, style "cards": three equal white cards, a coloured icon block on the left */
.rcards { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.rcard { height: 116px; display: flex; background: #fff; border-radius: 30px; overflow: hidden; color: #161616;
  box-shadow: 0 14px 26px rgba(0,0,0,.35); }
.rcard .side { width: 128px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(140deg, %(accent)s, %(accent)s 45%%, %(value)s 160%%); }
.rcard .ic { width: 84px; height: 84px; filter: drop-shadow(0 6px 8px rgba(0,0,0,.25)); }
.rcard .txt { flex: 1; min-width: 0; padding: 4px 30px; display: flex; flex-direction: column; justify-content: center;
  line-height: 1.12; }
.rcard small { color: %(value)s; font-weight: 800; font-size: .6em; letter-spacing: .5px; }
.rcard strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "cols": three equal columns, icon on top, label chip, value wrapping onto up to three lines */
.cols { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; padding-top: 58px; }
.col { position: relative; background: #fff; border-radius: 32px; color: #161616; text-align: center;
  box-shadow: 0 16px 28px rgba(0,0,0,.35); border-bottom: 12px solid %(accent)s; padding: 70px 14px 14px;
  display: flex; flex-direction: column; align-items: center; gap: 10px; }
.col .ic { position: absolute; top: -56px; left: 50%%; margin-left: -58px; width: 116px; height: 116px; padding: 14px;
  border-radius: 50%%; background: radial-gradient(circle at 35%% 30%%, #fff, %(accent)s); border: 6px solid #fff;
  box-shadow: 0 10px 20px rgba(0,0,0,.3); }
.col small { background: %(value)s; color: #fff; border-radius: 30px; padding: 2px 18px 4px; font: 700 26px/1.3 '%(body)s', sans-serif;
  max-width: 100%%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.col .txt { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.15; }
.col strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: %(value)s; }
/* style "steps": a dotted line joins three round icons, each with its own white bubble */
.steps { height: 100%%; position: relative; display: flex; flex-direction: column; justify-content: space-between; padding: 4px 0; }
.steps::before { content: ""; position: absolute; left: 58px; top: 60px; bottom: 60px;
  border-left: 8px dotted %(accent)s; }
.step { position: relative; height: 118px; display: flex; align-items: center; gap: 22px; }
.step .ic { width: 124px; height: 124px; flex-shrink: 0; padding: 16px; border-radius: 50%%; border: 6px solid #fff;
  background: radial-gradient(circle at 35%% 30%%, #fff, %(accent)s); box-shadow: 0 10px 20px rgba(0,0,0,.35); }
.step .txt { flex: 1; min-width: 0; height: 108px; background: #fff; color: #161616; border-radius: 22px 54px 54px 22px;
  padding: 4px 34px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12;
  box-shadow: 0 12px 24px rgba(0,0,0,.32); }
.step small { color: %(value)s; font-weight: 800; font-size: .6em; }
.step strong { font-family: '%(font)s', sans-serif; font-weight: 800; }

/* style "numbers": a big accent number, the text on a frosted bar */
.nums { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 4px 0; }
.num-row { height: 118px; display: flex; align-items: center; gap: 18px; }
.num-row .n { width: 104px; flex-shrink: 0; text-align: center; font: 800 112px/1 '%(font)s', sans-serif; color: %(accent)s;
  text-shadow: 0 6px 0 rgba(0,0,0,.35); }
.num-row .txt { flex: 1; min-width: 0; height: 112px; display: flex; align-items: center; gap: 20px; padding: 6px 26px 6px 10px;
  background: rgba(255,255,255,.14); border: 2px solid rgba(255,255,255,.3); border-radius: 26px; backdrop-filter: blur(6px); }
.num-row .ic { width: 86px; height: 86px; flex-shrink: 0; }
.num-row .t { flex: 1; min-width: 0; height: 100%%; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.num-row small { color: %(accent)s; font-weight: 800; font-size: .6em; }
.num-row strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: #fff; }
/* style "split": two cards side by side, the third one wide below */
.split { height: 100%%; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 20px; padding: 6px 0; }
.sp { background: #fff; border-radius: 30px; color: #161616; display: flex; align-items: center; gap: 16px; padding: 10px 22px 10px 14px;
  box-shadow: 0 14px 26px rgba(0,0,0,.35); border-top: 10px solid %(accent)s; }
.sp:nth-child(3) { grid-column: 1 / 3; }
.sp .ic { width: 100px; height: 100px; flex-shrink: 0; padding: 12px; border-radius: 26px;
  background: radial-gradient(circle at 35%% 30%%, #fff, %(accent)s); }
.sp .t { flex: 1; min-width: 0; height: 150px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.sp small { color: %(value)s; font-weight: 800; font-size: .6em; }
.sp strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "tickets": white tickets with cut notches, a dashed tear line before the icon stub */
.tickets { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 4px 0; }
.ticket { height: 116px; display: flex; color: #161616; filter: drop-shadow(0 12px 18px rgba(0,0,0,.35)); }
.ticket .t { flex: 1; min-width: 0; background: #fff; border-radius: 22px 0 0 22px; padding: 4px 30px;
  display: flex; flex-direction: column; justify-content: center; line-height: 1.12;
  -webkit-mask: radial-gradient(circle at 100%% 0, transparent 16px, #000 17px) top / 100%% 51%% no-repeat,
                radial-gradient(circle at 100%% 100%%, transparent 16px, #000 17px) bottom / 100%% 51%% no-repeat; }
.ticket .stub { width: 150px; flex-shrink: 0; background: %(accent)s; border-radius: 0 22px 22px 0; border-left: 5px dashed rgba(0,0,0,.25);
  display: flex; align-items: center; justify-content: center;
  -webkit-mask: radial-gradient(circle at 0 0, transparent 16px, #000 17px) top / 100%% 51%% no-repeat,
                radial-gradient(circle at 0 100%%, transparent 16px, #000 17px) bottom / 100%% 51%% no-repeat; }
.ticket .ic { width: 88px; height: 88px; }
.ticket small { color: %(value)s; font-weight: 800; font-size: .6em; }
.ticket strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "board": one white board, three rows split by thin lines, icons in accent squares */
.board { height: 100%%; background: #fff; border-radius: 36px; padding: 10px 30px; color: #161616;
  box-shadow: 0 18px 32px rgba(0,0,0,.4); border-left: 16px solid %(accent)s; display: flex; flex-direction: column; }
.brow { flex: 1; min-height: 0; display: flex; align-items: center; gap: 22px; }
.brow + .brow { border-top: 3px dashed #ddd; }
.brow .ic { width: 92px; height: 92px; flex-shrink: 0; padding: 12px; border-radius: 24px; background: %(value)s1f; }
.brow .t { flex: 1; min-width: 0; height: 104px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.brow small { color: %(value)s; font-weight: 800; font-size: .6em; }
.brow strong { font-family: '%(font)s', sans-serif; font-weight: 800; }

/* style "tabs": each bar wears its label as a coloured folder tab */
.tabs { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 0 0 4px; }
.tab { position: relative; height: 104px; margin-top: 26px; background: #fff; color: #161616; border-radius: 0 26px 26px 26px;
  display: flex; align-items: center; gap: 18px; padding: 6px 26px 6px 14px; box-shadow: 0 12px 22px rgba(0,0,0,.35); }
.tab small { position: absolute; left: 0; top: -38px; height: 40px; background: %(accent)s; color: #111; border-radius: 18px 18px 0 0;
  padding: 2px 24px; font: 800 26px/36px '%(body)s', sans-serif; white-space: nowrap; }
.tab .ic { width: 80px; height: 80px; flex-shrink: 0; }
.tab .t { flex: 1; min-width: 0; height: 92px; display: flex; align-items: center; line-height: 1.12; }
.tab strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: %(value)s; }
/* style "neon": dark glassy bars with a glowing accent outline, no white */
.neon { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.nrow { height: 112px; display: flex; align-items: center; gap: 20px; padding: 6px 28px 6px 12px; border-radius: 60px;
  background: rgba(0,0,0,.35); border: 4px solid %(accent)s; box-shadow: 0 0 22px %(accent)s88, inset 0 0 18px %(accent)s44; }
.nrow .ic { width: 90px; height: 90px; flex-shrink: 0; padding: 10px; border-radius: 50%%; background: radial-gradient(circle at 35%% 30%%, #fff, #ddd); }
.nrow .t { flex: 1; min-width: 0; height: 96px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.nrow small { color: %(accent)s; font-weight: 800; font-size: .6em; }
.nrow strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: #fff; }
/* style "circles": three big round icons in a row, the text straight on the background below */
.circles { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.circ { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 10px; }
.circ .ic { width: 168px; height: 168px; flex-shrink: 0; padding: 26px; border-radius: 50%%; border: 8px solid %(accent)s;
  background: radial-gradient(circle at 35%% 30%%, #fff, #f1f1f1); box-shadow: 0 14px 26px rgba(0,0,0,.4); }
.circ small { color: %(accent)s; font: 800 28px/1.2 '%(body)s', sans-serif; }
.circ .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: flex-start; justify-content: center; line-height: 1.15; }
.circ strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: #fff; text-shadow: 0 4px 0 rgba(0,0,0,.35); }
/* style "strips": bold accent-to-colour bars, white text, the icon in a white bubble on the right */
.strips { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.strip-row { height: 116px; display: flex; align-items: center; gap: 18px; padding: 6px 10px 6px 30px; border-radius: 22px;
  background: linear-gradient(100deg, %(value)s 0%%, %(value)s 55%%, %(accent)s 140%%); border: 3px solid rgba(255,255,255,.35);
  box-shadow: 0 12px 24px rgba(0,0,0,.4); }
.strip-row .t { flex: 1; min-width: 0; height: 100px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.strip-row small { color: %(accent)s; font-weight: 800; font-size: .6em; }
.strip-row strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: #fff; }
.strip-row .ic { width: 96px; height: 96px; flex-shrink: 0; padding: 12px; border-radius: 50%%; background: #fff; }

/* style "tv": TV-news lower thirds, a slanted accent label block, then a white bar */
.tv { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.tvrow { height: 112px; display: flex; filter: drop-shadow(0 10px 16px rgba(0,0,0,.4)); }
.tvrow .lab { width: 250px; flex-shrink: 0; background: %(accent)s; color: #111; display: flex; align-items: center; gap: 10px;
  padding: 0 34px 0 16px; clip-path: polygon(0 0, 100%% 0, calc(100%% - 30px) 100%%, 0 100%%);
  font: 800 30px/1.1 '%(body)s', sans-serif; }
.tvrow .lab .ic { width: 64px; height: 64px; flex-shrink: 0; }
.tvrow .t { flex: 1; min-width: 0; margin-left: -26px; background: #fff; color: #161616; padding: 4px 26px 4px 48px;
  clip-path: polygon(30px 0, 100%% 0, 100%% 100%%, 0 100%%); display: flex; align-items: center; line-height: 1.12;
  border-bottom: 8px solid %(value)s; }
.tvrow strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "notes": three sticky notes pinned in a row */
.notes { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; padding: 30px 6px 10px; }
.note { position: relative; background: linear-gradient(170deg, #fffbe0, #fff2a8); color: #2a2200; border-radius: 6px 6px 30px 6px;
  box-shadow: 0 16px 24px rgba(0,0,0,.4); padding: 64px 16px 16px; display: flex; flex-direction: column; align-items: center;
  text-align: center; gap: 6px; }
.note:nth-child(1) { transform: rotate(-3deg); } .note:nth-child(2) { transform: rotate(2deg); background: linear-gradient(170deg, #fff, #eaf4ff); }
.note:nth-child(3) { transform: rotate(-2deg); background: linear-gradient(170deg, #fff, #ffe8ec); }
.note .ic { position: absolute; top: -34px; left: 50%%; margin-left: -46px; width: 92px; height: 92px;
  filter: drop-shadow(0 8px 8px rgba(0,0,0,.3)); }
.note small { color: %(value)s; font: 800 26px/1.2 '%(body)s', sans-serif; }
.note .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.15; }
.note strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "capsules": one capsule per row, the label half in colour, the value half white */
.caps { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.cap { height: 112px; display: flex; border-radius: 60px; overflow: hidden; background: #fff; box-shadow: 0 12px 22px rgba(0,0,0,.35); }
.cap .lab { width: 290px; flex-shrink: 0; background: %(value)s; color: #fff; display: flex; align-items: center; gap: 12px;
  padding: 0 18px 0 14px; font: 800 30px/1.15 '%(body)s', sans-serif; border-right: 8px solid %(accent)s; }
.cap .lab .ic { width: 82px; height: 82px; flex-shrink: 0; padding: 8px; border-radius: 50%%; background: #fff; }
.cap .t { flex: 1; min-width: 0; padding: 4px 34px 4px 26px; display: flex; align-items: center; color: #161616; line-height: 1.12; }
.cap strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "stats": dark stat cards, icon in the corner, the value large in accent */
.stats { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 10px 0; }
.stat { position: relative; border-radius: 30px; background: linear-gradient(160deg, rgba(255,255,255,.2), rgba(0,0,0,.35));
  border: 3px solid rgba(255,255,255,.3); padding: 22px 18px; display: flex; flex-direction: column; gap: 8px;
  box-shadow: 0 14px 26px rgba(0,0,0,.4); }
.stat .ic { width: 84px; height: 84px; }
.stat small { color: rgba(255,255,255,.85); font: 700 28px/1.2 '%(body)s', sans-serif; }
.stat .t { height: 168px; display: flex; align-items: center; line-height: 1.15; }
.stat strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: %(accent)s; }

/* style "comic": pop-art panels, thick ink outlines, hard shadows, halftone dots, a tilted caption box */
.comic { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 8px 10px 14px 0; }
.cpanel { position: relative; height: 108px; display: flex; align-items: center; gap: 18px; padding: 4px 26px 4px 12px;
  background: radial-gradient(circle, rgba(0,0,0,.09) 2px, transparent 2.5px) 0 0 / 14px 14px, #fff;
  border: 5px solid #111; border-radius: 12px; box-shadow: 9px 9px 0 #111; color: #111; }
.cpanel:nth-child(2) { transform: rotate(-1deg); } .cpanel:nth-child(3) { transform: rotate(.8deg); }
.cpanel .ic { width: 84px; height: 84px; flex-shrink: 0; padding: 8px; border: 4px solid #111; border-radius: 50%%; background: %(accent)s; }
.cpanel small { position: absolute; top: -24px; right: 26px; background: %(accent)s; border: 4px solid #111; padding: 0 14px 2px;
  font: 800 26px/1.3 '%(font)s', sans-serif; transform: rotate(2deg); white-space: nowrap; }
.cpanel .t { flex: 1; min-width: 0; height: 92px; display: flex; align-items: center; line-height: 1.1; }
.cpanel strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "keys": chunky 3D push buttons, the icon on its own sunken key */
.keys { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 0 0 18px; }
.key { height: 110px; display: flex; align-items: center; gap: 20px; padding: 0 28px 10px 12px; border-radius: 30px;
  background: linear-gradient(180deg, #fff 0%%, #eceff3 100%%); color: #161616;
  box-shadow: inset 0 -12px 0 #c9ced6, 0 10px 0 %(value)s, 0 18px 24px rgba(0,0,0,.45); }
.key .ic { width: 86px; height: 86px; flex-shrink: 0; padding: 10px; border-radius: 22px; background: %(accent)s;
  box-shadow: inset 0 -8px 0 rgba(0,0,0,.2), inset 0 4px 0 rgba(255,255,255,.5); }
.key .t { flex: 1; min-width: 0; height: 92px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.key small { color: %(value)s; font-weight: 800; font-size: .6em; }
.key strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "signs": green highway sign boards with a white inner border and an arrow */
.signs { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.sign { height: 114px; display: flex; align-items: center; gap: 18px; padding: 0 20px 0 14px; border-radius: 16px; background: #0a6b3b;
  outline: 4px solid #fff; outline-offset: -11px; box-shadow: 0 0 0 4px #054526, 0 14px 24px rgba(0,0,0,.45); color: #fff; }
.sign .ic { width: 80px; height: 80px; flex-shrink: 0; padding: 8px; border-radius: 50%%; background: #fff; }
.sign .t { flex: 1; min-width: 0; height: 84px; display: flex; flex-direction: column; justify-content: center; line-height: 1.1; }
.sign small { color: #ffe14d; font-weight: 800; font-size: .58em; }
.sign strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
.sign .arr { flex-shrink: 0; font: 800 64px/1 '%(font)s', sans-serif; color: #fff; }
/* style "chat": incoming chat messages, a round avatar, sender name in colour, time and double tick */
.chat { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 4px 0; }
.msg { height: 118px; display: flex; align-items: flex-end; gap: 14px; }
.msg .ic { width: 78px; height: 78px; flex-shrink: 0; padding: 10px; border-radius: 50%%; background: %(accent)s;
  border: 4px solid #fff; }
.msg .b { position: relative; flex: 1; min-width: 0; height: 112px; background: #fff; color: #111; border-radius: 6px 30px 30px 30px;
  padding: 6px 120px 6px 24px; box-shadow: 0 8px 18px rgba(0,0,0,.35); }
.msg:nth-child(2) .b { background: #dcf8c6; }
.msg .b::before { content: ""; position: absolute; left: -16px; bottom: 14px; border: 14px solid transparent;
  border-right-color: inherit; }
.msg .t { height: 100%%; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.msg small { color: %(value)s; font-weight: 800; font-size: .58em; }
.msg strong { font-weight: 700; }
.msg .tm { position: absolute; right: 20px; bottom: 8px; font: 600 24px/1 '%(body)s', sans-serif; color: #7a8a7a; }
.msg .tm i { color: #34b7f1; font-style: normal; font-weight: 800; }

/* style "glass": liquid glass, frosted bars with a light rim, a shine across the top and a glass icon bubble */
.glassy { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.gl { position: relative; height: 114px; display: flex; align-items: center; gap: 20px; padding: 0 30px 0 12px; border-radius: 60px;
  background: linear-gradient(180deg, rgba(255,255,255,.32), rgba(255,255,255,.08)); backdrop-filter: blur(14px) saturate(160%%);
  border: 2px solid rgba(255,255,255,.55); box-shadow: inset 0 2px 0 rgba(255,255,255,.7), inset 0 -10px 24px rgba(0,0,0,.18),
  0 16px 30px rgba(0,0,0,.35); overflow: hidden; }
.gl::after { content: ""; position: absolute; left: 8%%; right: 8%%; top: 4px; height: 40%%; border-radius: 60px;
  background: linear-gradient(180deg, rgba(255,255,255,.45), transparent); pointer-events: none; }
.gl .ic { width: 92px; height: 92px; flex-shrink: 0; padding: 12px; border-radius: 50%%; background: rgba(255,255,255,.85);
  box-shadow: 0 6px 14px rgba(0,0,0,.25); }
.gl .t { flex: 1; min-width: 0; height: 96px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.gl small { color: %(accent)s; font-weight: 800; font-size: .58em; }
.gl strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: #fff; text-shadow: 0 2px 6px rgba(0,0,0,.35); }
/* style "bento": an uneven bento grid, one tall accent tile and two white tiles */
.bento { height: 100%%; display: grid; grid-template-columns: 1fr 1.55fr; grid-template-rows: 1fr 1fr; gap: 18px; padding: 4px 0; }
.bx { border-radius: 34px; background: #fff; color: #161616; padding: 14px 24px; display: flex; align-items: center; gap: 16px;
  box-shadow: 0 14px 26px rgba(0,0,0,.35); }
.bx:first-child { grid-row: 1 / 3; background: %(accent)s; color: #111; flex-direction: column; justify-content: center;
  align-items: flex-start; }
.bx .ic { width: 84px; height: 84px; flex-shrink: 0; }
.bx:first-child .ic { width: 120px; height: 120px; }
.bx .t { flex: 1; min-width: 0; width: 100%%; display: flex; flex-direction: column; justify-content: center; line-height: 1.12;
  height: 140px; }
.bx:first-child .t { height: 190px; flex: none; }
.bx small { color: %(value)s; font-weight: 800; font-size: .58em; }
.bx:first-child small { color: rgba(0,0,0,.65); }
.bx strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "clay": soft puffy clay buttons in pastel, inner highlights and a soft drop */
.clay { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0 12px; }
.cl { height: 112px; display: flex; align-items: center; gap: 20px; padding: 0 30px 0 14px; border-radius: 40px; color: #222;
  background: #fff4e6; box-shadow: inset 6px 6px 12px rgba(255,255,255,.9), inset -8px -10px 16px rgba(0,0,0,.12),
  0 18px 26px rgba(0,0,0,.35); }
.cl:nth-child(2) { background: #e9f3ff; } .cl:nth-child(3) { background: #f0ffe9; }
.cl .ic { width: 88px; height: 88px; flex-shrink: 0; padding: 12px; border-radius: 30px; background: %(accent)s;
  box-shadow: inset 4px 4px 8px rgba(255,255,255,.7), inset -5px -6px 10px rgba(0,0,0,.18), 0 6px 10px rgba(0,0,0,.18); }
.cl .t { flex: 1; min-width: 0; height: 96px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.cl small { color: %(value)s; font-weight: 800; font-size: .58em; }
.cl strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "aurora": dark cards with a glowing aurora gradient border */
.aurora { height: 100%%; display: flex; flex-direction: column; justify-content: space-between; padding: 6px 0; }
.au { position: relative; height: 112px; border-radius: 28px; padding: 4px;
  background: linear-gradient(100deg, #ff4fd8, %(accent)s 35%%, #33e1ff 70%%, #7c5cff);
  box-shadow: 0 0 26px rgba(124,92,255,.55), 0 12px 24px rgba(0,0,0,.4); }
.au .in { height: 100%%; border-radius: 24px; background: linear-gradient(120deg, #120a24, #1d1438); display: flex; align-items: center;
  gap: 20px; padding: 0 28px 0 12px; }
.au .ic { width: 84px; height: 84px; flex-shrink: 0; padding: 10px; border-radius: 22px; background: rgba(255,255,255,.9); }
.au .t { flex: 1; min-width: 0; height: 92px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.au small { font-weight: 800; font-size: .58em; background: linear-gradient(90deg, #ff8ae6, #7fe9ff); -webkit-background-clip: text;
  color: transparent; }
.au strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: #fff; }

/* style "hub": a mind map, the story icon in a big circle, the facts branching off it */
.hub { height: 100%%; position: relative; display: grid; grid-template-columns: 1fr 210px 1fr; grid-template-rows: 214px 1fr;
  column-gap: 26px; row-gap: 26px; }
.hub .core { grid-column: 2; grid-row: 1; align-self: center; width: 210px; height: 210px; border-radius: 50%%; padding: 34px;
  background: radial-gradient(circle at 35%% 30%%, #fff, %(accent)s); border: 8px solid #fff; z-index: 1;
  box-shadow: 0 0 0 10px %(accent)s55, 0 18px 30px rgba(0,0,0,.45); }
.hub .core .ic { width: 100%%; height: 100%%; }
.hub::before { content: ""; position: absolute; left: 16%%; right: 16%%; top: 107px; border-top: 6px dashed %(accent)s; }
.hub::after { content: ""; position: absolute; left: 50%%; top: 200px; height: 50px; border-left: 6px dashed %(accent)s; }
.hn { background: #fff; color: #161616; border-radius: 28px; padding: 12px 20px; box-shadow: 0 14px 24px rgba(0,0,0,.35);
  display: flex; flex-direction: column; justify-content: center; text-align: center; align-self: center; height: 180px; z-index: 1; }
.hn.n1 { grid-column: 1; grid-row: 1; } .hn.n2 { grid-column: 3; grid-row: 1; }
.hn.n3 { grid-column: 1 / 4; grid-row: 2; width: 74%%; justify-self: center; height: 128px; }
.hn small { color: %(value)s; font: 800 28px/1.2 '%(body)s', sans-serif; }
.hn .t { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.12; }
.hn strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "stairs": three rising steps, left to right, each with its icon standing on top */
.stairs { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; align-items: end; }
.st { position: relative; border-radius: 26px 26px 8px 8px; background: linear-gradient(180deg, #fff, #e9e9ee); color: #161616;
  padding: 50px 16px 14px; text-align: center; display: flex; flex-direction: column; box-shadow: 0 14px 24px rgba(0,0,0,.4);
  border-top: 12px solid %(accent)s; }
.st:nth-child(1) { height: 250px; } .st:nth-child(2) { height: 310px; } .st:nth-child(3) { height: 370px; }
.st .ic { position: absolute; top: -62px; left: 50%%; margin-left: -50px; width: 100px; height: 100px;
  filter: drop-shadow(0 8px 8px rgba(0,0,0,.35)); }
.st .no { position: absolute; left: 14px; bottom: 6px; font: 800 80px/1 '%(font)s', sans-serif; color: %(value)s22; }
.st small { color: %(value)s; font: 800 26px/1.2 '%(body)s', sans-serif; }
.st .t { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.15; position: relative; }
.st strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "arrows": a process, three chevron arrows pointing right, icon on top of each */
.arrows { height: 100%%; display: flex; align-items: center; filter: drop-shadow(0 14px 18px rgba(0,0,0,.4)); }
.ar { position: relative; flex: 1; height: 300px; margin-left: -34px; padding: 70px 54px 20px 70px; color: #161616; text-align: center;
  display: flex; flex-direction: column; background: #fff;
  clip-path: polygon(0 0, calc(100%% - 56px) 0, 100%% 50%%, calc(100%% - 56px) 100%%, 0 100%%, 56px 50%%); }
.ar:first-child { margin-left: 0; padding-left: 26px; clip-path: polygon(0 0, calc(100%% - 56px) 0, 100%% 50%%, calc(100%% - 56px) 100%%, 0 100%%); border-radius: 26px 0 0 26px; }
.ar:nth-child(2) { background: %(accent)s; }
.ar .ic { position: absolute; top: 14px; left: 50%%; margin-left: -34px; width: 68px; height: 68px; }
.ar:first-child .ic { margin-left: -46px; }
.ar small { color: %(value)s; font: 800 24px/1.2 '%(body)s', sans-serif; }
.ar .t { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.12; }
.ar strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "paper": a newspaper clipping, torn edges, three columns split by rules, values under a marker */
.paper { height: 100%%; padding: 34px 28px 30px; background: #f7f1e3; color: #1b1b1b; transform: rotate(-1.2deg);
  box-shadow: 0 18px 30px rgba(0,0,0,.45); display: grid; grid-template-columns: repeat(3, 1fr);
  clip-path: polygon(0 3%%, 4%% 0, 9%% 2.5%%, 15%% 0, 22%% 2%%, 30%% 0, 37%% 2.8%%, 45%% .5%%, 53%% 2.6%%, 61%% 0, 69%% 2.2%%, 77%% .3%%, 85%% 2.7%%, 92%% 0, 100%% 2.4%%,
    100%% 97%%, 95%% 100%%, 88%% 97.5%%, 80%% 100%%, 72%% 97.2%%, 64%% 99.6%%, 56%% 97.4%%, 48%% 100%%, 40%% 97.6%%, 32%% 99.8%%, 24%% 97.3%%, 16%% 100%%, 8%% 97.5%%, 0 100%%); }
.pc { padding: 0 18px; display: flex; flex-direction: column; gap: 6px; text-align: left; }
.pc + .pc { border-left: 3px double #9a8f7a; }
.pc .hd { display: flex; align-items: center; gap: 10px; border-bottom: 3px solid #1b1b1b; padding-bottom: 6px; }
.pc .ic { width: 54px; height: 54px; flex-shrink: 0; }
.pc small { font: 800 26px/1.15 '%(body)s', sans-serif; text-transform: uppercase; }
.pc .t { flex: 1; min-height: 0; display: flex; align-items: center; line-height: 1.25; }
.pc strong { font-family: '%(font)s', sans-serif; font-weight: 800;
  background: linear-gradient(transparent 55%%, %(accent)s 55%%, %(accent)s 92%%, transparent 92%%); box-decoration-break: clone;
  -webkit-box-decoration-break: clone; }
/* style "magazine": no boxes, type only; the main fact large with an outlined number, two smaller facts beside it */
.mag { height: 100%%; display: grid; grid-template-columns: 1.25fr 1fr; gap: 0 30px; }
.mg { position: relative; display: flex; flex-direction: column; justify-content: center; padding-left: 4px; }
.mg:first-child { grid-row: 1 / 3; border-right: 4px solid %(accent)s; padding-right: 26px; }
.mg .no { font: 800 140px/0.9 '%(font)s', sans-serif; color: transparent; -webkit-text-stroke: 3px %(accent)s; }
.mg:not(:first-child) .no { position: absolute; right: 0; top: 4px; font-size: 80px; opacity: .6; }
.mg small { display: flex; align-items: center; gap: 10px; color: %(accent)s; font: 800 30px/1.2 '%(body)s', sans-serif; }
.mg small .ic { width: 52px; height: 52px; }
.mg .t { height: 190px; display: flex; align-items: center; line-height: 1.12; }
.mg:not(:first-child) .t { height: 116px; }
.mg:nth-child(2) { border-bottom: 3px solid rgba(255,255,255,.25); }
.mg strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: #fff; text-shadow: 0 4px 0 rgba(0,0,0,.3); }

/* style "road": a winding road across the bottom, a pin standing on it under each fact */
.road { height: 100%%; position: relative; display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.road svg { position: absolute; left: -44px; right: -44px; bottom: 0; width: calc(100%% + 88px); height: 170px; }
.rd { position: relative; display: flex; flex-direction: column; align-items: center; }
.rd .card2 { width: 100%%; height: 190px; background: #fff; color: #161616; border-radius: 26px; padding: 10px 16px; text-align: center;
  display: flex; flex-direction: column; box-shadow: 0 12px 22px rgba(0,0,0,.4); }
.rd .card2::after { content: ""; position: absolute; left: 50%%; top: 188px; margin-left: -14px; border: 14px solid transparent;
  border-top-color: #fff; }
.rd .ic { position: absolute; width: 96px; height: 96px; left: 50%%; margin-left: -48px; filter: drop-shadow(0 8px 6px rgba(0,0,0,.45)); }
.rd:nth-child(2) .ic { top: 236px; } .rd:nth-child(3) .ic { top: 266px; } .rd:nth-child(4) .ic { top: 222px; }
.rd small { color: %(value)s; font: 800 26px/1.2 '%(body)s', sans-serif; }
.rd .t { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.12; }
.rd strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "rope": cards hanging from a sagging rope with wooden pegs */
.rope { height: 100%%; position: relative; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; padding-top: 34px; }
.rope svg { position: absolute; left: -44px; top: 0; width: calc(100%% + 88px); height: 80px; }
.hang { position: relative; height: 330px; background: #fff; color: #161616; border-radius: 10px 10px 28px 28px; padding: 46px 16px 16px;
  text-align: center; display: flex; flex-direction: column; align-items: center; gap: 4px; box-shadow: 0 16px 26px rgba(0,0,0,.45);
  transform-origin: 50%% 0; }
.hang:nth-of-type(1) { transform: rotate(3deg); margin-top: 6px; } .hang:nth-of-type(2) { transform: rotate(-1.5deg); margin-top: 26px; }
.hang:nth-of-type(3) { transform: rotate(-3.5deg); margin-top: 6px; }
.hang::before { content: ""; position: absolute; top: -26px; left: 50%%; margin-left: -12px; width: 24px; height: 58px; border-radius: 6px;
  background: linear-gradient(90deg, #b9824a, #e2b07a, #b9824a); box-shadow: 0 3px 4px rgba(0,0,0,.35); }
.hang .ic { width: 84px; height: 84px; flex-shrink: 0; }
.hang small { color: %(value)s; font: 800 26px/1.2 '%(body)s', sans-serif; }
.hang .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.12; }
.hang strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "puzzle": three jigsaw pieces locked together, each knob in the colour of its own piece */
.puzzle { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); align-items: center; padding: 0 30px 0 0;
  filter: drop-shadow(0 16px 20px rgba(0,0,0,.45)); }
.pz { position: relative; height: 300px; background: #fff; color: #161616; padding: 18px 30px 18px 22px; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 4px; }
.pz:nth-child(1) { border-radius: 30px 0 0 30px; z-index: 3; } .pz:nth-child(2) { background: %(accent)s; z-index: 2; }
.pz:nth-child(3) { border-radius: 0 30px 30px 0; z-index: 1; padding-left: 40px; }
.pz:nth-child(2) { padding-left: 40px; }
.pz:not(:last-child)::after { content: ""; position: absolute; right: -36px; top: 50%%; margin-top: -40px; width: 80px; height: 80px;
  border-radius: 50%%; background: inherit; }
.pz:nth-child(1)::before, .pz:nth-child(2)::before { content: ""; position: absolute; left: 50%%; bottom: -30px; margin-left: -34px;
  width: 68px; height: 68px; border-radius: 50%%; background: inherit; }
.pz .ic { width: 84px; height: 84px; flex-shrink: 0; position: relative; z-index: 1; }
.pz small { color: %(value)s; font: 800 26px/1.2 '%(body)s', sans-serif; position: relative; z-index: 1; }
.pz:nth-child(2) small { color: #111; }
.pz .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.12;
  position: relative; z-index: 1; }
.pz strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "pyramid": a three-tier pyramid of icons on the left, each tier's fact beside it */
.pyr { height: 100%%; display: grid; grid-template-columns: 400px 1fr; grid-template-rows: repeat(3, 1fr); column-gap: 0; row-gap: 8px; }
.tier.r1, .pf:nth-of-type(4) { grid-row: 1; } .tier.r2, .pf:nth-of-type(5) { grid-row: 2; } .tier.r3, .pf:nth-of-type(6) { grid-row: 3; }
.tier { grid-column: 1; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0 8px 8px rgba(0,0,0,.35)); }
.tier div { height: 100%%; display: flex; align-items: center; justify-content: center; background: %(accent)s; }
.tier.r1 div { width: 100%%; clip-path: polygon(50%% 0, 66.7%% 100%%, 33.3%% 100%%); background: #fff; padding-top: 40px; }
.tier.r2 div { width: 100%%; clip-path: polygon(31.3%% 0, 68.7%% 0, 83.3%% 100%%, 16.7%% 100%%); background: %(accent)s; }
.tier.r3 div { width: 100%%; clip-path: polygon(14.6%% 0, 85.4%% 0, 100%% 100%%, 0 100%%); background: %(value)s; }
.tier .ic { width: 70px; height: 70px; padding: 8px; border-radius: 50%%; background: rgba(255,255,255,.9); }
.tier.r1 .ic { width: 58px; height: 58px; padding: 0; background: none; }
.pf { grid-column: 2; display: flex; align-items: center; gap: 0; }
.pf::before { content: ""; width: 44px; flex-shrink: 0; border-top: 5px dotted %(accent)s; }
.pf .t { flex: 1; min-width: 0; height: 112px; background: #fff; color: #161616; border-radius: 22px; padding: 4px 22px;
  display: flex; flex-direction: column; justify-content: center; line-height: 1.12; box-shadow: 0 10px 20px rgba(0,0,0,.35); }
.pf small { color: %(value)s; font-weight: 800; font-size: .58em; }
.pf strong { font-family: '%(font)s', sans-serif; font-weight: 800; }

/* style "train": an engine and two coaches on a track, each fact in a coach window */
.train { height: 100%%; position: relative; display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 16px; align-items: end;
  padding-bottom: 46px; }
.train::after { content: ""; position: absolute; left: -44px; right: -44px; bottom: 14px; height: 14px;
  background: repeating-linear-gradient(90deg, #6b4a2b 0 18px, transparent 18px 40px), linear-gradient(#bbb, #bbb) 0 0 / 100%% 5px no-repeat;
  border-top: 5px solid #ccc; }
.coach { position: relative; height: 270px; border-radius: 26px 26px 10px 10px; background: %(value)s; padding: 16px 16px 26px;
  box-shadow: inset 0 -16px 0 rgba(0,0,0,.25), 0 14px 22px rgba(0,0,0,.4); border: 4px solid rgba(255,255,255,.5); }
.coach:first-child { background: %(accent)s; border-radius: 26px 90px 10px 10px; }
.coach:first-child::before { content: ""; position: absolute; left: 30px; top: -58px; width: 54px; height: 60px; border-radius: 10px 10px 0 0;
  background: #333; box-shadow: inset 0 8px 0 #555; }
.coach + .coach::before { content: ""; position: absolute; left: -22px; bottom: 40px; width: 28px; height: 12px; background: #333; }
.coach .wh { position: absolute; bottom: -34px; width: 58px; height: 58px; border-radius: 50%%; background: radial-gradient(circle, #ddd 0 8px, #333 9px 20px, #111 21px);
  border: 4px solid #666; }
.coach .wh.a { left: 26px; } .coach .wh.b { right: 26px; }
.coach .win { height: 100%%; background: #fff; color: #161616; border-radius: 18px; padding: 8px 12px; text-align: center;
  display: flex; flex-direction: column; align-items: center; }
.coach .ic { width: 64px; height: 64px; flex-shrink: 0; }
.coach small { color: %(value)s; font: 800 24px/1.2 '%(body)s', sans-serif; }
.coach .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.12; }
.coach strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "signpost": a wooden post with three arrow boards, pointing right, left, right */
.post { height: 100%%; position: relative; display: flex; flex-direction: column; justify-content: space-between; padding: 0 0 4px; }
.post::before { content: ""; position: absolute; left: 50%%; margin-left: -18px; top: -20px; bottom: -30px; width: 36px; border-radius: 8px;
  background: linear-gradient(90deg, #6b4423, #9c6a3c, #6b4423); box-shadow: 0 10px 18px rgba(0,0,0,.4); }
.sgn { position: relative; width: 90%%; height: 112px; display: flex; align-items: center; gap: 16px; padding: 0 90px 0 24px; color: #3b230d;
  background: repeating-linear-gradient(0deg, rgba(0,0,0,.05) 0 3px, transparent 3px 14px), linear-gradient(180deg, #f2c27f, #d99a52);
  clip-path: polygon(0 0, calc(100%% - 64px) 0, 100%% 50%%, calc(100%% - 64px) 100%%, 0 100%%); filter: drop-shadow(0 8px 10px rgba(0,0,0,.4)); }
.sgn:nth-child(2) { align-self: flex-end; flex-direction: row-reverse; padding: 0 24px 0 90px; text-align: right;
  clip-path: polygon(64px 0, 100%% 0, 100%% 100%%, 64px 100%%, 0 50%%); }
.sgn:nth-child(1) { transform: rotate(-2deg); } .sgn:nth-child(3) { transform: rotate(1.5deg); }
.sgn .ic { width: 78px; height: 78px; flex-shrink: 0; }
.sgn .t { flex: 1; min-width: 0; height: 96px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.sgn small { color: #8a3b00; font-weight: 800; font-size: .58em; }
.sgn strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "calendar": three desk-calendar pages with binder rings and a coloured header */
.cal { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; padding-top: 30px; }
.page { position: relative; border-radius: 18px; background: #fff; color: #161616; overflow: visible; display: flex; flex-direction: column;
  box-shadow: 0 6px 0 #ddd, 0 12px 0 #c8c8c8, 0 22px 26px rgba(0,0,0,.4); }
.page .hd { height: 80px; border-radius: 18px 18px 0 0; background: %(accent)s; display: flex; align-items: center; justify-content: center;
  gap: 8px; padding: 14px 10px 0; color: #111; font: 800 26px/1.15 '%(body)s', sans-serif; text-align: center; }
.page .hd .ic { width: 52px; height: 52px; flex-shrink: 0; }
.page::before, .page::after { content: ""; position: absolute; top: -26px; width: 18px; height: 50px; border-radius: 10px;
  background: linear-gradient(90deg, #888, #eee, #888); }
.page::before { left: 26%%; } .page::after { right: 26%%; }
.page .t { flex: 1; min-height: 0; padding: 10px 14px; display: flex; align-items: center; justify-content: center; text-align: center; line-height: 1.12; }
.page strong { font-family: '%(font)s', sans-serif; font-weight: 800; color: %(value)s; }
/* style "film": a strip of film with sprocket holes, one fact per frame */
.film { height: 100%%; display: flex; align-items: center; }
.reel { width: 100%%; height: 340px; transform: rotate(-2deg); background: #151515; border-radius: 10px; padding: 46px 16px;
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; position: relative; box-shadow: 0 18px 30px rgba(0,0,0,.5); }
.reel::before, .reel::after { content: ""; position: absolute; left: 14px; right: 14px; height: 22px;
  background: repeating-linear-gradient(90deg, #f3f3f3 0 26px, transparent 26px 50px); border-radius: 4px; }
.reel::before { top: 12px; } .reel::after { bottom: 12px; }
.fr { border-radius: 8px; background: linear-gradient(160deg, #fff, #ececec); color: #161616; padding: 8px 12px; text-align: center;
  display: flex; flex-direction: column; align-items: center; }
.fr:nth-child(2) { background: linear-gradient(160deg, #fff6d6, %(accent)s); }
.fr .ic { width: 60px; height: 60px; flex-shrink: 0; }
.fr small { color: %(value)s; font: 800 24px/1.2 '%(body)s', sans-serif; }
.fr .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.12; }
.fr strong { font-family: '%(font)s', sans-serif; font-weight: 800; }

/* style "kites": three Uttarayan kites, the fact in the middle of each, a tail of bows below */
.kites { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; align-items: start; }
.kite { position: relative; height: 100%%; display: flex; justify-content: center; }
.kite .sq { position: absolute; top: 18px; width: 218px; height: 218px; transform: rotate(45deg); border-radius: 10px;
  background: linear-gradient(135deg, %(accent)s 50%%, #ff7a3d 50%%); box-shadow: 0 14px 22px rgba(0,0,0,.4);
  border: 4px solid rgba(255,255,255,.8); }
.kite:nth-child(2) .sq { background: linear-gradient(135deg, #fff 50%%, #4fc3ff 50%%); top: 4px; }
.kite:nth-child(3) .sq { background: linear-gradient(135deg, #ff8fd8 50%%, %(accent)s 50%%); }
.kite .sq::before, .kite .sq::after { content: ""; position: absolute; background: rgba(0,0,0,.25); }
.kite .sq::before { left: 0; top: 0; width: 141%%; height: 4px; transform-origin: 0 0; transform: rotate(45deg); }
.kite .tail { position: absolute; top: 272px; left: 50%%; width: 4px; height: 110px; background: rgba(255,255,255,.7); }
.kite .tail::after { content: "▶◀"; position: absolute; top: 60px; left: -18px; color: %(accent)s; font-size: 22px; letter-spacing: -6px; }
.kite .in { position: relative; z-index: 1; margin-top: 92px; width: 250px; height: 150px; background: rgba(255,255,255,.95); border-radius: 26px;
  box-shadow: 0 6px 12px rgba(0,0,0,.25);
  color: #161616; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 10px 14px; }
.kite:nth-child(2) .in { margin-top: 78px; }
.kite .ic { width: 44px; height: 44px; flex-shrink: 0; }
.kite small { color: %(value)s; font: 800 22px/1.2 '%(body)s', sans-serif; }
.kite .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
.kite strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "clipboard": a clipboard with a metal clip, the facts as ticked lines */
.clip { height: 100%%; position: relative; padding-top: 24px; }
.clip .boardc { height: 100%%; border-radius: 26px; background: #b8834e; padding: 34px 22px 18px; box-shadow: 0 18px 30px rgba(0,0,0,.45); }
.clip .sheet { height: 100%%; background: #fff; border-radius: 10px; padding: 6px 26px; display: flex; flex-direction: column;
  background-image: repeating-linear-gradient(transparent 0 98px, #e3ecf7 98px 101px); }
.clip .metal { position: absolute; top: 0; left: 50%%; margin-left: -130px; width: 260px; height: 70px; border-radius: 16px 16px 30px 30px;
  background: linear-gradient(180deg, #f5f5f5, #9aa0a6); box-shadow: 0 6px 10px rgba(0,0,0,.35); z-index: 1; }
.clip .metal::before { content: ""; position: absolute; left: 50%%; top: 12px; margin-left: -40px; width: 80px; height: 20px; border-radius: 10px;
  background: #b8834e; }
.ln { flex: 1; min-height: 0; display: flex; align-items: center; gap: 18px; color: #161616; }
.ln .box { width: 54px; height: 54px; flex-shrink: 0; border: 5px solid %(value)s; border-radius: 10px; position: relative; }
.ln .box::after { content: "✔"; position: absolute; left: 6px; top: -22px; font-size: 58px; color: #18a558; font-weight: 800; }
.ln .ic { width: 66px; height: 66px; flex-shrink: 0; }
.ln .t { flex: 1; min-width: 0; height: 90px; display: flex; flex-direction: column; justify-content: center; line-height: 1.12; }
.ln small { color: %(value)s; font-weight: 800; font-size: .58em; }
.ln strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "tvs": three old TV sets with rabbit-ear antennas, the fact on each screen */
.tvs { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding-top: 60px; }
.set { position: relative; border-radius: 26px; background: linear-gradient(180deg, #8b5a2b, #5e3a17); padding: 16px 16px 40px;
  box-shadow: 0 16px 26px rgba(0,0,0,.45); }
.set::before, .set::after { content: ""; position: absolute; top: -58px; left: 50%%; width: 5px; height: 66px; background: #ccc;
  transform-origin: 50%% 100%%; }
.set::before { transform: rotate(-30deg); } .set::after { transform: rotate(30deg); }
.set .scr { height: 100%%; border-radius: 30px / 22px; background: radial-gradient(ellipse at 50%% 40%%, #ffffff, #dfe9e3);
  color: #161616; padding: 8px 12px; display: flex; flex-direction: column; align-items: center; text-align: center;
  box-shadow: inset 0 0 18px rgba(0,0,0,.35); border: 5px solid #2a1a0b; }
.set .knobs { position: absolute; bottom: 8px; right: 22px; display: flex; gap: 10px; }
.set .knobs i { width: 22px; height: 22px; border-radius: 50%%; background: #e0c08a; }
.set .ic { width: 56px; height: 56px; flex-shrink: 0; }
.set small { color: %(value)s; font: 800 22px/1.2 '%(body)s', sans-serif; }
.set .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
.set strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "balloons": three balloons on strings, the fact written on each */
.balloons { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.bl { position: relative; display: flex; flex-direction: column; align-items: center; }
.bl .ball { position: relative; width: 300px; height: 300px; border-radius: 50%% 50%% 48%% 48%% / 56%% 56%% 44%% 44%%;
  background: radial-gradient(circle at 32%% 28%%, rgba(255,255,255,.75) 0 8%%, transparent 22%%), %(accent)s;
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 20px 26px; color: #111;
  box-shadow: inset -16px -20px 30px rgba(0,0,0,.18), 0 14px 22px rgba(0,0,0,.35); }
.bl:nth-child(2) .ball { background: radial-gradient(circle at 32%% 28%%, rgba(255,255,255,.8) 0 8%%, transparent 22%%), #fff; margin-top: -10px; }
.bl:nth-child(3) .ball { background: radial-gradient(circle at 32%% 28%%, rgba(255,255,255,.75) 0 8%%, transparent 22%%), #7fd3ff; }
.bl .ball::after { content: ""; position: absolute; bottom: -14px; left: 50%%; margin-left: -12px; border: 12px solid transparent;
  border-bottom: 18px solid; border-bottom-color: inherit; }
.bl .str { width: 3px; flex: 1; background: rgba(255,255,255,.7); margin-top: 4px; }
.bl .ic { width: 54px; height: 54px; flex-shrink: 0; }
.bl small { color: %(value)s; font: 800 22px/1.2 '%(body)s', sans-serif; }
.bl .t { width: 100%%; height: 130px; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
.bl strong { font-family: '%(font)s', sans-serif; font-weight: 800; }

/* style "thali": a steel thali, each fact in its own katori */
.thali { height: 100%%; display: flex; align-items: center; justify-content: center; }
.plate { width: 100%%; height: 380px; border-radius: 50%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; align-items: center;
  padding: 0 54px; background: radial-gradient(ellipse at 50%% 45%%, #f4f6f8 0 55%%, #c9ced4 62%%, #eef1f4 68%%, #9aa1a8 74%%, #e7eaee 100%%);
  box-shadow: 0 20px 34px rgba(0,0,0,.5), inset 0 -10px 20px rgba(0,0,0,.18); }
.katori { width: 100%%; aspect-ratio: 1; border-radius: 50%%; padding: 18px; color: #161616; text-align: center;
  background: radial-gradient(circle at 50%% 40%%, #fffef5 0 58%%, #d6dbe0 64%%, #f6f7f9 70%%, #a9b0b7 100%%);
  box-shadow: 0 10px 16px rgba(0,0,0,.3); display: flex; flex-direction: column; align-items: center; justify-content: center; }
.katori:nth-child(2) { background: radial-gradient(circle at 50%% 40%%, #fff3c4 0 58%%, #d6dbe0 64%%, #f6f7f9 70%%, #a9b0b7 100%%); }
.katori .ic { width: 50px; height: 50px; flex-shrink: 0; }
.katori small { color: %(value)s; font: 800 22px/1.2 '%(body)s', sans-serif; }
.katori .t { width: 78%%; height: 110px; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
.katori strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "station": Indian railway station name boards, yellow with black letters, on two legs */
.station { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.sb { display: flex; flex-direction: column; align-items: stretch; }
.sb .plate2 { height: 250px; background: #ffd400; color: #111; border: 8px solid #111; border-radius: 6px; outline: 4px solid #ffd400;
  padding: 8px 12px; text-align: center; display: flex; flex-direction: column; align-items: center; box-shadow: 0 14px 22px rgba(0,0,0,.45); }
.sb .ic { width: 58px; height: 58px; flex-shrink: 0; }
.sb small { font: 800 24px/1.2 '%(body)s', sans-serif; border-bottom: 3px solid #111; padding: 0 8px; }
.sb .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
.sb strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
.sb .legs { flex: 1; display: flex; justify-content: space-between; padding: 0 40px; }
.sb .legs i { width: 14px; background: linear-gradient(90deg, #555, #aaa, #555); }
/* style "detective": a cork board, notes pinned at different heights, joined by a red string */
.cork { height: 100%%; position: relative; border-radius: 20px; padding: 26px 26px 0; border: 12px solid #6b4423;
  background: radial-gradient(circle at 20%% 30%%, rgba(0,0,0,.08) 2px, transparent 3px) 0 0 / 22px 22px,
              radial-gradient(circle at 70%% 60%%, rgba(255,255,255,.1) 2px, transparent 3px) 0 0 / 17px 17px, #c08a52;
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; align-items: start; box-shadow: 0 16px 28px rgba(0,0,0,.5); }
.cork svg { position: absolute; inset: 0; width: 100%%; height: 100%%; z-index: 2; pointer-events: none; }
.memo { position: relative; height: 230px; background: #fffdf2; color: #161616; padding: 26px 14px 12px; text-align: center;
  display: flex; flex-direction: column; align-items: center; box-shadow: 0 8px 14px rgba(0,0,0,.35); }
.memo:nth-of-type(1) { transform: rotate(-3deg); } .memo:nth-of-type(2) { margin-top: 64px; transform: rotate(2deg); background: #eaf6ff; }
.memo:nth-of-type(3) { margin-top: 22px; transform: rotate(-1.5deg); }
.memo::before { content: ""; position: absolute; top: -12px; left: 50%%; margin-left: -15px; width: 30px; height: 30px; border-radius: 50%%; z-index: 3;
  background: radial-gradient(circle at 35%% 30%%, #ff8a8a, #c40000); box-shadow: 0 4px 5px rgba(0,0,0,.4); }
.memo .ic { width: 56px; height: 56px; flex-shrink: 0; }
.memo small { color: #c40000; font: 800 22px/1.2 '%(body)s', sans-serif; }
.memo .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
.memo strong { font-family: '%(font)s', sans-serif; font-weight: 800; }
/* style "stamps": three postage stamps with perforated edges, a price corner and a postmark */
.stamps { height: 100%%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; align-items: center; }
.stp { height: 330px; padding: 14px; background: #fff; filter: drop-shadow(0 12px 14px rgba(0,0,0,.45));
  -webkit-mask: radial-gradient(circle at 10px 10px, transparent 7px, #000 7.5px) -10px -10px / 20px 20px,
                linear-gradient(#000 0 0) content-box; }
.stp:nth-child(1) { transform: rotate(-3deg); } .stp:nth-child(3) { transform: rotate(3deg); }
.stp .in { position: relative; height: 100%%; border: 5px solid %(value)s; background: linear-gradient(170deg, #fff, %(accent)s33);
  padding: 10px 10px 8px; display: flex; flex-direction: column; align-items: center; text-align: center; color: #161616; overflow: hidden; }
.stp:nth-child(2) .in { background: linear-gradient(170deg, #fff, #7fd3ff44); }
.stp .rs { position: absolute; top: 4px; right: 8px; font: 800 26px/1 '%(font)s', sans-serif; color: %(value)s; }
.stp .pm { position: absolute; right: -30px; bottom: 6px; width: 120px; height: 120px; border-radius: 50%%; border: 4px solid rgba(0,0,0,.18);
  background: repeating-linear-gradient(0deg, transparent 0 14px, rgba(0,0,0,.14) 14px 17px); }
.stp .ic { width: 64px; height: 64px; flex-shrink: 0; margin-top: 18px; }
.stp small { color: %(value)s; font: 800 22px/1.2 '%(body)s', sans-serif; }
.stp .t { width: 100%%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; line-height: 1.1; position: relative; }
.stp strong { font-family: '%(font)s', sans-serif; font-weight: 800; }

.foot { top: 1700px; height: 190px; display: flex; flex-direction: column; align-items: center; gap: 14px; }
.cta { background: %(accent)s; color: #111; border-radius: 50px; padding: 10px 40px; font: 800 40px/1.2 '%(font)s', sans-serif; }
.src { font: 600 28px/1.2 '%(body)s', sans-serif; opacity: .85; }
"""

# Each [data-fit] box keeps its size: its font starts at data-max and shrinks until the text fits.
FIT = """() => {
  let ok = true;
  for (const el of document.querySelectorAll('[data-fit]')) {
    let size = +el.dataset.max;
    const min = +el.dataset.min;
    const over = () => el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2;
    el.style.fontSize = size + 'px';
    while (over() && size > min) { size -= 2; el.style.fontSize = size + 'px'; }
    if (over()) ok = false;
  }
  return ok;
}"""


def _headline(story) -> str:
    text = esc(story.headline)
    key = story.highlight if story.highlight and story.highlight in story.headline else ""
    if not key:   # else the first number in the headline
        match = re.search(r"[₹$€£]?\s?[\d૦-૯][\d૦-૯,.]*\s?(%|કરોડ|લાખ|bn|billion|million|m\b|k\b)?", story.headline)
        key = match.group(0).strip() if match else ""
    return text.replace(esc(key), f'<span class="hi">{esc(key)}</span>', 1) if key else text


def _badge(story) -> str:
    """The most striking short number of the story (from the facts), e.g. ₹110 કરોડ, 35%, 8 મેડલ."""
    for fact in story.facts:
        if re.search(r"[\d૦-૯]", fact["value"]) and len(fact["value"]) <= 11:
            return f'<div class="badge"><small>{esc(fact["label"])}</small><b>{esc(fact["value"])}</b></div>'
    return ""


def _rows(story) -> list[tuple[str, str, str]]:
    """Exactly three (icon, label, value) rows, from the story's layout data, facts and points."""
    rows: list[tuple[str, str, str]] = []
    c = story.compare or {}
    if story.visual == "compare" and c.get("before") and c.get("after"):
        down = c.get("direction") == "down"
        rows += [("calendar", TEXT["before"], c["before"]), ("chart_down" if down else "chart_up", TEXT["now"], c["after"])]
        if c.get("change"):
            rows.append(("coin", TEXT["change"], c["change"]))
    elif story.visual in ("table", "timeline"):
        rows += [(r["left"] + " " + r["right"], r["left"], r["right"]) for r in story.rows]
    elif story.visual == "reasons":
        rows += [(r.get("icon") or r["text"], "", r["text"]) for r in story.reasons]
    badge_value = re.search(r"<b>(.*?)</b>", _badge(story))
    for fact in story.facts:   # facts not already in the badge
        if badge_value and esc(fact["value"]) == badge_value.group(1):
            continue
        rows.append((fact["label"] + " " + fact["value"], fact["label"], fact["value"]))
    rows += [(p, "", p) for p in story.points]
    for fact in story.facts:   # still short of three: the badge's fact too, then the subheadline
        rows.append((fact["label"] + " " + fact["value"], fact["label"], fact["value"]))
    if story.subheadline:
        rows.append((story.subheadline, "", story.subheadline))
    seen, unique = set(), []
    for row in rows:
        if row[2] not in seen:
            seen.add(row[2])
            unique.append(row)
    return unique[:3]


LONG_ROWS = "cards"   # how rows too long for tiles are shown: cards, cols, steps, numbers, split, tickets, board,
#   tabs, neon, circles, strips,
#   tv, notes, capsules, stats,
#   comic, keys, signs, chat,
#   glass, bento, clay, aurora,
#   hub, stairs, arrows, paper, magazine,
#   road, rope, puzzle, pyramid,
#   train, signpost, calendar, film,
#   kites, clipboard, tvs, balloons,
#   thali, station, detective or stamps
SPARE_ICONS = ["pin", "megaphone", "people", "document", "star", "calendar", "check"]


def _rows_html(rows: list[tuple[str, str, str]], style: str | None = None, hub_icon: str = "") -> str:
    """Short facts as three tiles side by side; longer lines as equal cards, columns or steps."""
    keys = []
    for key, _, _ in rows:   # each row its own icon
        key = key if key in available() else icon_key(key, "")
        if not key or key in keys:
            key = next(k for k in SPARE_ICONS if k not in keys)
        keys.append(key)
    rows = [(k, label, value) for k, (_, label, value) in zip(keys, rows)]
    small = lambda label: f"<small>{esc(label)}</small>" if label else ""
    if not style and len(rows) == 3 and all(len(value) <= 18 for _, _, value in rows):
        return '<div class="tiles">' + "".join(
            f'<div class="tile">{icon_img(key)}<div class="txt" data-fit data-max="76" data-min="34">'
            f'<strong>{esc(value)}</strong>{small(label)}</div></div>'
            for key, label, value in rows) + "</div>"
    style = style or LONG_ROWS
    if style == "cols":
        return '<div class="cols">' + "".join(
            f'<div class="col">{icon_img(key)}{small(label)}<div class="txt" data-fit data-max="50" data-min="26">'
            f'<strong>{esc(value)}</strong></div></div>'
            for key, label, value in rows) + "</div>"
    if style == "steps":
        return '<div class="steps">' + "".join(
            f'<div class="step">{icon_img(key)}<div class="txt" data-fit data-max="52" data-min="28">'
            f'{small(label)}<strong>{esc(value)}</strong></div></div>'
            for key, label, value in rows) + "</div>"
    if style == "numbers":
        return '<div class="nums">' + "".join(
            f'<div class="num-row"><div class="n">{i}</div><div class="txt">{icon_img(key)}'
            f'<div class="t" data-fit data-max="50" data-min="26">{small(label)}<strong>{esc(value)}</strong></div></div></div>'
            for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style == "thali":
        return '<div class="thali"><div class="plate">' + "".join(
            f'<div class="katori">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="34" data-min="18">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div></div>"
    if style == "station":
        return '<div class="station">' + "".join(
            f'<div class="sb"><div class="plate2">{icon_img(key)}{small(label or TEXT["point"].format(n=i))}<div class="t" data-fit data-max="44" data-min="20">'
            f'<strong>{esc(value)}</strong></div></div><div class="legs"><i></i><i></i></div></div>'
            for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style == "detective":
        string = ('<svg viewBox="0 0 968 368" preserveAspectRatio="none"><polyline points="150,22 484,84 818,40" fill="none"'
                  ' stroke="#d40000" stroke-width="5" stroke-linejoin="round"/></svg>')
        return '<div class="cork">' + "".join(
            f'<div class="memo">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="40" data-min="20">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + string + "</div>"
    if style == "stamps":
        return '<div class="stamps">' + "".join(
            f'<div class="stp"><div class="in"><span class="rs">₹5</span><span class="pm"></span>{icon_img(key)}{small(label)}'
            f'<div class="t" data-fit data-max="40" data-min="20"><strong>{esc(value)}</strong></div></div></div>'
            for key, label, value in rows) + "</div>"
    if style == "kites":
        return '<div class="kites">' + "".join(
            f'<div class="kite"><div class="sq"></div><div class="tail"></div><div class="in">{icon_img(key)}{small(label)}'
            f'<div class="t" data-fit data-max="36" data-min="18"><strong>{esc(value)}</strong></div></div></div>'
            for key, label, value in rows) + "</div>"
    if style == "clipboard":
        return '<div class="clip"><div class="metal"></div><div class="boardc"><div class="sheet">' + "".join(
            f'<div class="ln"><span class="box"></span>{icon_img(key)}<div class="t" data-fit data-max="44" data-min="22">'
            f'{small(label)}<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div></div></div>"
    if style == "tvs":
        return '<div class="tvs">' + "".join(
            f'<div class="set"><div class="scr">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="38" data-min="20">'
            f'<strong>{esc(value)}</strong></div></div><div class="knobs"><i></i><i></i></div></div>'
            for key, label, value in rows) + "</div>"
    if style == "balloons":
        return '<div class="balloons">' + "".join(
            f'<div class="bl"><div class="ball">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="38" data-min="20">'
            f'<strong>{esc(value)}</strong></div></div><div class="str"></div></div>' for key, label, value in rows) + "</div>"
    if style == "train":
        return '<div class="train">' + "".join(
            f'<div class="coach"><div class="win">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="40" data-min="22">'
            f'<strong>{esc(value)}</strong></div></div><i class="wh a"></i><i class="wh b"></i></div>'
            for key, label, value in rows) + "</div>"
    if style == "signpost":
        return '<div class="post">' + "".join(
            f'<div class="sgn">{icon_img(key)}<div class="t" data-fit data-max="46" data-min="24">{small(label)}'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div>"
    if style == "calendar":
        return '<div class="cal">' + "".join(
            f'<div class="page"><div class="hd">{icon_img(key)}<span>{esc(label or TEXT["point"].format(n=i))}</span></div>'
            f'<div class="t" data-fit data-max="44" data-min="22"><strong>{esc(value)}</strong></div></div>'
            for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style == "film":
        return '<div class="film"><div class="reel">' + "".join(
            f'<div class="fr">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="40" data-min="22">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div></div>"
    if style == "road":
        svg = ('<svg viewBox="0 0 1080 170" preserveAspectRatio="none"><path d="M0 120 C 180 60, 300 160, 540 110 S 900 40, 1080 100"'
               ' fill="none" stroke="#2b2b33" stroke-width="64" stroke-linecap="round"/><path d="M0 120 C 180 60, 300 160, 540 110 S 900 40, 1080 100"'
               ' fill="none" stroke="#fff" stroke-width="6" stroke-dasharray="26 22"/></svg>')
        return '<div class="road">' + svg + "".join(
            f'<div class="rd"><div class="card2">{small(label)}<div class="t" data-fit data-max="44" data-min="22">'
            f'<strong>{esc(value)}</strong></div></div>{icon_img("pin")}</div>'
            for key, label, value in rows) + "</div>"
    if style == "rope":
        svg = ('<svg viewBox="0 0 1080 80" preserveAspectRatio="none"><path d="M0 10 Q 270 70, 540 34 T 1080 12" fill="none"'
               ' stroke="#e9d3a8" stroke-width="7"/></svg>')
        return '<div class="rope">' + svg + "".join(
            f'<div class="hang">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="44" data-min="22">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div>"
    if style == "puzzle":
        return '<div class="puzzle">' + "".join(
            f'<div class="pz">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="42" data-min="22">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div>"
    if style == "pyramid":
        tiers = "".join(f'<div class="tier r{i}"><div>{icon_img(key)}</div></div>' for i, (key, _, _) in enumerate(rows, 1))
        facts = "".join(f'<div class="pf"><div class="t" data-fit data-max="46" data-min="24">{small(label)}<strong>{esc(value)}</strong>'
                        f'</div></div>' for _, label, value in rows)
        return f'<div class="pyr">{tiers}{facts}</div>'
    if style == "hub":
        nodes = "".join(f'<div class="hn n{i}">{small(label)}<div class="t" data-fit data-max="46" data-min="24">'
                        f'<strong>{esc(value)}</strong></div></div>' for i, (_, label, value) in enumerate(rows, 1))
        return f'<div class="hub"><div class="core">{icon_img(hub_icon or rows[0][0])}</div>{nodes}</div>'
    if style == "stairs":
        return '<div class="stairs">' + "".join(
            f'<div class="st">{icon_img(key)}<div class="no">{i}</div>{small(label)}<div class="t" data-fit data-max="46" data-min="24">'
            f'<strong>{esc(value)}</strong></div></div>' for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style == "arrows":
        return '<div class="arrows">' + "".join(
            f'<div class="ar">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="42" data-min="22">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div>"
    if style == "paper":
        return '<div class="paper">' + "".join(
            f'<div class="pc"><div class="hd">{icon_img(key)}<small>{esc(label or TEXT["point"].format(n=i))}</small></div>'
            f'<div class="t" data-fit data-max="44" data-min="22"><strong>{esc(value)}</strong></div></div>'
            for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style == "magazine":
        return '<div class="mag">' + "".join(
            f'<div class="mg"><div class="no">0{i}</div><small>{icon_img(key)}{esc(label)}</small>'
            f'<div class="t" data-fit data-max="{64 if i == 1 else 44}" data-min="24"><strong>{esc(value)}</strong></div></div>'
            for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style in ("glass", "bento", "clay", "aurora"):
        outer, inner = {"glass": ("glassy", "gl"), "bento": ("bento", "bx"), "clay": ("clay", "cl"), "aurora": ("aurora", "au")}[style]
        def tile(key, label, value):
            body = (f'{icon_img(key)}<div class="t" data-fit data-max="{46 if style == "bento" else 50}" data-min="24">'
                    f'{small(label)}<strong>{esc(value)}</strong></div>')
            return f'<div class="in">{body}</div>' if style == "aurora" else body
        return f'<div class="{outer}">' + "".join(f'<div class="{inner}">{tile(*row)}</div>' for row in rows) + "</div>"
    if style in ("comic", "keys", "signs"):
        inner = {"comic": "cpanel", "keys": "key", "signs": "sign"}[style]
        arrow = '<div class="arr">➜</div>' if style == "signs" else ""
        if style == "comic":   # the label goes to the caption box, the text stays big
            return '<div class="comic">' + "".join(
                f'<div class="cpanel">{small(label)}{icon_img(key)}<div class="t" data-fit data-max="52" data-min="26">'
                f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div>"
        return f'<div class="{style}">' + "".join(
            f'<div class="{inner}">{icon_img(key)}<div class="t" data-fit data-max="50" data-min="26">'
            f'{small(label)}<strong>{esc(value)}</strong></div>{arrow}</div>' for key, label, value in rows) + "</div>"
    if style == "chat":
        return '<div class="chat">' + "".join(
            f'<div class="msg">{icon_img(key)}<div class="b"><div class="t" data-fit data-max="46" data-min="24">'
            f'{small(label)}<strong>{esc(value)}</strong></div><span class="tm">{esc(TEXT["just_now"])} <i>✓✓</i></span></div></div>'
            for key, label, value in rows) + "</div>"
    if style in ("tv", "capsules"):
        outer, inner = {"tv": ("tv", "tvrow"), "capsules": ("caps", "cap")}[style]
        return f'<div class="{outer}">' + "".join(
            f'<div class="{inner}"><div class="lab">{icon_img(key)}<span>{esc(label or TEXT["point"].format(n=i))}</span></div>'
            f'<div class="t" data-fit data-max="50" data-min="26"><strong>{esc(value)}</strong></div></div>'
            for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style in ("notes", "stats"):
        inner = {"notes": "note", "stats": "stat"}[style]
        return f'<div class="{style}">' + "".join(
            f'<div class="{inner}">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="46" data-min="24">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div>"
    if style == "tabs":
        return '<div class="tabs">' + "".join(
            f'<div class="tab">{small(label or TEXT["point"].format(n=i))}{icon_img(key)}<div class="t" data-fit data-max="52" data-min="26">'
            f'<strong>{esc(value)}</strong></div></div>' for i, (key, label, value) in enumerate(rows, 1)) + "</div>"
    if style == "circles":
        return '<div class="circles">' + "".join(
            f'<div class="circ">{icon_img(key)}{small(label)}<div class="t" data-fit data-max="46" data-min="24">'
            f'<strong>{esc(value)}</strong></div></div>' for key, label, value in rows) + "</div>"
    if style in ("neon", "strips"):
        inner = {"neon": "nrow", "strips": "strip-row"}[style]
        def line(key, label, value):
            text = f'<div class="t" data-fit data-max="52" data-min="26">{small(label)}<strong>{esc(value)}</strong></div>'
            return text + icon_img(key) if style == "strips" else icon_img(key) + text
        return f'<div class="{style}">' + "".join(f'<div class="{inner}">{line(*row)}</div>' for row in rows) + "</div>"
    if style in ("split", "tickets", "board"):
        outer, inner = {"split": ("split", "sp"), "tickets": ("tickets", "ticket"), "board": ("board", "brow")}[style]
        def body(key, label, value):
            text = f'<div class="t" data-fit data-max="52" data-min="26">{small(label)}<strong>{esc(value)}</strong></div>'
            return text + f'<div class="stub">{icon_img(key)}</div>' if style == "tickets" else icon_img(key) + text
        return f'<div class="{outer}">' + "".join(
            f'<div class="{inner}">{body(*row)}</div>' for row in rows) + "</div>"
    return '<div class="rcards">' + "".join(
        f'<div class="rcard"><div class="side">{icon_img(key)}</div><div class="txt" data-fit data-max="54" data-min="28">'
        f'{small(label)}<strong>{esc(value)}</strong></div></div>'
        for key, label, value in rows) + "</div>"


def brand_page(story, date: str, handle: str, cutout_url: str | None = None, scene_url: str | None = None,
               row_style: str | None = None) -> str:
    """scene_url: a landscape cartoon scene for the picture zone; else the cut-out, else a big 3D icon.
    row_style: how the three facts are drawn (one of the styles in _rows_html); None = tiles or LONG_ROWS."""
    label, icon, top, bottom, accent, value = look_for(story)
    css = CSS % {"font": FONT, "body": BODY_FONT, "top": top, "bottom": bottom, "accent": accent, "value": value}
    story.style.update({"palette": story.category, "visual": story.visual or "checklist"})
    summary = story.summary or story.subheadline
    if scene_url:
        picture = f'<div class="scene" style="background-image:url({scene_url})"></div>'
    elif cutout_url:
        picture = f'<div class="glow"></div><img class="obj" src="{cutout_url}" alt="">'
    else:
        picture = f'<div class="glow"></div>{icon_img(story.headline, "icon-big")}'
    rows = _rows_html(_rows(story), row_style, hub_icon=icon_key(story.headline, icon))
    # fonts are added as bundled @font-face rules by render.py (no Google Fonts request)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>{css}</style></head><body>
  <div class="zone bar"><div class="chip">{icon_img(icon)}{esc(label)}</div><div class="date">{date}</div></div>
  <div class="zone hl" data-fit data-max="124" data-min="64"><div>{_headline(story)}</div></div>
  {f'<div class="zone sum" data-fit data-max="40" data-min="26"><div><b>{esc(TEXT["what"])}</b>{highlight_numbers(summary)}</div></div>' if summary else ''}
  <div class="zone hero{' has-scene' if scene_url else ''}">{picture}{_badge(story)}</div>
  <div class="zone rows">{rows}</div>
  <div class="zone foot"><div class="cta">{esc(TEXT["follow"].format(handle=handle))}</div>
    <div class="src">{esc(TEXT["source"])} {esc(story.source_name)}</div></div>
</body></html>"""
