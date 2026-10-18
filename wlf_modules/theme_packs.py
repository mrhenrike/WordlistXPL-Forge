"""theme_packs.py - Thematic vocabulary packs for targeted generation.

Provides curated keyword sets for pop-culture themes commonly found in
passwords: Star Wars, Marvel, gaming, sports, anime, etc.

Usage:
    wlf combiner --theme starwars --tails '123,!'
    wlf combiner --theme gaming --leet --tails '2026'

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from typing import Optional

__all__ = ["get_theme", "list_themes", "THEMES"]

THEMES: dict[str, dict[str, list[str] | str]] = {
    "starwars": {
        "description": "Star Wars universe characters, factions, and terms",
        "keywords": [
            "anakin", "vader", "darth", "luke", "leia", "han", "solo",
            "chewbacca", "chewie", "yoda", "obiwan", "kenobi", "padme",
            "palpatine", "sidious", "maul", "dooku", "grievous", "kylo",
            "ren", "rey", "finn", "poe", "mace", "windu", "r2d2", "c3po",
            "bb8", "jedi", "sith", "force", "lightsaber", "deathstar",
            "empire", "rebel", "republic", "mandalorian", "grogu",
            "boba", "fett", "ahsoka", "stormtrooper", "wookie",
            "tatooine", "coruscant", "endor", "hoth", "dagobah",
            "naboo", "mustafar", "kashyyyk", "alderaan",
            "theforce", "darkside", "lightside", "starwars",
            "maythe4th", "order66", "clonewars", "phantom",
            "menace", "empire", "jedi", "hope", "strikes",
            "padawan", "master", "apprentice", "council",
        ],
    },
    "marvel": {
        "description": "Marvel Cinematic Universe characters and terms",
        "keywords": [
            "stark", "ironman", "tony", "pepper", "spiderman", "peter",
            "parker", "thor", "loki", "odin", "hulk", "bruce", "banner",
            "natasha", "widow", "blackwidow", "hawkeye", "clint",
            "captain", "america", "steve", "rogers", "bucky", "winter",
            "soldier", "thanos", "infinity", "gauntlet", "snap",
            "avengers", "shield", "hydra", "wakanda", "panther",
            "tchalla", "shuri", "strange", "doctor", "wanda",
            "vision", "scarlet", "witch", "falcon", "antman",
            "wasp", "groot", "rocket", "gamora", "drax", "nebula",
            "deadpool", "wolverine", "xmen", "magneto", "xavier",
            "cyclops", "storm", "jean", "phoenix", "mutant",
            "asgard", "mjolnir", "vibranium", "adamantium",
            "jarvis", "friday", "ultron", "endgame", "assemble",
        ],
    },
    "gaming": {
        "description": "Gaming culture, platforms, and popular titles",
        "keywords": [
            "gamer", "player", "noob", "pro", "gg", "ggwp", "pwned",
            "headshot", "respawn", "frag", "combo", "boss", "final",
            "level", "quest", "loot", "epic", "legendary", "rare",
            "steam", "xbox", "playstation", "nintendo", "switch",
            "mario", "luigi", "peach", "bowser", "zelda", "link",
            "master", "chief", "halo", "cortana", "kratos", "god",
            "war", "snake", "solid", "metal", "gear", "cloud",
            "sephiroth", "chocobo", "minecraft", "creeper", "steve",
            "fortnite", "victory", "royale", "apex", "legends",
            "valorant", "csgo", "counter", "strike", "dota",
            "league", "teemo", "yasuo", "garen", "ahri",
            "pikachu", "pokemon", "charizard", "mewtwo",
            "elden", "ring", "darksouls", "praise", "sunbro",
            "wasd", "qwerty", "1337", "h4x0r", "pwn",
            "glhf", "nerf", "buff", "patch", "meta",
        ],
    },
    "sports": {
        "description": "Sports teams, athletes, and culture",
        "keywords": [
            "futebol", "football", "soccer", "basketball", "baseball",
            "hockey", "tennis", "golf", "boxing", "mma", "ufc",
            "champion", "trophy", "medal", "goal", "score", "match",
            "team", "player", "coach", "captain", "stadium",
            "flamengo", "corinthians", "palmeiras", "santos", "vasco",
            "gremio", "inter", "atletico", "cruzeiro", "bahia",
            "barcelona", "real", "madrid", "manchester", "united",
            "liverpool", "chelsea", "arsenal", "juventus", "milan",
            "bayern", "psg", "paris", "dortmund", "ajax",
            "messi", "ronaldo", "neymar", "pele", "maradona",
            "zidane", "ronaldinho", "kaka", "rivaldo", "romario",
            "lakers", "bulls", "warriors", "celtics", "heat",
            "jordan", "lebron", "kobe", "curry", "durant",
            "brady", "mahomes", "superbowl", "nfl", "nba",
            "fifa", "worldcup", "copa", "champions", "league",
        ],
    },
    "anime": {
        "description": "Anime and manga characters and terms",
        "keywords": [
            "naruto", "sasuke", "sakura", "kakashi", "itachi",
            "hinata", "gaara", "hokage", "rasengan", "sharingan",
            "goku", "vegeta", "gohan", "piccolo", "frieza", "cell",
            "buu", "saiyan", "kamehameha", "dragonball", "dbz",
            "luffy", "zoro", "nami", "sanji", "onepiece", "pirate",
            "king", "gear", "haki", "devil", "fruit",
            "ichigo", "rukia", "bleach", "bankai", "zanpakuto",
            "light", "ryuk", "deathnote", "shinigami", "kira",
            "eren", "mikasa", "levi", "titan", "attack",
            "saitama", "genos", "onepunch", "hero", "villain",
            "todoroki", "bakugo", "deku", "allmight", "midoriya",
            "tanjiro", "nezuko", "demon", "slayer", "hashira",
            "sensei", "senpai", "kawaii", "sugoi", "baka",
            "otaku", "manga", "anime", "waifu", "nakama",
        ],
    },
    "music": {
        "description": "Music artists, bands, and terms",
        "keywords": [
            "rock", "metal", "punk", "jazz", "blues", "hiphop", "rap",
            "samba", "funk", "pagode", "sertanejo", "forro", "axe",
            "metallica", "slayer", "megadeth", "pantera", "acdc",
            "ironmaiden", "sabbath", "ozzy", "nirvana", "cobain",
            "pinkfloyd", "zeppelin", "beatles", "stones", "queen",
            "freddie", "mercury", "bowie", "hendrix", "clapton",
            "eminem", "tupac", "biggie", "drake", "kendrick",
            "guitar", "bass", "drums", "vocal", "riff", "solo",
            "concert", "festival", "stage", "encore", "setlist",
            "spotify", "playlist", "vinyl", "album", "track",
            "legiao", "renato", "russo", "raul", "seixas",
            "cazuza", "cbjr", "skank", "jota", "quest",
        ],
    },
    "hacking": {
        "description": "Hacking culture, tools, and terminology",
        "keywords": [
            "hacker", "hack", "root", "admin", "shell", "exploit",
            "payload", "buffer", "overflow", "injection", "xss",
            "sqli", "reverse", "bind", "listener", "backdoor",
            "trojan", "malware", "virus", "worm", "ransomware",
            "phishing", "bruteforce", "dictionary", "rainbow",
            "hash", "crack", "dump", "sniff", "spoof", "mitm",
            "metasploit", "nmap", "burp", "wireshark", "john",
            "hashcat", "hydra", "gobuster", "nikto", "sqlmap",
            "kali", "parrot", "pentest", "redteam", "blueteam",
            "ctf", "flag", "pwn", "binary", "forensic",
            "osint", "recon", "enum", "privesc", "lateral",
            "pivot", "exfil", "c2", "beacon", "implant",
            "zero", "day", "cve", "patch", "vuln",
            "encrypt", "decrypt", "cipher", "aes", "rsa",
            "anonymous", "legion", "lulz", "sec", "infosec",
        ],
    },
    "ctf": {
        "description": "CTF competition terms and lab culture",
        "keywords": [
            "ctf", "flag", "capture", "challenge", "pwn", "crypto",
            "reverse", "forensic", "web", "misc", "stego",
            "binary", "exploit", "overflow", "shellcode", "rop",
            "gadget", "libc", "canary", "aslr", "pie", "nx",
            "jedi", "padawan", "master", "knight", "warrior",
            "hacker", "cracker", "breaker", "solver", "hunter",
            "lab", "labpentest", "pentest", "sec4us", "hackthebox",
            "tryhackme", "vulnhub", "overthewire", "picoctf",
            "rootme", "cybrary", "htb", "thm", "offsec",
            "oscp", "ceh", "dcpt", "ecppt", "ewpt",
            "firstblood", "solved", "rooted", "owned", "pwned",
            "points", "score", "rank", "team", "solo",
        ],
    },
}


def list_themes() -> list[str]:
    """Return available theme names."""
    return sorted(THEMES.keys())


def get_theme(name: str) -> list[str]:
    """Return keywords for a theme.

    Args:
        name: Theme name (case-insensitive).

    Returns:
        List of keywords, or empty list if theme not found.
    """
    theme = THEMES.get(name.lower().strip())
    if theme is None:
        return []
    kws = theme.get("keywords", [])
    return list(kws) if isinstance(kws, list) else []


def get_all_themes() -> list[str]:
    """Return all keywords from all themes, deduplicated."""
    seen: set[str] = set()
    result: list[str] = []
    for theme in THEMES.values():
        kws = theme.get("keywords", [])
        if isinstance(kws, list):
            for kw in kws:
                if kw not in seen:
                    seen.add(kw)
                    result.append(kw)
    return result
