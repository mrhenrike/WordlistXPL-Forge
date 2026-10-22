"""
diceware_engine.py - Diceware/passphrase generation engine.

Generates passphrase candidates using the diceware method and common
passphrase patterns. Supports EFF wordlists, custom dictionaries, and
multiple separator styles. Useful for predicting passphrase-style passwords
that follow the xkcd "correct horse battery staple" pattern.

Inspired by xkcdpass (1,434 stars) and passphraseme, with mutation
layers for real-world passphrase variations (capitalization, numbers
between words, special char separators, truncation).

Usage (as library):
    from wlf_modules.diceware_engine import generate_passphrases
    for pp in generate_passphrases(num_words=4, max_candidates=1000):
        print(pp)

Usage (CLI):
    wlf.py diceware --words 4 --separator "-" --capitalize
    wlf.py diceware --wordlist custom.txt --words 3

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import itertools
import logging
import random
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__info__ = {
    "name": "diceware_engine",
    "version": "1.0.0",
    "author": "Andre Henrique (@mrhenrike)",
    "description": "Diceware/passphrase generation and prediction engine",
    "category": "passphrase",
    "tags": ["diceware", "passphrase", "xkcdpass", "prediction"],
}

EFF_SHORT_WORDLIST: list[str] = [
    "acid", "acme", "aged", "also", "arch", "army", "atom", "aunt",
    "avid", "baby", "back", "bald", "band", "bank", "barn", "base",
    "bath", "bead", "bean", "bear", "beat", "beef", "bell", "belt",
    "bend", "bike", "bird", "bite", "blow", "blue", "blur", "boat",
    "body", "bold", "bolt", "bomb", "bone", "book", "bore", "boss",
    "bowl", "bulk", "bump", "burn", "busy", "buzz", "cafe", "cage",
    "cake", "calm", "camp", "cape", "card", "care", "cart", "case",
    "cash", "cast", "cave", "cell", "chat", "chef", "chin", "chip",
    "chop", "city", "clad", "clam", "clap", "clay", "clip", "club",
    "clue", "coal", "coat", "code", "coil", "cold", "colt", "come",
    "cook", "cool", "cope", "copy", "cord", "core", "cork", "corn",
    "cost", "cozy", "crew", "crop", "crow", "cube", "cult", "cure",
    "curl", "cute", "dare", "dark", "dart", "dash", "data", "date",
    "dawn", "days", "dead", "deaf", "deal", "dean", "dear", "debt",
    "deck", "deep", "deer", "demo", "deny", "desk", "dial", "dice",
    "diet", "dirt", "dish", "disk", "dock", "does", "dome", "done",
    "door", "dose", "dove", "down", "drag", "draw", "drip", "drop",
    "drum", "dual", "duck", "dude", "duel", "dull", "dump", "dune",
    "dunk", "dusk", "dust", "duty", "each", "earl", "earn", "ease",
    "east", "easy", "edge", "else", "emit", "epic", "euro", "even",
    "evil", "exam", "exec", "exit", "expo", "eyes", "face", "fact",
    "fade", "fail", "fair", "fake", "fall", "fame", "fang", "farm",
    "fast", "fate", "fear", "feat", "feed", "feel", "feet", "fell",
    "felt", "file", "fill", "film", "find", "fine", "fire", "firm",
    "fish", "fist", "five", "flag", "flat", "fled", "flew", "flip",
    "flow", "foam", "fold", "folk", "fond", "font", "food", "fool",
    "foot", "ford", "fork", "form", "fort", "foul", "four", "free",
    "from", "fuel", "full", "fund", "fury", "fuse", "fuss", "gain",
    "gala", "game", "gang", "gate", "gave", "gaze", "gear", "gene",
    "gift", "girl", "give", "glad", "glow", "glue", "goat", "goes",
    "gold", "golf", "gone", "good", "grab", "gray", "grew", "grid",
    "grim", "grin", "grip", "grow", "gulf", "guru", "gust", "hack",
    "hair", "half", "hall", "halt", "hand", "hang", "hard", "harm",
    "harp", "hash", "hate", "haul", "have", "hawk", "haze", "head",
    "heal", "heap", "heat", "heel", "held", "help", "herb", "herd",
    "here", "hero", "hide", "high", "hike", "hill", "hint", "hire",
    "hold", "hole", "holy", "home", "hook", "hope", "horn", "host",
    "hour", "huge", "hull", "hung", "hunt", "hurt", "hush", "icon",
    "idea", "inch", "info", "iron", "isle", "item", "jack", "jade",
    "jail", "jazz", "jean", "jobs", "join", "joke", "jump", "june",
    "jury", "just", "keen", "keep", "kept", "kick", "kids", "kill",
    "kind", "king", "kiss", "kite", "knee", "knew", "knit", "knob",
    "knot", "know", "lack", "laid", "lake", "lamp", "land", "lane",
    "laps", "lard", "lash", "last", "late", "lawn", "lazy", "lead",
    "leaf", "lean", "leap", "left", "lend", "lens", "less", "lick",
    "life", "lift", "like", "lime", "limp", "line", "link", "lion",
    "lips", "list", "live", "load", "loan", "lock", "logo", "lone",
    "long", "look", "loop", "lord", "lose", "loss", "lost", "loud",
    "love", "luck", "lump", "lung", "lure", "lurk", "lush", "made",
    "maid", "mail", "main", "make", "male", "mall", "malt", "mane",
    "many", "maps", "mark", "mars", "mask", "mass", "mast", "mate",
    "mayo", "maze", "meal", "mean", "meat", "meet", "melt", "memo",
    "menu", "mere", "mesh", "mess", "mild", "milk", "mill", "mind",
    "mine", "mint", "miss", "mist", "mock", "mode", "mole", "mood",
    "moon", "more", "moss", "most", "move", "much", "mule", "muse",
    "must", "myth", "nail", "name", "navy", "near", "neat", "neck",
    "need", "nest", "newt", "next", "nice", "nine", "node", "none",
    "noon", "norm", "nose", "note", "noun", "nova", "nude", "nuts",
    "oaks", "oath", "obey", "odds", "odor", "okay", "omit", "once",
    "only", "onto", "open", "oral", "orca", "oven", "owed", "oxen",
    "pace", "pack", "page", "paid", "pail", "pain", "pair", "pale",
    "palm", "pane", "pang", "park", "part", "pass", "past", "path",
    "peak", "pear", "peel", "peer", "perk", "pest", "pick", "pier",
    "pile", "pine", "pink", "pipe", "plan", "play", "plea", "plot",
    "plug", "plum", "plus", "poem", "poet", "pole", "poll", "polo",
    "pond", "pony", "pool", "poor", "pope", "pork", "port", "pose",
    "post", "pour", "pray", "prey", "prop", "pull", "pulp", "pump",
    "punk", "pure", "push", "quit", "quiz", "race", "rack", "raft",
    "rage", "raid", "rail", "rain", "rank", "rare", "rash", "rate",
    "rays", "read", "real", "rear", "reed", "reef", "reel", "rely",
    "rent", "repo", "rest", "rice", "rich", "ride", "rift", "ring",
    "riot", "rise", "risk", "road", "roam", "robe", "rock", "rode",
    "role", "roll", "roof", "room", "root", "rope", "rose", "rote",
    "ruin", "rule", "rung", "runs", "rush", "rust", "safe", "sage",
    "said", "sail", "sake", "sale", "salt", "same", "sand", "sang",
    "sank", "save", "seal", "seam", "seed", "seek", "self", "sell",
    "semi", "send", "sent", "sept", "shed", "shin", "ship", "shop",
    "shot", "show", "shut", "sick", "side", "sigh", "sign", "silk",
    "sing", "sink", "site", "size", "skip", "slab", "slam", "slap",
    "sled", "slew", "slid", "slim", "slip", "slot", "slow", "slug",
    "smog", "snap", "snow", "soak", "soap", "soar", "sock", "soda",
    "sofa", "soft", "soil", "sold", "sole", "some", "song", "soon",
    "sort", "soul", "sour", "span", "spar", "spec", "sped", "spin",
    "spit", "spot", "spur", "stab", "star", "stay", "stem", "step",
    "stew", "stir", "stop", "stud", "such", "suit", "sulk", "sung",
    "sunk", "sure", "surf", "swan", "swap", "swim", "tabs", "tack",
    "tail", "take", "tale", "talk", "tall", "tank", "tape", "taps",
    "tart", "task", "taxi", "team", "tear", "tell", "tend", "tent",
    "term", "test", "text", "than", "that", "them", "then", "thin",
    "this", "tick", "tide", "tidy", "tied", "tier", "tile", "till",
    "tilt", "time", "tiny", "tips", "tire", "toad", "toil", "told",
    "toll", "tomb", "tone", "took", "tool", "tops", "tore", "torn",
    "toss", "tour", "town", "trap", "tray", "tree", "trek", "trim",
    "trio", "trod", "trot", "true", "tube", "tuck", "tuna", "tune",
    "turf", "turn", "tuft", "twin", "type", "undo", "unit", "upon",
    "urge", "used", "user", "vain", "vale", "vane", "vary", "vase",
    "vast", "veil", "vein", "vent", "verb", "very", "vest", "veto",
    "vice", "view", "vine", "visa", "void", "volt", "vote", "wade",
    "wage", "wait", "wake", "walk", "wall", "wand", "ward", "warm",
    "warn", "warp", "wart", "wash", "wasp", "wave", "wavy", "waxy",
    "ways", "weak", "wear", "weed", "week", "well", "went", "were",
    "west", "what", "when", "whom", "wick", "wide", "wife", "wild",
    "will", "wilt", "wily", "wind", "wine", "wing", "wink", "wipe",
    "wire", "wise", "wish", "with", "woke", "wolf", "womb", "wood",
    "wool", "word", "wore", "work", "worm", "worn", "wrap", "wren",
    "wrist", "yard", "yawn", "year", "yell", "yoga", "yolk", "your",
    "zeal", "zero", "zinc", "zone", "zoom",
]

SEPARATORS = ("", " ", "-", "_", ".", "+", "#", "@")

COMMON_PASSPHRASES: list[str] = [
    "correcthorsebatterystaple",
    "correct horse battery staple",
    "correct-horse-battery-staple",
    "iloveyousomuch",
    "letmein123",
    "trustno1",
    "opensesame",
    "password123",
    "qwerty123",
    "sunshine",
    "monkey123",
    "shadow123",
    "master123",
    "dragon123",
    "football123",
    "baseball123",
    "soccer123",
    "hockey123",
    "jordan23",
    "asshole",
]


def _load_wordlist(path: str | Path) -> list[str]:
    """Load words from a file (one per line)."""
    p = Path(path)
    if not p.exists():
        logger.warning("Wordlist not found: %s", p)
        return []
    words: list[str] = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        w = line.strip().lower()
        if w and w.isalpha() and 3 <= len(w) <= 12:
            words.append(w)
    return words


def _mutate_passphrase(words: list[str], sep: str) -> list[str]:
    """Generate passphrase variants from a word list."""
    base = sep.join(words)
    variants: list[str] = [base]

    cap = sep.join(w.capitalize() for w in words)
    variants.append(cap)

    upper = sep.join(w.upper() for w in words)
    variants.append(upper)

    if len(words) >= 2:
        first_cap = words[0].capitalize() + sep + sep.join(words[1:])
        variants.append(first_cap)

    variants.append(base + "1")
    variants.append(base + "123")
    variants.append(base + "!")
    variants.append(cap + "1")
    variants.append(cap + "!")

    if len(words) >= 2:
        num_between = words[0] + "1" + sep.join(words[1:])
        variants.append(num_between)

    trunc = sep.join(w[:4] for w in words)
    if trunc != base:
        variants.append(trunc)
        variants.append(trunc.capitalize() + "1")

    return list(dict.fromkeys(variants))


def generate_passphrases(
    num_words: int = 4,
    *,
    wordlist: list[str] | None = None,
    wordlist_file: str = "",
    separators: list[str] | None = None,
    capitalize: bool = True,
    add_numbers: bool = True,
    sample_size: int = 100,
    max_candidates: int = 0,
    seed: int | None = None,
) -> Generator[str, None, None]:
    """Generate passphrase candidates using diceware patterns.

    Picks random word combinations and applies common passphrase
    mutations to predict real-world passphrase-style passwords.

    Args:
        num_words: Number of words per passphrase (2-6).
        wordlist: Custom word list. Uses EFF short list if not provided.
        wordlist_file: Path to custom wordlist file.
        separators: Separators to try between words.
        capitalize: Include capitalized variants.
        add_numbers: Include numeric suffix variants.
        sample_size: Number of random combinations to generate.
        max_candidates: Limit total output (0 = unlimited).
        seed: Random seed for reproducibility.

    Yields:
        Unique passphrase candidate strings.
    """
    num_words = max(2, min(6, num_words))

    words = wordlist or []
    if not words and wordlist_file:
        words = _load_wordlist(wordlist_file)
    if not words:
        words = EFF_SHORT_WORDLIST

    if len(words) < num_words:
        logger.error("Wordlist too small (%d words, need %d).", len(words), num_words)
        return

    seps = separators if separators is not None else list(SEPARATORS)
    rng = random.Random(seed)

    seen: set[str] = set()
    emitted = 0

    def _emit(candidate: str) -> bool:
        nonlocal emitted
        c = candidate.strip()
        if not c or len(c) < 6 or c in seen:
            return False
        seen.add(c)
        emitted += 1
        return True

    for pp in COMMON_PASSPHRASES:
        if _emit(pp):
            yield pp
            if max_candidates and emitted >= max_candidates:
                return

    for _ in range(sample_size):
        combo = rng.sample(words, num_words)
        for sep in seps:
            variants = _mutate_passphrase(combo, sep)
            for v in variants:
                if _emit(v):
                    yield v
                    if max_candidates and emitted >= max_candidates:
                        return

    if len(words) <= 200 and num_words <= 3:
        for word_group in itertools.combinations(words[:100], min(num_words, 3)):
            combo_list = list(word_group)
            for sep in seps[:3]:
                base = sep.join(combo_list)
                if _emit(base):
                    yield base
                    if max_candidates and emitted >= max_candidates:
                        return
                cap = sep.join(w.capitalize() for w in combo_list)
                if _emit(cap):
                    yield cap
                    if max_candidates and emitted >= max_candidates:
                        return


def run(
    num_words: int = 4,
    wordlist_file: str = "",
    separators: list[str] | None = None,
    sample_size: int = 100,
    max_candidates: int = 0,
    seed: int | None = None,
) -> list[str]:
    """Generate diceware passphrases and return as list."""
    return list(generate_passphrases(
        num_words,
        wordlist_file=wordlist_file,
        separators=separators,
        sample_size=sample_size,
        max_candidates=max_candidates,
        seed=seed,
    ))


def handle_diceware(
    args: Any, _ctx: dict[str, Any],
) -> Generator[str, None, None] | None:
    """CLI handler for the diceware subcommand."""
    words = getattr(args, "words", 4) or 4
    wordlist_file = getattr(args, "wordlist", "") or ""
    sep = getattr(args, "separator", None)
    sample = getattr(args, "sample", 100) or 100
    limit = getattr(args, "limit", 0) or 0
    seed_val = getattr(args, "seed", None)

    seps = [sep] if sep is not None else None

    return generate_passphrases(
        words,
        wordlist_file=wordlist_file,
        separators=seps,
        sample_size=sample,
        max_candidates=limit,
        seed=seed_val,
    )
