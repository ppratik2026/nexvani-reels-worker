"""Small text helpers used by the brand poster (from InstagramFacebookAutomation/src/designs.py)."""
import html
import re

esc = html.escape


def highlight_numbers(text: str) -> str:
    """Escape text and put words with digits (times, amounts, dates) in the accent colour."""
    return re.sub(r"(\S*[\d૦-૯]\S*)", r'<span class="num">\1</span>', esc(text))


MOODS = ("breaking", "money", "info", "happy")


def mood_of(story) -> str:
    """The script's mood, or a guess from the category and the numbers in the story."""
    if story.mood in MOODS:
        return story.mood
    if story.category in ("politics", "world", "crime"):
        return "breaking"
    text = " ".join([story.headline, story.summary] + [f["value"] for f in story.facts])
    return "money" if re.search(r"[$€£₹]|\bprice|\brate|\bbillion|\bmillion", text, re.I) else "info"
