"""
pii_correlator.py - Cross-cultural PII pattern detection in passwords.

Identifies cognitive PII patterns embedded in passwords: names, dates,
phone fragments, sequential numbers, and hybrid combinations. Supports
multi-language name detection (EN, PT-BR, ES, FR, DE) to validate the
universal nature of cognitive bias in password creation.

Classification categories:
  - name_based: password contains a recognizable first name
  - date_based: password contains a date-like numeric pattern
  - keyword_based: password contains common dictionary words/patterns
  - hybrid: password contains both name and date/number components
  - sequential: password is a simple numeric/keyboard sequence
  - random_like: no detectable PII pattern

Author: Andre Henrique (@mrhenrike)
Version: 0.2.0
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

# Top first names per language (curated from census/civil registry data).
# Each list: ~200 names, lowercased, covering male+female common names.
# These are used for substring matching against password contents.

NAMES_EN: set[str] = {
    "james", "mary", "john", "patricia", "robert", "jennifer", "michael",
    "linda", "david", "elizabeth", "william", "barbara", "richard", "susan",
    "joseph", "jessica", "thomas", "sarah", "charles", "karen", "christopher",
    "lisa", "daniel", "nancy", "matthew", "betty", "anthony", "margaret",
    "mark", "sandra", "donald", "ashley", "steven", "kimberly", "paul",
    "emily", "andrew", "donna", "joshua", "michelle", "kenneth", "dorothy",
    "kevin", "carol", "brian", "amanda", "george", "melissa", "timothy",
    "deborah", "ronald", "stephanie", "edward", "rebecca", "jason", "sharon",
    "jeffrey", "laura", "ryan", "cynthia", "jacob", "kathleen", "gary",
    "amy", "nicholas", "angela", "eric", "shirley", "jonathan", "anna",
    "stephen", "brenda", "larry", "pamela", "justin", "emma", "scott",
    "nicole", "brandon", "helen", "benjamin", "samantha", "samuel", "katherine",
    "raymond", "christine", "gregory", "debra", "frank", "rachel", "alexander",
    "carolyn", "patrick", "janet", "jack", "catherine", "dennis", "maria",
    "jerry", "heather", "tyler", "diane", "aaron", "ruth", "jose",
    "julie", "adam", "olivia", "nathan", "joyce", "henry", "virginia",
    "peter", "victoria", "zachary", "kelly", "douglas", "lauren", "harold",
    "christina", "dylan", "joan", "jordan", "evelyn", "keith", "judith",
    "logan", "megan", "bruce", "andrea", "ralph", "cheryl", "roy",
    "hannah", "noah", "jacqueline", "ethan", "martha", "mason", "gloria",
    "luke", "teresa", "aiden", "ann", "harry", "sara", "hunter",
    "madison", "riley", "frances", "gabriel", "kathryn", "owen", "janice",
    "charlie", "jean", "caleb", "abigail", "connor", "alice", "adrian",
    "judy", "liam", "sophia", "elijah", "grace", "oliver",
    "amber", "max", "rose", "leo", "denise", "oscar", "marilyn",
}

NAMES_PT: set[str] = {
    "joao", "maria", "jose", "ana", "pedro", "patricia", "carlos",
    "fernanda", "lucas", "juliana", "gabriel", "amanda", "rafael",
    "bruna", "matheus", "camila", "bruno", "leticia", "daniel",
    "jessica", "gustavo", "larissa", "felipe", "mariana", "rodrigo",
    "beatriz", "thiago", "carolina", "leandro", "raquel", "marcos",
    "adriana", "andre", "cristiane", "diego", "tatiana", "eduardo",
    "vanessa", "marcelo", "renata", "antonio", "gabriela", "paulo",
    "daniela", "ricardo", "natalia", "fabio", "priscila", "vinicius",
    "aline", "henrique", "simone", "douglas", "viviane", "leonardo",
    "luciana", "guilherme", "alessandra", "fernando", "michele", "tiago",
    "sandra", "caio", "monique", "wellington", "eliane", "francisco",
    "katia", "anderson", "debora", "renan", "flavia", "samuel",
    "roberta", "arthur", "cintia", "miguel", "carla", "davi",
    "bianca", "enzo", "sabrina", "luiz", "luana", "claudio",
    "milena", "rogerio", "tania", "william", "solange", "igor",
    "rosana", "alex", "claudia", "victor", "silvana", "jorge",
    "ligia", "murilo", "sueli", "renato", "izabel", "caique",
    "valeria", "raul", "denise", "otavio", "marta", "bernardo",
    "vera", "heitor", "lucia", "valentina", "giovanna", "sofia",
    "helena", "alice", "laura", "manuela", "cecilia", "lorena",
    "isadora", "lara", "isabela", "livia", "marina", "rafaela",
}

NAMES_ES: set[str] = {
    "jose", "maria", "juan", "carmen", "luis", "ana", "carlos",
    "rosa", "miguel", "pilar", "angel", "laura", "francisco",
    "isabel", "antonio", "cristina", "david", "marta", "pedro",
    "elena", "javier", "lucia", "rafael", "paula", "fernando",
    "sara", "alejandro", "andrea", "manuel", "sofia", "pablo",
    "raquel", "jorge", "patricia", "daniel", "silvia", "sergio",
    "beatriz", "roberto", "sandra", "marcos", "nuria", "alberto",
    "irene", "raul", "alba", "enrique", "eva", "adrian",
    "natalia", "ivan", "rocio", "andres", "alicia", "victor",
    "ines", "mario", "olga", "oscar", "julia", "diego",
    "lorena", "ramon", "monica", "eduardo", "esther", "hector",
    "sonia", "hugo", "carolina", "jaime", "amparo", "gabriel",
    "lola", "ignacio", "lidia", "alvaro", "noelia", "ruben",
    "claudia", "tomas", "teresa", "martin", "encarnacion",
    "santiago", "consuelo", "rodrigo", "yolanda", "gonzalo", "blanca",
    "agustin", "susana", "nicolas", "mercedes", "emilio", "dolores",
    "mateo", "valentina", "samuel", "jimena", "guillermo", "camila",
}

NAMES_FR: set[str] = {
    "jean", "marie", "pierre", "nathalie", "michel", "isabelle",
    "philippe", "sylvie", "alain", "catherine", "patrick", "christine",
    "nicolas", "monique", "christophe", "valerie", "jacques", "veronique",
    "pascal", "sandrine", "laurent", "anne", "thierry", "sophie",
    "frederic", "dominique", "olivier", "brigitte", "francois", "patricia",
    "bruno", "corinne", "eric", "florence", "stephane", "laurence",
    "didier", "martine", "david", "pascale", "julien", "emilie",
    "alexandre", "caroline", "thomas", "virginie", "antoine", "aurelie",
    "romain", "delphine", "maxime", "julie", "sebastien", "celine",
    "guillaume", "karine", "vincent", "helene", "jerome", "stephanie",
    "mathieu", "laure", "benoit", "marine", "arnaud", "camille",
    "hugo", "charlotte", "louis", "margaux", "lucas", "lea",
    "gabriel", "manon", "emma", "chloe", "raphael", "alice",
    "nathan", "juliette", "clement", "clara", "paul", "sarah",
    "leo", "ines", "baptiste", "jeanne", "theo", "louise",
    "arthur", "lucie", "adam", "lola", "noel", "amelie",
    "etienne", "madeleine", "rene", "danielle", "serge", "lucienne",
}

NAMES_DE: set[str] = {
    "hans", "maria", "peter", "ursula", "michael", "monika",
    "thomas", "petra", "andreas", "sabine", "stefan", "andrea",
    "christian", "gabriele", "markus", "susanne", "daniel", "birgit",
    "matthias", "heike", "martin", "claudia", "frank", "martina",
    "klaus", "karin", "bernd", "christine", "jens", "angelika",
    "uwe", "brigitte", "dirk", "nicole", "torsten", "manuela",
    "oliver", "katrin", "sven", "stefanie", "alexander", "silke",
    "ralf", "anja", "tobias", "sandra", "jan", "julia",
    "patrick", "kathrin", "florian", "daniela", "sebastian", "melanie",
    "benjamin", "christina", "maximilian", "jennifer", "dennis", "nadine",
    "johannes", "anna", "felix", "sarah", "lukas", "laura",
    "leon", "lisa", "paul", "lena", "tim", "marie",
    "jonas", "sophie", "philipp", "emma", "niklas", "leonie",
    "moritz", "hannah", "david", "johanna", "simon", "katharina",
    "lars", "franziska", "marcel", "elke", "volker", "renate",
    "karl", "elisabeth", "heinz", "helga", "werner", "ingrid",
    "dieter", "gertraud", "helmut", "hildegard", "manfred", "elfriede",
    "walter", "irmgard", "kurt", "lieselotte", "otto", "margarete",
    "wolfgang", "erika", "friedrich", "gisela", "harald", "ilse",
}

ALL_NAMES: set[str] = NAMES_EN | NAMES_PT | NAMES_ES | NAMES_FR | NAMES_DE

# Pre-sorted by length (descending) for greedy matching
_SORTED_NAMES: list[str] = sorted(ALL_NAMES, key=len, reverse=True)

# Date patterns: DDMMYYYY, MMDDYYYY, YYYYMMDD, DDMM, MMDD, YYYY, YY
_DATE_FULL_RE = re.compile(
    r"(?:0[1-9]|[12]\d|3[01])(?:0[1-9]|1[0-2])(?:19[5-9]\d|20[0-2]\d)"  # DDMMYYYY
    r"|(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:19[5-9]\d|20[0-2]\d)"  # MMDDYYYY
    r"|(?:19[5-9]\d|20[0-2]\d)(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"  # YYYYMMDD
)

_DATE_SHORT_RE = re.compile(
    r"(?:0[1-9]|[12]\d|3[01])(?:0[1-9]|1[0-2])"  # DDMM
    r"|(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"  # MMDD
)

_YEAR_RE = re.compile(r"(?:19[5-9]\d|20[0-2]\d)")
_SHORT_YEAR_RE = re.compile(r"(?:[5-9]\d|0\d|1\d|2[0-6])")

_SEQUENCE_RE = re.compile(
    r"^(?:0123|1234|2345|3456|4567|5678|6789|12345|123456|1234567|12345678"
    r"|123456789|0987|9876|8765|7654|6543|5432|4321|abcdef|qwerty|asdf"
    r"|zxcv|qwer|1q2w3e|q1w2e3|abc123|111|222|333|444|555|666|777|888|999|000)$",
    re.IGNORECASE,
)

_PHONE_RE = re.compile(r"\d{7,11}")


@dataclass
class PIIMatch:
    """A detected PII pattern in a password."""
    category: str  # name_based, date_based, hybrid, sequential, keyword_based, random_like
    name_found: str | None = None
    name_lang: str | None = None
    date_found: str | None = None
    date_type: str | None = None
    confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CorpusStats:
    """Aggregate statistics from PII correlation over a password corpus."""
    total: int = 0
    name_based: int = 0
    date_based: int = 0
    hybrid: int = 0
    sequential: int = 0
    keyword_based: int = 0
    random_like: int = 0
    names_by_lang: dict[str, int] = field(default_factory=lambda: {
        "en": 0, "pt": 0, "es": 0, "fr": 0, "de": 0, "multi": 0,
    })
    date_types: dict[str, int] = field(default_factory=lambda: {
        "full_date": 0, "short_date": 0, "year_4": 0, "year_2": 0,
    })
    top_names: Counter = field(default_factory=Counter)
    top_years: Counter = field(default_factory=Counter)
    length_distribution: Counter = field(default_factory=Counter)

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "categories": {
                "name_based": self.name_based,
                "date_based": self.date_based,
                "hybrid": self.hybrid,
                "sequential": self.sequential,
                "keyword_based": self.keyword_based,
                "random_like": self.random_like,
            },
            "pii_detectable_pct": round(
                (self.name_based + self.date_based + self.hybrid) / max(self.total, 1) * 100, 2
            ),
            "names_by_lang": dict(self.names_by_lang),
            "date_types": dict(self.date_types),
            "top_names": dict(self.top_names.most_common(30)),
            "top_years": dict(self.top_years.most_common(20)),
            "length_distribution": dict(sorted(self.length_distribution.items())),
        }


def _detect_name(password: str) -> tuple[str | None, str | None]:
    """Find the longest matching name in the password (case-insensitive)."""
    pw_lower = password.lower()
    for name in _SORTED_NAMES:
        if len(name) < 3:
            continue
        if name in pw_lower:
            lang = "multi"
            if name in NAMES_EN:
                lang = "en"
            if name in NAMES_PT:
                lang = "pt" if lang == "multi" else "multi"
            if name in NAMES_ES:
                lang = "es" if lang == "multi" else "multi"
            if name in NAMES_FR:
                lang = "fr" if lang == "multi" else "multi"
            if name in NAMES_DE:
                lang = "de" if lang == "multi" else "multi"
            return name, lang
    return None, None


def _detect_date(password: str) -> tuple[str | None, str | None]:
    """Detect date-like patterns in the password."""
    m = _DATE_FULL_RE.search(password)
    if m:
        return m.group(), "full_date"
    m = _YEAR_RE.search(password)
    if m:
        return m.group(), "year_4"
    m = _DATE_SHORT_RE.search(password)
    if m and len(password) > len(m.group()) + 1:
        return m.group(), "short_date"
    digits_only = re.sub(r"[^0-9]", "", password)
    if len(digits_only) == 2:
        m2 = _SHORT_YEAR_RE.fullmatch(digits_only)
        if m2:
            return digits_only, "year_2"
    return None, None


def _name_lang_single(name: str) -> str:
    """Return the single most specific language for a name."""
    langs = []
    if name in NAMES_EN:
        langs.append("en")
    if name in NAMES_PT:
        langs.append("pt")
    if name in NAMES_ES:
        langs.append("es")
    if name in NAMES_FR:
        langs.append("fr")
    if name in NAMES_DE:
        langs.append("de")
    if len(langs) == 1:
        return langs[0]
    return "multi"


def correlate_password(password: str) -> PIIMatch:
    """Classify a single password by its PII content."""
    pw = password.strip()
    if not pw or len(pw) < 3:
        return PIIMatch(category="random_like", confidence=0.0)

    if _SEQUENCE_RE.match(pw):
        return PIIMatch(category="sequential", confidence=1.0)

    name, lang = _detect_name(pw)
    date_val, date_type = _detect_date(pw)

    if name and date_val:
        return PIIMatch(
            category="hybrid",
            name_found=name,
            name_lang=lang,
            date_found=date_val,
            date_type=date_type,
            confidence=0.9,
        )
    if name:
        return PIIMatch(
            category="name_based",
            name_found=name,
            name_lang=lang,
            confidence=0.7,
        )
    if date_val:
        return PIIMatch(
            category="date_based",
            date_found=date_val,
            date_type=date_type,
            confidence=0.6,
        )

    return PIIMatch(category="random_like", confidence=0.1)


def correlate_corpus(
    passwords: list[str] | None = None,
    filepath: str | None = None,
    max_lines: int = 0,
    progress_every: int = 500_000,
) -> CorpusStats:
    """Run PII correlation over a list or file of passwords.

    Args:
        passwords: In-memory list of passwords.
        filepath: Path to newline-delimited password file.
        max_lines: Max lines to process (0 = unlimited).
        progress_every: Print progress every N lines (0 = silent).

    Returns:
        CorpusStats with aggregate statistics.
    """
    stats = CorpusStats()

    def _process(pw: str) -> None:
        pw = pw.strip()
        if not pw:
            return
        stats.total += 1
        stats.length_distribution[len(pw)] += 1

        result = correlate_password(pw)
        cat = result.category

        if cat == "name_based":
            stats.name_based += 1
        elif cat == "date_based":
            stats.date_based += 1
        elif cat == "hybrid":
            stats.hybrid += 1
            stats.name_based += 1
            stats.date_based += 1
        elif cat == "sequential":
            stats.sequential += 1
        elif cat == "keyword_based":
            stats.keyword_based += 1
        else:
            stats.random_like += 1

        if result.name_found:
            lang = result.name_lang or "multi"
            stats.names_by_lang[lang] = stats.names_by_lang.get(lang, 0) + 1
            stats.top_names[result.name_found] += 1

        if result.date_found and result.date_type:
            stats.date_types[result.date_type] = stats.date_types.get(result.date_type, 0) + 1
            if result.date_type == "year_4":
                stats.top_years[result.date_found] += 1

    if passwords is not None:
        for pw in passwords:
            _process(pw)
            if max_lines and stats.total >= max_lines:
                break
    elif filepath:
        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                _process(line)
                if max_lines and stats.total >= max_lines:
                    break
    return stats
