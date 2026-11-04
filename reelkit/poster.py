"""The website's featured image for a story: a 16:9 news poster in the same brand style as the reels.

Layout on 1600x900: a real photo for the story (photos.py, Wikimedia Commons) fills the poster, darkened on the left;
without a photo the drawn cartoon scene takes its place and fades into the category colour. On the left: the category
chip, the headline with its key word highlighted and the most striking number as a badge; NexVani Media top right; the
photo's licence credit bottom right. Nothing is invented: every text comes from the story's reel script.
"""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

from . import brand
from .icons import icon_img
from .paths import ASSETS, chromium_path
from .render import font_css
from .scenes import BY_CATEGORY, scene_html
from .text import esc

WIDTH, HEIGHT = 1600, 900

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1600px; height: 900px; overflow: hidden; }
body { position: relative; color: #fff; font-family: '%(body)s', sans-serif;
  background: linear-gradient(115deg, %(bottom)s 0%%, %(top)s 58%%, %(top)s 100%%); }
.scene { position: absolute; inset: 0; overflow: hidden; }
.scene iframe { position: absolute; border: 0; width: 1536px; height: 1024px; left: 330px; top: -80px; pointer-events: none; }
/* the scene fades into the category colour on the left, where the text sits */
.fade { position: absolute; inset: 0; background:
  linear-gradient(90deg, %(bottom)s 0%%, %(top)s 36%%, %(top)scc 46%%, %(top)s00 66%%),
  linear-gradient(0deg, %(bottom)s99 0%%, transparent 28%%); }
.tex { position: absolute; inset: 0; opacity: .06;
  background: repeating-linear-gradient(135deg, #fff 0 2px, transparent 2px 46px); }
.brand { position: absolute; top: 56px; right: 60px; display: flex; align-items: center; gap: 12px;
  background: rgba(0,0,0,.45); border-radius: 18px; padding: 8px 20px 8px 8px; font: 800 32px/1 '%(font)s', sans-serif;
  white-space: nowrap; backdrop-filter: blur(4px); }
.brand img { width: 54px; height: 54px; border-radius: 12px; }
.left { position: absolute; left: 70px; top: 56px; bottom: 60px; width: 820px; display: flex; flex-direction: column; }
.chip { align-self: flex-start; display: flex; align-items: center; gap: 12px; background: %(accent)s; color: #111;
  border-radius: 60px; padding: 8px 28px 8px 10px; font: 800 36px/1.1 '%(font)s', sans-serif; }
.chip .ic { width: 58px; height: 58px; }
.hl { flex: 1; display: flex; align-items: center; font: 800 96px/1.08 '%(font)s', sans-serif; text-wrap: balance;
  text-shadow: 0 5px 0 rgba(0,0,0,.35), 0 0 36px rgba(0,0,0,.45); }
.hl .hi { color: %(accent)s; }
.bottom { display: flex; align-items: flex-end; }
.badge { display: flex; flex-direction: column; background: #fff; color: %(value)s; border-radius: 22px;
  padding: 12px 26px 10px; box-shadow: 0 12px 30px rgba(0,0,0,.35); border-left: 12px solid %(accent)s; max-width: 560px; }
.badge small { font: 700 26px/1.2 '%(body)s', sans-serif; color: #333; }
.badge b { font: 800 60px/1.05 '%(font)s', sans-serif; }
/* photo mode */
.photo { position: absolute; inset: 0; background: center/cover no-repeat; }
.shade { position: absolute; inset: 0; background:
  linear-gradient(90deg, rgba(0,0,0,.9) 0%%, rgba(0,0,0,.72) 38%%, rgba(0,0,0,.2) 66%%, rgba(0,0,0,0) 82%%),
  linear-gradient(0deg, rgba(0,0,0,.55) 0%%, transparent 30%%); }
.stripe { position: absolute; left: 0; top: 0; bottom: 0; width: 14px; background: %(accent)s; }
.credit { position: absolute; right: 24px; bottom: 18px; max-width: 760px; font: 600 17px/1.3 '%(body)s', sans-serif;
  color: rgba(255,255,255,.85); background: rgba(0,0,0,.45); padding: 4px 10px; border-radius: 8px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
"""


def _scene_doc(story) -> str:
    scene = story.scene if story.scene else BY_CATEGORY.get(story.category, "city")
    return base64.b64encode(scene_html(scene, story.props).encode()).decode()


def _badge(story) -> str:
    # the first short fact value with a number, else the first short fact
    facts = [f for f in story.facts if f.get("value") and len(f["value"]) <= 14]
    fact = next((f for f in facts if any(c.isdigit() for c in f["value"])), facts[0] if facts else None)
    if not fact:
        return "<span></span>"
    return f'<div class="badge"><small>{esc(fact["label"])}</small><b>{esc(fact["value"])}</b></div>'


def poster_page(story, logo_url: str, site_name: str = "NexVani Media", photo: dict | None = None) -> str:
    """photo: {"url": data or https URL, "credit": licence credit} from photos.find_photo; None = drawn scene."""
    label, icon, top, bottom, accent, value = brand.look_for(story)
    css = CSS % {"font": brand.FONT, "body": brand.BODY_FONT, "top": top, "bottom": bottom, "accent": accent, "value": value}
    if photo:
        background = (f'<div class="photo" style="background-image:url({photo["url"]})"></div><div class="shade"></div>'
                      f'<div class="stripe"></div><div class="credit">Representative image · {esc(photo["credit"])}</div>')
    else:
        background = (f'<div class="scene"><iframe src="data:text/html;base64,{_scene_doc(story)}"></iframe>'
                      f'<div class="fade"></div></div><div class="tex"></div>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font_css()}
{css}</style></head><body>
  {background}
  <div class="brand"><img src="{logo_url}" alt=""><span>{esc(site_name)}</span></div>
  <div class="left">
    <div class="chip">{icon_img(icon)}{esc(label)}</div>
    <div class="hl" data-fit data-max="104" data-min="58"><div>{brand._headline(story)}</div></div>
    <div class="bottom">{_badge(story)}</div>
  </div>
</body></html>"""


def logo_data_url() -> str:
    path = ASSETS / "logo.png"
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode() if path.exists() else ""


# The same poster without its words, for the website's cards (they print the headline themselves): the drawn scene
# or the photo fills the picture, nothing else.
BARE_CSS = """.left, .brand, .credit { display: none !important; }
.scene iframe { left: 0 !important; top: -40px !important; transform: scale(1.042); transform-origin: 0 0; }
.fade { background: linear-gradient(0deg, rgba(0,0,0,.25) 0%, transparent 35%) !important; }
.shade { background: none !important; }"""


def render_poster(story, out_path: Path, site_name: str = "NexVani Media", photo: dict | None = None,
                  bare_path: Path | None = None) -> Path:
    """JPEG poster (1600x900) for the story; photo as returned by photos.find_photo (with "bytes"), or None.
    bare_path: also save the poster without its words there."""
    if photo and photo.get("bytes"):
        photo = {**photo, "url": f"data:{photo.get('mime', 'image/jpeg')};base64,"
                 + base64.b64encode(photo["bytes"]).decode()}
    html = poster_page(story, logo_data_url(), site_name, photo)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path())
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.set_content(html, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)   # let the scene frame paint
        if not page.evaluate(brand.FIT):
            print("   Warning: some poster text is too long and may be cut off.")
        page.screenshot(path=str(out_path), type="jpeg", quality=88)
        if bare_path:
            page.add_style_tag(content=BARE_CSS)
            page.wait_for_timeout(200)
            page.screenshot(path=str(bare_path), type="jpeg", quality=85)
        browser.close()
    return out_path
