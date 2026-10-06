"""coverage_analyzer.py - Sample corpus coverage and replay hit-rate (memory-safe).

Streams local generated/*.lst without loading full corpora into RAM.
Reports structural families and whether configurable engines can reproduce
sampled targets (cover). Replay generates candidates and measures hits
against a sampled bloom of the corpus.

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import hashlib
import random
import re
import zlib
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator, Optional

_REPO = Path(__file__).resolve().parents[1]

_STRUCT_RE = re.compile(
    r"(?P<lead>[^A-Za-z0-9]*)"
    r"(?P<body>[A-Za-z0-9]+(?:[^A-Za-z0-9]+[A-Za-z0-9]+)*)"
    r"(?P<trail>[^A-Za-z0-9]*)"
)


def _default_corpus(kind: str = "passwords") -> Path:
    name = "passwords.lst" if kind == "passwords" else "users.lst"
    return _REPO / "generated" / name


def reservoir_sample(path: Path, k: int, seed: int = 42) -> list[str]:
    """Reservoir sample k non-empty lines from path (O(k) memory)."""
    rng = random.Random(seed)
    sample: list[str] = []
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for i, line in enumerate(fh, 1):
            s = line.rstrip("\n\r")
            if not s:
                continue
            if len(sample) < k:
                sample.append(s)
            else:
                j = rng.randint(1, i)
                if j <= k:
                    sample[j - 1] = s
    return sample


def structure_mask(pwd: str) -> str:
    """Map password to coarse mask: W=alpha run, D=digit, S=special."""
    out: list[str] = []
    for ch in pwd:
        if ch.isalpha():
            t = "W"
        elif ch.isdigit():
            t = "D"
        else:
            t = "S"
        if not out or out[-1] != t:
            out.append(t)
    return "".join(out)


def hashcat_mask(pwd: str) -> str:
    parts: list[str] = []
    for ch in pwd:
        if ch.islower():
            parts.append("?l")
        elif ch.isupper():
            parts.append("?u")
        elif ch.isdigit():
            parts.append("?d")
        else:
            parts.append("?s")
    return "".join(parts)


class _Bloom:
    """Tiny bloom for membership tests on sampled corpus (memory-safe)."""

    __slots__ = ("_bits", "_m", "_k")

    def __init__(self, m_bits: int = 1 << 22, k: int = 4) -> None:
        self._m = m_bits
        self._k = k
        self._bits = bytearray(m_bits // 8)

    def _indexes(self, s: str) -> Iterator[int]:
        h = hashlib.sha256(s.encode("utf-8", errors="replace")).digest()
        for i in range(self._k):
            v = int.from_bytes(h[i * 4 : (i + 1) * 4], "little")
            yield v % self._m

    def add(self, s: str) -> None:
        for idx in self._indexes(s):
            self._bits[idx // 8] |= 1 << (idx % 8)

    def __contains__(self, s: object) -> bool:
        if not isinstance(s, str):
            return False
        return all(self._bits[idx // 8] & (1 << (idx % 8)) for idx in self._indexes(s))


def build_bloom_from_file(path: Path, max_lines: int = 500_000, seed: int = 7) -> _Bloom:
    """Add up to max_lines reservoir-sampled entries into a bloom filter."""
    bloom = _Bloom()
    for s in reservoir_sample(path, max_lines, seed=seed):
        bloom.add(s)
    return bloom


def analyze_cover(
    corpus: Path,
    sample_size: int = 1000,
    seed: int = 42,
) -> dict:
    """Sample corpus and summarize structural families + engine hints."""
    sample = reservoir_sample(corpus, sample_size, seed=seed)
    structs = Counter(structure_mask(s) for s in sample)
    masks = Counter(hashcat_mask(s) for s in sample)
    special_heavy = sum(1 for s in sample if any(c in s for c in "#@_!$"))
    leetish = sum(1 for s in sample if re.search(r"[4301@$]", s) and re.search(r"[A-Za-z]", s))
    multi_sep = sum(1 for s in sample if sum(1 for c in s if not c.isalnum()) >= 2)

    engine_hints = {
        "pattern+leet": "Templates with leet.*: vars cover P1/P2/P3 families",
        "profile/affix": "Pets/years/specials for Company#PetYY and _LEET@YEAR#Pet",
        "password-dna": "Replay behavioral DNA from known cracks",
        "pcfg/markov": "Train on generated/*.lst then generate (--action train)",
        "rulegen": "Derive hashcat rules from sampled masks",
    }

    top_structs = structs.most_common(15)
    top_masks = masks.most_common(10)
    return {
        "corpus": str(corpus),
        "sampled": len(sample),
        "unique_structures": len(structs),
        "unique_masks": len(masks),
        "special_heavy_pct": round(100.0 * special_heavy / max(len(sample), 1), 2),
        "leetish_pct": round(100.0 * leetish / max(len(sample), 1), 2),
        "multi_sep_pct": round(100.0 * multi_sep / max(len(sample), 1), 2),
        "top_structures": top_structs,
        "top_masks": top_masks,
        "engine_hints": engine_hints,
        "sample_preview": sample[:10],
    }


def replay_hit_rate(
    candidates: Iterable[str],
    bloom: _Bloom,
) -> dict:
    """Measure how many generated candidates appear in bloom(sample of corpus)."""
    total = 0
    hits = 0
    hit_examples: list[str] = []
    for c in candidates:
        c = c.strip()
        if not c:
            continue
        total += 1
        if c in bloom:
            hits += 1
            if len(hit_examples) < 20:
                hit_examples.append(c)
    return {
        "candidates": total,
        "hits": hits,
        "hit_rate_pct": round(100.0 * hits / max(total, 1), 4),
        "hit_examples": hit_examples,
        "note": "Hit rate is vs bloom of a corpus sample — not a 100% guarantee.",
    }


def generate_pattern_candidates(
    company: str = "BrandX",
    pet: str = "OzZY",
    year: str = "2026",
    tag: str = "CS",
) -> list[str]:
    """Deterministic P1/P2/P3-style smoke candidates (placeholders)."""
    from wfh_modules.pattern_engine import expand_variable, render_template

    out: list[str] = []
    specs = [
        ("{company}#{pet}{yy}", {"company": [company], "pet": [pet], "yy": [year[-2:]]}),
        (
            "_{company}@{year}#{pet}",
            {
                "company": expand_variable("company", f"leet.aggressive:{company}"),
                "year": [year],
                "pet": [pet if pet != "OzZY" else "Pitty"],
            },
        ),
        (
            "#{company}@{tag}",
            {
                "company": expand_variable("company", f"leet.medium:{company.lower()}"),
                "tag": [tag],
            },
        ),
    ]
    for tmpl, vars_ in specs:
        for line in render_template(tmpl, vars_):
            out.append(line)
            if len(out) >= 400:
                return out
    return out


def handle_cover(args, _ctx: dict) -> None:
    kind = getattr(args, "kind", "passwords") or "passwords"
    corpus = Path(getattr(args, "corpus", "") or _default_corpus(kind))
    sample_size = int(getattr(args, "sample", 1000) or 1000)
    if not corpus.is_file():
        print(f"[-] Corpus not found: {corpus}")
        return
    report = analyze_cover(corpus, sample_size=sample_size, seed=int(getattr(args, "seed", 42)))
    print(f"[+] Cover report for {report['corpus']}")
    print(f"    sampled={report['sampled']} structures={report['unique_structures']} masks={report['unique_masks']}")
    print(f"    special_heavy={report['special_heavy_pct']}% leetish={report['leetish_pct']}% multi_sep={report['multi_sep_pct']}%")
    print("    top structures:")
    for struct, n in report["top_structures"]:
        print(f"      {struct:12s} {n}")
    print("    top hashcat masks:")
    for mask, n in report["top_masks"]:
        print(f"      {mask}  ({n})")
    print("    engine hints:")
    for k, v in report["engine_hints"].items():
        print(f"      - {k}: {v}")
    out = getattr(args, "output", None)
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(f"# cover {report['corpus']}\n")
            for struct, n in report["top_structures"]:
                fh.write(f"struct\t{struct}\t{n}\n")
            for mask, n in report["top_masks"]:
                fh.write(f"mask\t{mask}\t{n}\n")
        print(f"[+] Wrote {out}")


def handle_replay(args, _ctx: dict) -> None:
    kind = getattr(args, "kind", "passwords") or "passwords"
    corpus = Path(getattr(args, "corpus", "") or _default_corpus(kind))
    bloom_n = int(getattr(args, "bloom_sample", 200_000) or 200_000)
    if not corpus.is_file():
        print(f"[-] Corpus not found: {corpus}")
        return

    cand_file = getattr(args, "candidates", None)
    if cand_file:
        def _iter() -> Iterator[str]:
            with open(cand_file, encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    yield line
    else:
        company = getattr(args, "company", "BrandX")
        pet = getattr(args, "pet", "OzZY")
        year = getattr(args, "year", "2026")
        tag = getattr(args, "tag", "CS")
        cands = generate_pattern_candidates(company, pet, year, tag)
        # optional DNA expansion from seeds
        seeds = getattr(args, "seeds", None) or []
        if seeds:
            from wfh_modules.password_dna import PasswordDNA, generate_from_dna

            try:
                dna = PasswordDNA(list(seeds)[:10])
                for line in generate_from_dna(dna, depth=getattr(args, "depth", "quick") or "quick"):
                    cands.append(line)
                    if len(cands) >= 5000:
                        break
            except Exception:
                pass
        def _iter() -> Iterator[str]:
            yield from cands

    print(f"[*] Building bloom from sample≤{bloom_n} of {corpus} ...")
    bloom = build_bloom_from_file(corpus, max_lines=bloom_n)
    result = replay_hit_rate(_iter(), bloom)
    print(f"[+] Replay: candidates={result['candidates']} hits={result['hits']} "
          f"rate={result['hit_rate_pct']}%")
    print(f"    {result['note']}")
    if result["hit_examples"]:
        print("    examples:")
        for h in result["hit_examples"]:
            print(f"      {h}")
    out = getattr(args, "output", None)
    if out:
        Path(out).write_text(
            "\n".join(result["hit_examples"]) + ("\n" if result["hit_examples"] else ""),
            encoding="utf-8",
        )
        print(f"[+] Wrote hit examples: {out}")
