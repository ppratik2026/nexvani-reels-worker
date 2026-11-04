"""Render the brand poster and its intro animation (copied from InstagramFacebookAutomation/src/card.py, brand
design only), with the fonts bundled locally so the reel looks the same on every machine."""
import base64
from functools import cache
from pathlib import Path

from playwright.sync_api import sync_playwright

from . import brand
from .paths import ASSETS, chromium_path

WIDTH, HEIGHT = 1080, 1920

# Intro animation for the reel: elements fly / punch / slam in one after another.
ANIM_CSS = """<style>
@keyframes dropIn { from { transform: translateY(-160%) var(--t0); opacity: 0; } to { transform: var(--t0); opacity: 1; } }
@keyframes punchIn { 0% { transform: scale(2.6) var(--t0); opacity: 0; } 60% { transform: scale(.92) var(--t0); opacity: 1; }
  100% { transform: var(--t0); } }
@keyframes zoomIn { from { transform: scale(1.35) var(--t0); opacity: 0; } to { transform: var(--t0); opacity: 1; } }
@keyframes slam { 0% { transform: var(--t0) scale(4); opacity: 0; } 55% { transform: var(--t0) scale(.88); opacity: 1; }
  75% { transform: var(--t0) scale(1.08); } 100% { transform: var(--t0); } }
@keyframes slideL { from { transform: translateX(-130%) var(--t0); } to { transform: var(--t0); } }
@keyframes slideR { from { transform: translateX(130%) var(--t0); } to { transform: var(--t0); } }
@keyframes popIn { 0% { transform: scale(0) var(--t0); opacity: 0; } 70% { transform: scale(1.12) var(--t0); opacity: 1; }
  100% { transform: var(--t0); } }
@keyframes riseUp { from { transform: translateY(160%) var(--t0); opacity: 0; } to { transform: var(--t0); opacity: 1; } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes glow { 0%, 100% { filter: none; } 50% { filter: brightness(1.5) drop-shadow(0 0 18px currentColor); } }
@keyframes flash { from { opacity: .95; } to { opacity: 0; } }
@keyframes shake { 0%, 100% { translate: 0 0; } 20% { translate: -14px 6px; } 40% { translate: 12px -8px; }
  60% { translate: -8px 4px; } 80% { translate: 6px -2px; } }
#flash { position: fixed; inset: 0; background: #fff; z-index: 99; pointer-events: none; }
</style>"""

ANIM_JS = """([steps, flashOn]) => {
  const done = new Set();
  for (const [sel, name, start, dur, stagger] of steps) {
    [...document.querySelectorAll(sel)].filter(el => !done.has(el)).forEach((el, i) => {
      done.add(el);
      const t0 = getComputedStyle(el).transform;
      el.style.setProperty('--t0', t0 === 'none' ? 'translate(0)' : t0);
      const anim = name === 'slideAlt' ? (i % 2 ? 'slideR' : 'slideL') : name;
      el.style.animation = `${anim} ${dur}s cubic-bezier(.2,.9,.3,1.2) ${start + i * stagger}s both`;
    });
  }
  if (flashOn) {
    const flash = document.createElement('div'); flash.id = 'flash';
    flash.style.animation = 'flash .35s ease-out 0s both'; document.body.appendChild(flash);
  }
  const main = document.getElementById('main');
  if (main) main.style.animation = 'shake .3s linear 1.55s both';   // the stamp "hits" the poster
  document.getAnimations().forEach(a => a.pause());
}"""

BRAND_STEPS = [
    [".hl .hi", "glow", 0.3, 0.7, 0],   # stays visible, only lights up for a moment
    [".badge", "slam", 0.25, 0.4, 0],
    [".tile, .circ, .note, .stat, .bx, .st, .ar, .core, .rd, .hang, .pz, .tier, .coach, .sgn, .page, .fr, .kite, .set, .bl, .katori, .sb, .memo, .stp", "popIn", 0.45, 0.35, 0.15],
    [".rcard, .col, .step, .num-row, .sp, .ticket, .brow, .tab, .nrow, .strip-row, .tvrow, .cap, .cpanel, .key, .sign, .msg, .gl, .cl, .au, .hn, .mg, .pc, .pf, .ln", "slideAlt", 0.45, 0.35, 0.12],
    [".foot", "fadeIn", 1.1, 0.3, 0],
]


def _capture_intro(page, frames_dir: Path, seconds: float, fps: int, steps: list | None = None,
                   flash: bool = True) -> None:
    """Screenshot the intro animation frame by frame (deterministic, no screen recording)."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    page.add_style_tag(content=ANIM_CSS.removeprefix("<style>").removesuffix("</style>"))
    page.evaluate(ANIM_JS, [steps or ANIM_STEPS, flash])
    for n in range(int(seconds * fps)):
        page.evaluate("t => document.getAnimations().forEach(a => a.currentTime = t)", n * 1000 / fps)
        page.screenshot(path=str(frames_dir / f"f{n:04d}.jpg"), type="jpeg", quality=92)


FONT_FILES = {
    brand.FONT: ("baloo-bhai-2", (600, 700, 800)),
    brand.BODY_FONT: ("hind-vadodara", (600, 700)),
}
# the same designs' Devanagari cuts (Baloo 2, Hind) for the Hindi edition
DEVANAGARI_FILES = {
    brand.FONT: ("baloo-2", (600, 700, 800)),
    brand.BODY_FONT: ("hind", (600, 700)),
}


@cache
def font_css() -> str:
    """@font-face rules with the bundled fonts as data URLs (no network needed while rendering)."""
    rules = []
    # Hindi: Devanagari faces under the same family names, declared first so the Latin files win for Latin text
    for family, (stem, weights) in DEVANAGARI_FILES.items():
        for w in weights:
            path = ASSETS / "fonts" / f"{stem}-devanagari-{w}-normal.woff2"
            if path.exists():
                data = base64.b64encode(path.read_bytes()).decode()
                rules.append(f"@font-face {{ font-family: '{family}'; font-weight: {w}; font-display: block; "
                             f"unicode-range: U+0900-097F, U+1CD0-1CF9, U+200C-200D, U+20A8, U+20B9, U+25CC, U+A830-A839, U+A8E0-A8FF; "
                             f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")
    for family, (stem, weights) in FONT_FILES.items():
        for w in weights:
            for subset in ("latin", "latin-ext", "gujarati"):
                path = ASSETS / "fonts" / f"{stem}-{subset}-{w}-normal.woff2"
                if path.exists():
                    data = base64.b64encode(path.read_bytes()).decode()
                    rules.append(f"@font-face {{ font-family: '{family}'; font-weight: {w}; font-display: block; "
                                 f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")
    return "\n".join(rules)


def render_brand(story, out_path: Path, intro_dir: Path | None, *, date: str, handle: str, row_style: str | None,
                 scene_url: str | None = None, fps: int = 30, intro_seconds: float = 3.4) -> Path:
    """Card PNG for the story; with intro_dir also the intro frames f0000.jpg ... in that folder."""
    page_html = brand.brand_page(story, date, handle, None, scene_url, row_style)
    page_html = page_html.replace("<style>", f"<style>{font_css()}\n", 1)
    (out_path.parent / "card.html").write_text(page_html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path())
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.set_content(page_html, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        if not page.evaluate(brand.FIT):
            print("   Warning: some poster text is too long and may be cut off.")
        page.screenshot(path=str(out_path))
        if intro_dir:
            _capture_intro(page, intro_dir, intro_seconds, fps, BRAND_STEPS, flash=False)
        browser.close()
    return out_path
