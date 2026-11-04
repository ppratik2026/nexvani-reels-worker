"""The data one reel needs, in the shape the brand poster expects (see brand.py)."""
from dataclasses import dataclass, field


@dataclass
class Story:
    category: str               # category slug, picks the colour look
    category_label: str         # shown in the chip at the top
    headline: str
    highlight: str = ""         # word or number of the headline printed in the accent colour
    summary: str = ""           # "What happened?" box
    subheadline: str = ""
    facts: list = field(default_factory=list)    # [{"label", "value"}]; the first short number becomes the badge
    points: list = field(default_factory=list)   # extra short lines for the three rows
    visual: str = ""            # "", "compare", "reasons"
    compare: dict = field(default_factory=dict)  # before / after / change / direction
    rows: list = field(default_factory=list)
    reasons: list = field(default_factory=list)
    mood: str = ""              # breaking / money / info / happy: picks the music
    scene: str = ""             # drawn cartoon place (scenes.py)
    props: list = field(default_factory=list)    # up to three icon names placed in the scene
    imageQueries: list = field(default_factory=list)  # search terms for a real photo (website poster)
    source_name: str = ""
    style: dict = field(default_factory=dict)    # how the reel looked (row style, music...), reported back

    @classmethod
    def from_script(cls, script: dict, category: str, category_label: str, source_name: str) -> "Story":
        known = set(cls.__dataclass_fields__)
        data = {k: v for k, v in (script or {}).items() if k in known}
        return cls(**{**data, "category": category, "category_label": category_label, "source_name": source_name})
