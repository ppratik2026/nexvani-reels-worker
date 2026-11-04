"""Flat cartoon scenes drawn in code (SVG): always available and free, used when no image AI is available.

A scene is a place (airport, stadium, assembly, rally stage, market, ...) with up to three of the story's
objects (3D icons) placed in it, e.g. the airport with a plane, suitcases and a clock. No text and no faces.
"""
import base64
import random
from pathlib import Path

from .icons import ICON_DIR, available

W, H = 1536, 1024


def _sky(top: str, bottom: str) -> str:
    return (f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></linearGradient></defs><rect width="{W}" height="{H}" fill="url(#sky)"/>')


def _clouds(color: str = "#fff", opacity: float = .9) -> str:
    return (f'<g fill="{color}" opacity="{opacity}"><ellipse cx="260" cy="170" rx="130" ry="42"/><ellipse cx="350" cy="148" rx="95" ry="46"/>'
            f'<ellipse cx="980" cy="120" rx="120" ry="38"/><ellipse cx="1060" cy="104" rx="80" ry="38"/></g>')


def _windows(x: int, y: int, cols: int, rows: int, w: int, h: int, gap: int, color: str) -> str:
    return "".join(f'<rect x="{x + c * (w + gap)}" y="{y + r * (h + gap)}" width="{w}" height="{h}" rx="6" fill="{color}"/>'
                   for c in range(cols) for r in range(rows))


def _crowd(y: int, n: int = 46, r: int = 13) -> str:
    colors = ["#f87171", "#fbbf24", "#60a5fa", "#34d399", "#f472b6", "#a78bfa"]
    return "".join(f'<circle cx="{20 + i * W // n}" cy="{y + (i % 3) * 14}" r="{r}" fill="{colors[i % 6]}"/>' for i in range(n))


def _skyline(y: int, color: str) -> str:
    rnd = random.Random(7)
    out, x = "", 0
    while x < W:
        w, h = rnd.randint(70, 150), rnd.randint(120, 320)
        out += f'<rect x="{x}" y="{y - h}" width="{w}" height="{h}" fill="{color}"/>'
        x += w + rnd.randint(4, 18)
    return out


# scene -> (svg body, three prop slots (x, y, width, rotation), default props)
def _airport():
    body = (_sky("#ff9a5a", "#fff1d6") + '<circle cx="1230" cy="220" r="105" fill="#fff3b0"/>' + _clouds()
            + '<rect x="80" y="430" width="900" height="290" rx="30" fill="#2f4b7c"/><rect x="80" y="430" width="900" height="60" rx="30" fill="#1d3461"/>'
            + _windows(110, 515, 9, 1, 70, 150, 25, "#9ad0ff")
            + '<rect x="1040" y="250" width="70" height="470" fill="#3d5a80"/><rect x="990" y="200" width="170" height="90" rx="20" fill="#1d3461"/>'
            + '<rect x="1005" y="215" width="140" height="55" rx="12" fill="#9ad0ff"/><rect x="0" y="720" width="1536" height="304" fill="#4a4e69"/>'
            + "".join(f'<rect x="{40 + i * 190}" y="860" width="110" height="18" rx="9" fill="#fff"/>' for i in range(8)))
    return body, [(300, 120, 520, -12), (500, 680, 190, 0), (1180, 520, 170, 0)], ["plane", "job", "clock"]


def _stadium():
    body = (_sky("#1e3a8a", "#60a5fa") + '<g fill="#fde68a"><circle cx="200" cy="120" r="40"/><circle cx="1330" cy="110" r="40"/></g>'
            + '<g stroke="#e5e7eb" stroke-width="10"><line x1="200" y1="120" x2="200" y2="380"/><line x1="1330" y1="110" x2="1330" y2="380"/></g>'
            + '<path d="M0 420 Q768 250 1536 420 L1536 560 L0 560 Z" fill="#334155"/>' + _crowd(440)
            + '<ellipse cx="768" cy="880" rx="900" ry="380" fill="#22c55e"/><ellipse cx="768" cy="880" rx="700" ry="280" fill="#16a34a"/>'
            + '<rect x="690" y="580" width="156" height="420" rx="10" fill="#e7c98b"/>')
    return body, [(560, 600, 400, 0), (1060, 560, 290, 0), (240, 600, 250, -8)], ["cricket", "trophy", "medal"]


def _government():
    body = (_sky("#7dd3fc", "#e0f2fe") + _clouds() + '<rect x="0" y="760" width="1536" height="264" fill="#84cc16"/>'
            + '<rect x="0" y="740" width="1536" height="40" fill="#d6d3d1"/>'
            + '<path d="M468 330 Q768 120 1068 330 Z" fill="#f5f5f4"/><rect x="440" y="330" width="656" height="60" fill="#e7e5e4"/>'
            + '<rect x="400" y="390" width="736" height="360" fill="#fafaf9"/>'
            + "".join(f'<rect x="{430 + i * 76}" y="410" width="34" height="330" fill="#d6d3d1"/>' for i in range(10))
            + '<rect x="380" y="730" width="776" height="30" fill="#a8a29e"/>'
            + '<g><rect x="760" y="70" width="8" height="120" fill="#57534e"/><rect x="768" y="70" width="90" height="60" fill="#1e40af"/>'
            # a plain flag, not a real country's: NexVani covers every country
            + '<circle cx="813" cy="100" r="13" fill="#fff"/></g>')
    return body, [(90, 600, 260, 0), (1180, 600, 260, 0), (640, 790, 230, 0)], ["megaphone", "document", "handshake"]


def _rally():
    body = (_sky("#f97316", "#fde68a") + '<rect x="0" y="560" width="1536" height="464" fill="#78350f"/>'
            + '<rect x="330" y="420" width="876" height="200" fill="#7c2d12"/><rect x="330" y="400" width="876" height="30" fill="#fbbf24"/>'
            + "".join(f'<path d="M{330 + i * 73} 400 l36 60 l37 -60 Z" fill="{["#ef4444", "#facc15", "#3b82f6"][i % 3]}"/>' for i in range(12))
            + _crowd(720, 40, 22) + _crowd(800, 44, 24) + _crowd(890, 48, 26))
    return body, [(600, 150, 330, 0), (1100, 170, 250, 8), (190, 190, 240, -8)], ["megaphone", "vote", "handshake"]


def _police():
    body = (_sky("#0f172a", "#334155") + '<circle cx="1260" cy="160" r="70" fill="#e2e8f0"/>' + _skyline(700, "#1e293b")
            + _windows(60, 480, 14, 2, 26, 30, 80, "#fde047") + '<rect x="0" y="700" width="1536" height="324" fill="#374151"/>'
            + "".join(f'<rect x="{40 + i * 190}" y="850" width="110" height="16" rx="8" fill="#e5e7eb"/>' for i in range(8))
            + '<g fill="#f59e0b"><rect x="120" y="760" width="300" height="26" rx="6"/><rect x="140" y="786" width="14" height="70"/><rect x="386" y="786" width="14" height="70"/></g>'
            + '<ellipse cx="760" cy="420" rx="420" ry="220" fill="#3b82f6" opacity=".18"/><ellipse cx="1000" cy="420" rx="300" ry="180" fill="#ef4444" opacity=".15"/>')
    return body, [(520, 520, 520, 0), (1120, 520, 230, 0), (150, 520, 230, 0)], ["police", "siren", "magnifier"]


def _market():
    awn = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6"]
    body = (_sky("#fde68a", "#fff7ed") + '<rect x="0" y="700" width="1536" height="324" fill="#d6b48a"/>'
            + "".join(f'<rect x="{60 + i * 370}" y="380" width="320" height="330" fill="#fef3c7"/>'
                      f'<path d="M{50 + i * 370} 380 h340 l-20 -90 h-300 Z" fill="{awn[i]}"/>'
                      f'<rect x="{80 + i * 370}" y="560" width="280" height="40" fill="#92400e"/>' for i in range(4))
            + "".join(f'<circle cx="{110 + i * 52}" cy="545" r="20" fill="{["#f97316", "#84cc16", "#ef4444"][i % 3]}"/>' for i in range(26)))
    return body, [(150, 690, 280, 0), (620, 660, 260, 0), (1080, 680, 260, 0)], ["cart", "coin", "chart_up"]


def _farm():
    body = (_sky("#fbbf24", "#fef3c7") + '<circle cx="1230" cy="200" r="120" fill="#fde047"/>'
            + '<path d="M0 520 Q400 440 800 520 T1536 500 V1024 H0 Z" fill="#a3a33a"/>'
            + "".join(f'<path d="M{-200 + i * 160} 1024 L{560 + i * 30} 560" stroke="#7c6f1d" stroke-width="16"/>' for i in range(14))
            + '<rect x="180" y="380" width="200" height="170" fill="#b45309"/><path d="M160 390 L280 300 L400 390 Z" fill="#7f1d1d"/>')
    return body, [(560, 560, 380, 0), (1080, 600, 260, 0), (120, 620, 230, 0)], ["tractor", "farm", "water"]


def _rain():
    body = (_sky("#475569", "#94a3b8") + _clouds("#334155", 1) + _skyline(720, "#1f2937")
            + '<rect x="0" y="720" width="1536" height="304" fill="#2563eb" opacity=".75"/>'
            + "".join(f'<line x1="{(i * 97) % W}" y1="{(i * 53) % 650}" x2="{(i * 97) % W - 18}" y2="{(i * 53) % 650 + 50}" stroke="#bfdbfe" stroke-width="5"/>' for i in range(70)))
    return body, [(560, 140, 380, 0), (1100, 520, 250, 0), (180, 520, 250, 0)], ["storm", "warning", "water"]


def _city():
    body = (_sky("#38bdf8", "#e0f2fe") + _clouds() + _skyline(720, "#64748b") + _windows(40, 520, 22, 2, 22, 26, 46, "#e2e8f0")
            + '<rect x="0" y="720" width="1536" height="304" fill="#4b5563"/>'
            + "".join(f'<rect x="{40 + i * 190}" y="860" width="110" height="16" rx="8" fill="#fff"/>' for i in range(8)))
    return body, [(540, 600, 400, 0), (1060, 640, 300, 0), (130, 640, 280, 0)], ["bus", "car", "road"]


def _school():
    body = (_sky("#86efac", "#f0fdf4") + _clouds() + '<rect x="0" y="760" width="1536" height="264" fill="#65a30d"/>'
            + '<rect x="380" y="380" width="780" height="380" fill="#fca5a5"/><path d="M340 390 L770 200 L1200 390 Z" fill="#b91c1c"/>'
            + _windows(420, 440, 6, 2, 90, 90, 36, "#e0f2fe") + '<rect x="720" y="620" width="100" height="140" fill="#7c2d12"/>')
    return body, [(80, 600, 280, 0), (1180, 600, 260, 0), (640, 800, 230, 0)], ["exam", "document", "star"]


def _hospital():
    body = (_sky("#a5f3fc", "#ecfeff") + _clouds() + '<rect x="0" y="760" width="1536" height="264" fill="#cbd5e1"/>'
            + '<rect x="420" y="300" width="700" height="460" fill="#f8fafc"/>' + _windows(460, 360, 6, 3, 80, 70, 30, "#bae6fd")
            + '<rect x="725" y="200" width="90" height="250" fill="#ef4444"/><rect x="645" y="280" width="250" height="90" fill="#ef4444"/>')
    return body, [(80, 580, 300, 0), (1160, 600, 260, 0), (650, 800, 220, 0)], ["ambulance", "medicine", "doctor"]


def _power():
    body = (_sky("#1e1b4b", "#6366f1") + '<rect x="0" y="760" width="1536" height="264" fill="#1f2937"/>'
            + "".join(f'<path d="M{200 + i * 560} 760 L{260 + i * 560} 260 L{320 + i * 560} 760 M{170 + i * 560} 360 H{350 + i * 560} M{150 + i * 560} 460 H{370 + i * 560}" stroke="#9ca3af" stroke-width="12" fill="none"/>' for i in range(3))
            + '<path d="M260 300 Q540 380 820 300 T1380 300" stroke="#e5e7eb" stroke-width="5" fill="none"/>')
    return body, [(560, 380, 380, 0), (1080, 560, 260, 0), (120, 560, 260, 0)], ["bulb", "power", "factory"]


def _court():
    body = (_sky("#cbd5e1", "#f1f5f9") + '<rect x="0" y="780" width="1536" height="244" fill="#94a3b8"/>'
            + '<path d="M380 360 L768 180 L1156 360 Z" fill="#e2e8f0"/><rect x="380" y="360" width="776" height="40" fill="#cbd5e1"/>'
            + "".join(f'<rect x="{420 + i * 120}" y="400" width="56" height="360" fill="#f1f5f9"/>' for i in range(7))
            + '<rect x="360" y="760" width="816" height="30" fill="#64748b"/>')
    return body, [(640, 420, 260, 0), (1150, 600, 250, 0), (130, 600, 250, 0)], ["law", "document", "magnifier"]


def _finance():
    body = (_sky("#064e3b", "#10b981") + _skyline(760, "#065f46") + '<rect x="0" y="760" width="1536" height="264" fill="#022c22"/>'
            + '<path d="M100 700 L400 560 L650 620 L950 400 L1250 460 L1450 280" stroke="#fde047" stroke-width="18" fill="none" stroke-linecap="round"/>')
    return body, [(560, 520, 360, 0), (1060, 560, 300, 0), (140, 600, 260, 0)], ["bank", "coin", "chart_up"]


def _festival():
    body = (_sky("#312e81", "#7c3aed") + '<rect x="0" y="760" width="1536" height="264" fill="#3b0764"/>'
            + "".join(f'<circle cx="{(i * 131) % W}" cy="{80 + (i * 71) % 400}" r="{4 + i % 4}" fill="#fde68a"/>' for i in range(60))
            + '<path d="M0 220 Q384 300 768 220 T1536 220" stroke="#fbbf24" stroke-width="4" fill="none"/>'
            + "".join(f'<circle cx="{40 + i * 96}" cy="{245 + (i % 2) * 12}" r="12" fill="{["#f87171", "#fde047", "#34d399"][i % 3]}"/>' for i in range(16)))
    return body, [(560, 480, 400, 0), (1080, 560, 280, 0), (160, 560, 280, 0)], ["party", "star", "temple"]


SCENES = {
    "airport": _airport, "stadium": _stadium, "government": _government, "rally": _rally, "police": _police,
    "market": _market, "farm": _farm, "rain": _rain, "city": _city, "school": _school, "hospital": _hospital,
    "power": _power, "court": _court, "finance": _finance, "festival": _festival,
}

# when the AI gives no scene: the category's usual place
BY_CATEGORY = {"government": "government", "politics": "rally", "crime": "police", "trending": "city",
               "good_news": "festival", "world": "city", "india": "city", "crypto": "finance", "stock-market": "finance", "share-market": "finance", "markets": "finance", "business": "finance", "technology": "city",
               "science": "school", "health": "hospital", "sports": "stadium", "climate": "rain",
               "entertainment": "festival"}


def _icon(key: str) -> str:
    return "data:image/png;base64," + base64.b64encode((ICON_DIR / f"{key}.png").read_bytes()).decode()


def scene_html(scene: str, props: list[str] | None = None) -> str:
    body, slots, defaults = SCENES.get(scene, SCENES["city"])()
    keys = [p for p in (props or []) if p in available()][:3]
    keys += [d for d in defaults if d not in keys][:3 - len(keys)]
    # the poster shows the middle band of the scene (its top and bottom fade out): keep every object inside it,
    # and away from the left and right edges
    def place(x, y, w):
        return min(max(x, 140), W - 140 - w), min(max(y, 200), 760 - w)
    imgs = "".join(
        f'<img src="{_icon(k)}" style="position:absolute;left:{place(x, y, w)[0]}px;top:{place(x, y, w)[1]}px;width:{w}px;'
        f'transform:rotate({r}deg);filter:drop-shadow(0 18px 14px rgba(0,0,0,.35))">' for k, (x, y, w, r) in zip(keys, slots))
    return (f'<html><body style="margin:0;width:{W}px;height:{H}px;position:relative;overflow:hidden">'
            f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">{body}</svg>{imgs}</body></html>')


def draw_scene(scene: str, props: list[str] | None, out_path: Path) -> Path:
    """Render the scene to a PNG (1536x1024)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        from .paths import chromium_path
        browser = p.chromium.launch(executable_path=chromium_path())
        page = browser.new_page(viewport={"width": W, "height": H})
        page.set_content(scene_html(scene, props))
        page.screenshot(path=str(out_path))
        browser.close()
    print(f"Background: drawn cartoon scene '{scene}' with {', '.join(props or []) or 'default objects'}")
    return out_path
