"""noun_dictionary.py - Built-in noun dictionaries for EN and PT-BR.

Provides common nouns for use by combiner, passphrase, and affix engines.
Each list is curated for password generation relevance: short, memorable
words that humans actually use in passwords.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

__all__ = ["NOUNS_EN", "NOUNS_PT", "get_nouns"]

NOUNS_EN: list[str] = [
    # Nature
    "sun", "moon", "star", "fire", "water", "wind", "rain", "snow",
    "ice", "stone", "rock", "wave", "storm", "earth", "sky", "cloud",
    "river", "ocean", "lake", "mountain", "forest", "tree", "flower",
    "rose", "leaf", "seed", "wolf", "bear", "lion", "tiger", "eagle",
    "hawk", "fox", "snake", "dragon", "horse", "cat", "dog", "bird",
    "fish", "shark", "whale", "deer", "rabbit", "spider", "crow",
    # Body / human
    "heart", "bone", "blood", "brain", "eye", "hand", "arm", "back",
    "head", "face", "neck", "teeth", "jaw", "nerve", "soul", "mind",
    # Objects
    "sword", "shield", "arrow", "blade", "knife", "gun", "bomb",
    "chain", "lock", "key", "door", "gate", "wall", "tower", "bridge",
    "ship", "boat", "car", "truck", "train", "plane", "rocket",
    "house", "home", "room", "floor", "glass", "iron", "steel",
    "gold", "silver", "diamond", "crown", "ring", "coin", "money",
    "book", "page", "code", "rule", "law", "flag", "sign", "light",
    "shadow", "mirror", "clock", "bell", "horn", "drum", "song",
    "phone", "screen", "wire", "cable", "port", "plug", "chip",
    # Abstract
    "power", "force", "speed", "dream", "faith", "hope", "trust",
    "love", "rage", "fear", "peace", "war", "death", "life", "luck",
    "truth", "lie", "game", "play", "fight", "night", "day", "dawn",
    "dusk", "time", "space", "point", "edge", "limit", "match",
    "round", "record", "score", "deal", "trade", "cover", "guard",
    "break", "crash", "smash", "blast", "flash", "spark", "flame",
    "smoke", "dust", "void", "ghost", "spirit", "angel", "demon",
    # Actions (as nouns)
    "punch", "kick", "shot", "strike", "touch", "sight", "sound",
    "voice", "image", "story", "trail", "track", "path", "shore",
    "beach", "ground", "prison", "spell", "portal", "scale",
    # Tech
    "cyber", "hack", "byte", "data", "node", "root", "shell",
    "kernel", "proxy", "stack", "queue", "loop", "patch", "debug",
    "pixel", "laser", "radar", "robot", "clone", "virus", "worm",
    # Compound helpers
    "breaking", "break-ing", "maker", "master", "hunter", "killer",
    "rider", "runner", "walker", "fighter", "keeper", "seeker",
]

NOUNS_PT: list[str] = [
    # Natureza
    "sol", "lua", "estrela", "fogo", "agua", "vento", "chuva", "neve",
    "gelo", "pedra", "rocha", "onda", "tempestade", "terra", "ceu",
    "nuvem", "rio", "oceano", "lago", "montanha", "floresta", "arvore",
    "flor", "rosa", "folha", "semente", "lobo", "urso", "leao",
    "tigre", "aguia", "falcao", "raposa", "cobra", "dragao", "cavalo",
    "gato", "cachorro", "passaro", "peixe", "tubarao", "baleia",
    # Corpo / humano
    "coracao", "osso", "sangue", "cerebro", "olho", "mao", "braco",
    "costas", "cabeca", "rosto", "pescoco", "dente", "nervo", "alma",
    "mente", "vida", "morte",
    # Objetos
    "espada", "escudo", "flecha", "lamina", "faca", "arma", "bomba",
    "corrente", "cadeado", "chave", "porta", "portao", "muro", "torre",
    "ponte", "navio", "barco", "carro", "caminhao", "trem", "aviao",
    "foguete", "casa", "lar", "quarto", "chao", "vidro", "ferro",
    "aco", "ouro", "prata", "diamante", "coroa", "anel", "moeda",
    "dinheiro", "livro", "pagina", "codigo", "regra", "lei", "bandeira",
    "placa", "luz", "sombra", "espelho", "relogio", "sino", "tambor",
    "musica", "telefone", "tela", "fio", "cabo",
    # Abstrato
    "forca", "poder", "velocidade", "sonho", "fe", "esperanca",
    "confianca", "amor", "raiva", "medo", "paz", "guerra", "sorte",
    "verdade", "mentira", "jogo", "luta", "noite", "dia", "tempo",
    "espaco", "ponto", "limite", "recorde", "acordo", "guarda",
    # Gírias e coloquial
    "mano", "cara", "bicho", "nave", "bala", "trampo", "role",
    "parada", "bagulho", "corre", "quebrada", "favela", "vila",
    "praia", "morro", "sertao", "caatinga", "cerrado", "pampa",
    # Comida / cultura
    "cafe", "cerveja", "cachaca", "acai", "churras", "feijao",
    "arroz", "farofa", "coxinha", "pastel", "brigadeiro", "bolo",
    "futebol", "gol", "craque", "camisa", "torcida", "estadio",
    "samba", "funk", "pagode", "forró", "axe", "sertanejo",
    # Tech PT
    "senha", "rede", "servidor", "sistema", "banco", "dados",
    "acesso", "admin", "usuario", "perfil", "conta", "login",
]


def get_nouns(
    lang: str = "all",
    include_compounds: bool = True,
) -> list[str]:
    """Return noun list filtered by language.

    Args:
        lang: Language code ('en', 'pt', 'all').
        include_compounds: Include compound helpers (breaking, maker, etc.).

    Returns:
        Deduplicated noun list.
    """
    result: list[str] = []
    lang_lower = lang.lower().strip()

    if lang_lower in ("en", "en-us", "en-gb", "english", "all"):
        if include_compounds:
            result.extend(NOUNS_EN)
        else:
            result.extend(n for n in NOUNS_EN if " " not in n and "-" not in n)

    if lang_lower in ("pt", "pt-br", "pt-pt", "portuguese", "all"):
        result.extend(NOUNS_PT)

    return list(dict.fromkeys(result))
