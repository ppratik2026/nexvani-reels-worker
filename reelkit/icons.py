"""3D icons for the cards (Microsoft Fluent Emoji 3D, MIT licence, stored in assets/icons)."""
import base64
import re
from functools import cache

from .paths import ASSETS

ICON_DIR = ASSETS / "icons"

# Gujarati / English words -> icon, checked in order (first match wins)
RULES = [
    # English news words (NexVani Media), checked first
    (r"\bAI\b|artificial intelligence|chip|semiconductor|software|tech|cyber|internet|smartphone|app\b|robot", "phone"),
    (r"space|rocket|satellite|launch|orbit|telescope|scien|research|discover", "bulb"),
    (r"football|soccer|olympic|tennis|marathon|championship|world cup|tournament|match", "trophy"),
    (r"film|movie|music|concert|festival|award|streaming|celebrit", "star"),
    (r"climate|emission|carbon|wind|solar|heatwave|glacier|drought", "sun"),
    (r"war|ceasefire|peace talks|troops|missile|attack|conflict", "alert"),
    (r"summit|treaty|diplomat|talks|alliance|\bUN\b|united nations|G20|NATO", "handshake"),
    (r"stock|market|shares|econom|inflation|interest rate|central bank|GDP|trade|tariff", "chart_up"),
    (r"ધરપકડ|આરોપી|પોલીસ|ગુનો|ચોરી|arrest|police|crime", "police"),
    (r"અકસ્માત|accident|ઇમરજન્સી|ambulance", "ambulance"),
    (r"આગ|fire", "fire"),
    (r"એલર્ટ|ચેતવણી|alert|warning|સાવચેત", "warning"),
    (r"વરસાદ|માવઠ|rain|monsoon", "rain"), (r"વાવાઝોડ|તોફાન|storm|cyclone", "storm"), (r"ગરમી|heat|તાપમાન", "sun"),
    (r"પાણી|water|ડેમ|નર્મદા", "water"),
    (r"વીજ|લાઈટ|વીજળી|power|electric", "power"),
    (r"ઘટાડ|ઘટ્ય|ઘટશે|ઘટી|fall|drop|down", "chart_down"),
    (r"વધાર|વધ્ય|વધશે|વધી|rise|hike|increase", "chart_up"),
    (r"સોનુ|સોનાન|ચાંદી|gold|silver", "gold"),
    (r"₹|રૂ\.|રૂપિયા|ભાવ|કિંમત|પગાર|ભથ્થ|પેન્શન|રિફંડ|ફી(?![\u0A80-\u0AFF])|refund|price|fee|salary|pension|\bDA\b", "coin"),
    (r"બેંક|લોન|વ્યાજ|bank|loan|interest", "bank"),
    (r"પેટ્રોલ|ડીઝલ|CNG|ગેસ|fuel|petrol", "fuel"),
    (r"ખેડૂત|પાક|ખેતી|farmer|crop", "farm"),
    (r"પરીક્ષા|ધોરણ|વિદ્યાર્થી|પરિણામ|exam|result|student|GSEB", "exam"), (r"શાળા|સ્કૂલ|school", "school"),
    (r"હોસ્પિટલ|દર્દી|આરોગ્ય|hospital|health", "hospital"), (r"રસી|દવા|vaccine|medicine", "medicine"),
    (r"નોકરી|ભરતી|job|recruit", "job"), (r"કોર્ટ|ચુકાદ|કાયદ|court|law", "law"),
    (r"ચૂંટણી|મતદાન|election|vote", "vote"),
    (r"બસ|bus|ST ", "bus"), (r"ટ્રેન|રેલ|train|rail", "train"), (r"ફ્લાઇટ|એરપોર્ટ|flight|airport", "plane"),
    # કાર(?!્): not the "કાર્" of કાર્યક્રમ / કાર્યવાહી
    (r"રસ્તો|રોડ|હાઇવે|બ્રિજ|road|highway|bridge", "road"), (r"વાહન|કાર(?!\u0acd)|ગાડી|\bcar\b|vehicle", "car"),
    (r"ઘર|મકાન|આવાસ|house|housing", "house"), (r"ઉદ્યોગ|ફેક્ટરી|કંપની|industr|factory", "factory"),
    (r"વિશ્વ|વૈશ્વિક|દેશ|global|world|international|અમેરિકા", "globe"),
    (r"મેડલ|જીત|ગોલ્ડ મેડલ|medal|winner", "medal"), (r"એવોર્ડ|સન્માન|award|trophy", "trophy"),
    (r"ઉજવણી|તહેવાર|ઉત્સવ|દિવાળી|celebrat|festival", "party"), (r"મંદિર|temple|દર્શન", "temple"),
    (r"ક્રિકેટ|cricket", "cricket"), (r"મોબાઈલ|ફોન|ઓનલાઈન|app|online|phone", "phone"),
    (r"કાર્ડ|આધાર|ઓળખ|લાયસન્સ|card|licen", "id"),
    (r"તારીખ|દિવસ|જાન્યુઆરી|ફેબ્રુઆરી|માર્ચ|એપ્રિલ|જૂન|જુલાઈ|ઓગસ્ટ|સપ્ટેમ્બર|ઓક્ટોબર|નવેમ્બર|ડિસેમ્બર|date|day", "calendar"),
    (r"વાગ્યા|સમય|કલાક|time|hour", "clock"), (r"મુદત|સુધી|deadline", "hourglass"),
    (r"જિલ્લ|શહેર|ગામ|સ્થળ|ઝોન|વિસ્તાર|place|city|zone", "pin"),
    (r"સરકાર|યોજના|નિર્ણય|મંત્રી|government|scheme|minister", "govt"),
    (r"નેતા|પ્રમુખ|અધ્યક્ષ|મુખ્યમંત્રી|વડાપ્રધાન|leader|president", "people"),
    (r"કાર્યક્રમ|જયંતિ|સભા|રેલી|સંમેલન|event|rally", "megaphone"),
    (r"લોકો|નાગરિક|પરિવાર|people|citizen", "people"), (r"તપાસ|investigat", "magnifier"),
    (r"બેઠક|કરાર|સમજૂતી|meeting|agreement", "handshake"), (r"જાહેર|જાહેરાત|announce", "megaphone"),
    (r"નિયમ|પરિપત્ર|હુકમ|rule|order|circular", "document"),
]


def available() -> set[str]:
    return {p.stem for p in ICON_DIR.glob("*.png")}


def icon_key(text: str, fallback: str = "pin") -> str:
    """Icon that fits the text."""
    for pattern, key in RULES:
        # a Gujarati word must start the match (not "કાર" inside "મલ્લિકાર્જુન")
        if re.search(rf"(?<![\u0A80-\u0AFF])(?:{pattern})", text or "", re.I):
            return key
    return fallback


@cache
def icon_url(key: str) -> str:
    """The icon as a data URL (the cards are rendered offline); an unknown key gets the pin."""
    path = ICON_DIR / f"{key}.png"
    if not path.exists():
        path = ICON_DIR / "pin.png"
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def icon_img(key_or_text: str, cls: str = "ic") -> str:
    """<img> for an icon key, or for the icon that fits a piece of text."""
    key = key_or_text if key_or_text in available() else icon_key(key_or_text)
    return f'<img class="{cls}" src="{icon_url(key)}" alt="">'
