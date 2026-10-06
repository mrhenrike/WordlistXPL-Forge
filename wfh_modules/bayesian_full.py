"""bayesian_full.py - Full Bayesian password model (TarGuess-style).

Implements a Bayesian approach to password structure inference based on:
  - TarGuess (Wang et al. 2016) — user demographic-informed guessing
  - Adaptive PCFG with Dirichlet priors on structure counts
  - Posterior updating as new corpus evidence arrives

Key concepts:
  Prior    : Dirichlet(α) over grammar non-terminals
  Likelihood: P(password | grammar) = PCFG derivation probability
  Posterior : updated online via pseudo-count Dirichlet update

This model tracks three levels:
  1. Structure prior: P(structure | demographic_context)
  2. Segment prior:   P(segment_value | structure_type, context)
  3. Composition:    P(password) = P(structure) * ∏ P(segment)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Generator, Optional


# ── Grammar types ─────────────────────────────────────────────────────────────

_SEG_ALPHA  = "A"   # contiguous alphabetic sequence
_SEG_DIGIT  = "D"   # contiguous digit sequence
_SEG_SPECIAL = "S"  # contiguous special-char sequence


def _segment_type(s: str) -> str:
    if s.isalpha():
        return _SEG_ALPHA
    if s.isdigit():
        return _SEG_DIGIT
    return _SEG_SPECIAL


def _tokenize(pw: str) -> list[tuple[str, str]]:
    """Split password into [(type, value)] segments."""
    segs = []
    for m in re.finditer(r"[A-Za-z]+|[0-9]+|[^A-Za-z0-9]+", pw):
        val = m.group()
        segs.append((_segment_type(val), val))
    return segs


def _structure_key(pw: str) -> str:
    """Compact structure: e.g. 'A6D2S1' from 'hunter42!'"""
    return "".join(f"{t}{len(v)}" for t, v in _tokenize(pw))


# ── Dirichlet posterior ───────────────────────────────────────────────────────

@dataclass
class DirichletCounts:
    """Maintains pseudocounts for Dirichlet posterior P(x | counts)."""
    counts: Counter = field(default_factory=Counter)
    alpha: float = 0.5   # Dirichlet concentration (smoothing)

    def update(self, item: str, weight: float = 1.0) -> None:
        self.counts[item] += weight

    def prob(self, item: str) -> float:
        total = sum(self.counts.values()) + self.alpha * max(len(self.counts), 1)
        return (self.counts.get(item, 0) + self.alpha) / total

    def sample(self, rng: random.Random) -> Optional[str]:
        if not self.counts:
            return None
        keys = list(self.counts.keys())
        weights = [self.counts[k] + self.alpha for k in keys]
        return rng.choices(keys, weights=weights)[0]

    def top_k(self, k: int = 10) -> list[tuple[str, float]]:
        total = sum(self.counts.values()) + self.alpha * max(len(self.counts), 1)
        items = [(k, (v + self.alpha) / total) for k, v in self.counts.most_common(k)]
        return items


# ── Bayesian grammar ──────────────────────────────────────────────────────────

class BayesianGrammar:
    """Bayesian PCFG grammar with online Dirichlet updates.

    Grammar rules:
      S   → structure (sequence of (type, length) pairs)
      Aₙ  → alphabetic segment of length n
      Dₙ  → digit segment of length n
      Sₙ  → special segment of length n

    Each rule has an associated DirichletCounts for segment values.
    """

    def __init__(self, alpha: float = 0.5) -> None:
        self.alpha = alpha
        # P(structure)
        self.structure_prior: DirichletCounts = DirichletCounts(alpha=alpha)
        # P(value | type, length)
        self.segment_priors: dict[str, DirichletCounts] = defaultdict(
            lambda: DirichletCounts(alpha=alpha)
        )

    def _seg_key(self, seg_type: str, length: int) -> str:
        return f"{seg_type}{length}"

    def train(self, passwords: list[str]) -> None:
        """Update posterior from a list of observed passwords."""
        for pw in passwords:
            segs = _tokenize(pw)
            struct = "".join(f"{t}{len(v)}" for t, v in segs)
            self.structure_prior.update(struct)
            for seg_type, value in segs:
                key = self._seg_key(seg_type, len(value))
                self.segment_priors[key].update(value)

    def train_one(self, pw: str, weight: float = 1.0) -> None:
        segs = _tokenize(pw)
        struct = "".join(f"{t}{len(v)}" for t, v in segs)
        self.structure_prior.update(struct, weight)
        for seg_type, value in segs:
            key = self._seg_key(seg_type, len(value))
            self.segment_priors[key].update(value, weight)

    def prob(self, pw: str) -> float:
        """Log probability of a password under the grammar."""
        segs = _tokenize(pw)
        struct = "".join(f"{t}{len(v)}" for t, v in segs)
        log_p = math.log(self.structure_prior.prob(struct) + 1e-30)
        for seg_type, value in segs:
            key = self._seg_key(seg_type, len(value))
            log_p += math.log(self.segment_priors[key].prob(value) + 1e-30)
        return log_p

    def sample(self, rng: random.Random) -> Optional[str]:
        """Sample one password from the posterior grammar."""
        struct = self.structure_prior.sample(rng)
        if not struct:
            return None
        # parse struct: e.g. "A6D2S1"
        parts = re.findall(r"([ADS])(\d+)", struct)
        segments = []
        for seg_type, length_str in parts:
            length = int(length_str)
            key = self._seg_key(seg_type, length)
            dc = self.segment_priors.get(key)
            if dc and dc.counts:
                value = dc.sample(rng)
            else:
                # random fallback for unseen (type, length)
                if seg_type == _SEG_ALPHA:
                    chars = "abcdefghijklmnopqrstuvwxyz"
                elif seg_type == _SEG_DIGIT:
                    chars = "0123456789"
                else:
                    chars = "!@#$%^&*()_+-="
                value = "".join(rng.choices(chars, k=length))
            if value is None:
                return None
            segments.append(value)
        return "".join(segments)


# ── Context priors (TarGuess-style) ──────────────────────────────────────────

@dataclass
class DemographicContext:
    """Demographic context used to weight segment priors."""
    country: str = ""
    gender: str = ""            # "m", "f", ""
    age_band: str = ""          # "young", "adult", "senior"
    sector: str = ""            # "corporate", "consumer", "gov"
    name_tokens: list[str] = field(default_factory=list)
    date_tokens: list[str] = field(default_factory=list)
    keyword_tokens: list[str] = field(default_factory=list)

    def weight_for(self, value: str) -> float:
        """Extra weight for a segment value that matches this context."""
        low = value.lower()
        w = 1.0
        for tok in self.name_tokens + self.date_tokens + self.keyword_tokens:
            if tok.lower() in low:
                w += 2.0
        return min(w, 5.0)


# ── Full Bayesian engine ──────────────────────────────────────────────────────

class BayesianFullEngine:
    """Full Bayesian password generation engine.

    Combines:
      - BayesianGrammar for structure/segment posterior
      - DemographicContext for prior weighting
      - Online update as candidates are reviewed
    """

    def __init__(
        self,
        profile: Optional[dict] = None,
        alpha: float = 0.5,
        seed: Optional[int] = None,
    ) -> None:
        self.profile = profile or {}
        self.grammar = BayesianGrammar(alpha=alpha)
        self.context = _context_from_profile(self.profile)
        self.rng = random.Random(seed)
        self._trained = False

    def train(self, corpus: list[str]) -> None:
        """Train grammar from a corpus of sample passwords."""
        # Weight each password by how well it matches the context
        for pw in corpus:
            segs = _tokenize(pw)
            extra_w = max(self.context.weight_for(v) for _, v in segs) if segs else 1.0
            self.grammar.train_one(pw, weight=extra_w)
        self._trained = True

    def update(self, password: str, weight: float = 1.0) -> None:
        """Online update from a single new observation."""
        self.grammar.train_one(password, weight=weight)

    def score(self, pw: str) -> float:
        """Return normalized [0,1] probability estimate for a candidate."""
        log_p = self.grammar.prob(pw)
        # Normalize: typical log_p range is roughly -30 to -5
        return max(0.0, min(1.0, (log_p + 30) / 25.0))

    def generate(
        self,
        seed_corpus: Optional[list[str]] = None,
        max_candidates: int = 100_000,
        min_len: int = 4,
        max_len: int = 32,
    ) -> Generator[tuple[str, float], None, None]:
        """Generate (candidate, score) tuples from the Bayesian posterior."""
        if seed_corpus:
            self.train(seed_corpus)

        if not self._trained:
            # bootstrap with context tokens
            _bootstrap_from_profile(self.grammar, self.profile, self.rng)
            self._trained = True

        yielded: set[str] = set()
        count = 0
        attempts = 0
        max_attempts = max_candidates * 5

        while count < max_candidates and attempts < max_attempts:
            attempts += 1
            pw = self.grammar.sample(self.rng)
            if pw is None or len(pw) < min_len or len(pw) > max_len:
                continue
            if pw in yielded:
                continue
            yielded.add(pw)
            score = self.score(pw)
            yield (pw, score)
            count += 1

    def describe(self) -> str:
        n_struct = len(self.grammar.structure_prior.counts)
        n_segs = sum(len(d.counts) for d in self.grammar.segment_priors.values())
        top = self.grammar.structure_prior.top_k(5)
        lines = [
            f"BayesianFullEngine — {n_struct} structures, {n_segs} segment values",
            "  Top structures:",
        ]
        for struct, p in top:
            lines.append(f"    {struct:<20s}  p={p:.4f}")
        return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _context_from_profile(profile: dict) -> DemographicContext:
    ctx = DemographicContext()
    ctx.country = profile.get("country", "")
    ctx.sector  = profile.get("sector", "")
    name = profile.get("full_name", "") or profile.get("short_name", "")
    ctx.name_tokens = [t for t in re.split(r"\W+", name) if len(t) > 2]
    for date in profile.get("special_dates", []):
        ctx.date_tokens.extend(re.split(r"\D+", str(date)))
    ctx.keyword_tokens = [str(k) for k in profile.get("keywords", [])]
    return ctx


def _bootstrap_from_profile(grammar: BayesianGrammar, profile: dict, rng: random.Random) -> None:
    """Seed grammar with profile-derived word/date/keyword patterns."""
    seed_pws = []
    name = profile.get("full_name", "") or profile.get("short_name", "")
    if name:
        seed_pws.append(name.capitalize())
        seed_pws.append(name.lower() + "123")
        seed_pws.append(name.lower() + "!")
    for date in profile.get("special_dates", [])[:3]:
        d = str(date).replace("-", "")
        seed_pws.append(d)
    for kw in profile.get("keywords", [])[:10]:
        kw = str(kw)
        seed_pws.append(kw)
        seed_pws.append(kw + str(rng.randint(1, 99)))
    if not seed_pws:
        seed_pws = ["password123", "admin2024!", "user@2025", "P@ssw0rd"]
    for pw in seed_pws:
        grammar.train_one(pw)
