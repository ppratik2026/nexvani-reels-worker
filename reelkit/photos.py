"""A real, freely licensed photo for a story from Wikimedia Commons (no API key needed).

Only licences that allow use on a commercial news site are taken (public domain, CC0, CC BY, CC BY-SA), and the
credit the licence asks for is returned with the photo, to print on the poster and on the website.
"""
import html
import re

import requests

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks every client to name itself with a contact URL.
HEADERS = {"User-Agent": "NexVaniMediaPosters/1.0 (https://nexvanimedia.com)"}

FREE = re.compile(r"^(cc0|public domain|pd\b|pd-|cc[ -]by(-sa)?[ -]\d)", re.I)
NOT_FREE = re.compile(r"\bnc\b|\bnd\b|non-?commercial|no ?deriv|fair use", re.I)

# Photos of identifiable people are skipped: next to a story they would suggest the people in them are its
# subjects. Places, buildings, objects and maps only.
PEOPLE = re.compile(
    r"portrait|people|person|persons|\bm[ae]n\b|wom[ae]n|girl|boy|child|kids|crowd|audience|fans|soldier|troops|"
    r"marine|seal|officer|police ?m|player|athlete|runner|team|squad|minister|president|senator|mayor|governor|"
    r"politician|delegat|official|ceremony|meeting|visit|speech|speaks|speaking|interview|press conference|"
    r"protest|rally|march|wedding|family|selfie|students|workers|members|participat|competitor|winner|award|"
    r"celebrat|\b(mr|mrs|ms|dr)\b|\bwith\b",
    re.I,
)

# Not photographs: scans, printed pages, artwork and graphics look wrong behind a news headline.
NOT_PHOTO = re.compile(
    r"scan|page|book|magazine|newspaper|leaflet|flyer|poster|banner|logo|emblem|graphic|infographic|diagram|"
    r"drawing|engraving|painting|illustration|lithograph|postcard|stamp|coin|banknote|cartoon|render|screenshot|"
    r"collage|\.svg|\.png$",
    re.I,
)

STOP = {"the", "and", "of", "in", "at", "on", "for", "with", "view", "building", "street", "city", "aerial", "photo"}


def _match(query: str, text: str) -> float:
    """Share of the query's main words found in the photo's title and description."""
    words = [w for w in re.findall(r"[\w-]+", query.lower()) if len(w) > 2 and w not in STOP]
    if not words:
        return 0.0
    text = text.lower()
    # a short stem, so "Russian" finds "Russia" and "refineries" finds "refinery"
    return sum((w[:-2] if len(w) > 5 else w) in text for w in words) / len(words)


# Stories where a photo could hurt (deaths, sexual violence, accidents, abuse): they get the drawn scene.
SENSITIVE = re.compile(
    r"kill|dead|death|deadly|died|dies|fatal|rape|sexual|assault|abuse|massacre|murder|suicide|corpse|body found|"
    r"crash|victim|injur|hostage|terror|soil|child",
    re.I,
)


def sensitive(text: str) -> bool:
    return bool(SENSITIVE.search(text or ""))


def _strip(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def _search(query: str) -> list[dict]:
    res = requests.get(API, headers=HEADERS, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": 20,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600,
    })
    res.raise_for_status()
    pages = sorted(res.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    found = []
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licence = _strip(meta.get("LicenseShortName", {}).get("value", ""))
        w, h = info.get("width", 0), info.get("height", 0)
        if info.get("mime") not in ("image/jpeg", "image/png") or w < 1200 or not h or not 1.2 <= w / h <= 2.4:
            continue
        if not FREE.search(licence) or NOT_FREE.search(licence):
            continue
        described = " ".join([p.get("title", ""), _strip(meta.get("ImageDescription", {}).get("value", ""))[:300],
                              _strip(meta.get("Categories", {}).get("value", ""))])
        if PEOPLE.search(described) or NOT_PHOTO.search(p.get("title", "")):
            continue
        # the photo must be about the search terms (most of their main words in its title/description)
        if _match(query, described) < 0.6:
            continue
        artist = _strip(meta.get("Artist", {}).get("value", "")) or "Unknown"
        found.append({
            "url": info.get("thumburl") or info.get("url"),
            "page": info.get("descriptionurl", ""),
            "title": p.get("title", ""),
            "credit": f"Photo: {artist[:40]} / Wikimedia Commons, {licence}",
        })
    return found


def _get(url: str) -> requests.Response | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        return r if r.ok and len(r.content) > 10_000 else None
    except requests.RequestException:
        return None


def find_photo(queries: list[str], story_text: str = "", check=None, max_checks: int = 6) -> dict | None:
    """The first suitable photo for the story's search terms (url, credit, page, bytes), or None: then the poster
    uses the drawn scene. Sensitive stories never get a photo, and no generic stand-in is used when nothing fits.

    check(image_bytes, mime) -> (ok, reason): a final look at each candidate (Gemini, through the website); with a
    checker, at most max_checks candidates are looked at and only an approved one is used."""
    # Without a checker, sensitive stories get no photo; with one, Gemini keeps people, victims and damage out.
    if sensitive(story_text) and not check:
        print("   Sensitive story: drawn scene instead of a photo")
        return None
    checks = 0
    for q in queries:
        q = (q or "").strip()
        if not q:
            continue
        try:
            hits = _search(q)
        except requests.RequestException as e:
            print(f"   Photo search failed for '{q}': {e}")
            continue
        for hit in hits[:3]:
            if check:
                if checks >= max_checks:
                    return None
                small = _get(re.sub(r"/\d+px-", "/640px-", hit["url"])) or _get(hit["url"])
                if not small:
                    continue
                checks += 1
                ok, reason = check(small.content, small.headers.get("content-type", "image/jpeg"))
                print(f"   {'Approved' if ok else 'Rejected'}: {hit['title']} ({reason})")
                if not ok:
                    continue
            img = _get(hit["url"])
            if img:
                print(f"   Photo for '{q}': {hit['title']} ({hit['credit']})")
                return {**hit, "query": q, "bytes": img.content, "mime": img.headers.get("content-type", "image/jpeg")}
    return None
