"""finetune_engine.py - LLM fine-tune dataset generation from wordlists.

Converts password wordlists into instruction-tuning datasets suitable
for LoRA/QLoRA fine-tuning of language models.  Supports multiple
output formats (Alpaca, ShareGPT, raw completion) and data augmentation
strategies (partial masking, prefix completion, style transfer).

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import logging
import random
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Output formats ──────────────────────────────────────────────────────────

FORMATS = ("alpaca", "sharegpt", "completion")


def _to_alpaca(instruction: str, inp: str, output: str) -> dict[str, str]:
    """Alpaca instruction-tuning format."""
    return {"instruction": instruction, "input": inp, "output": output}


def _to_sharegpt(instruction: str, inp: str, output: str) -> dict[str, Any]:
    """ShareGPT multi-turn conversation format."""
    user_msg = f"{instruction}\n{inp}".strip() if inp else instruction
    return {
        "conversations": [
            {"from": "human", "value": user_msg},
            {"from": "gpt", "value": output},
        ]
    }


def _to_completion(instruction: str, inp: str, output: str) -> dict[str, str]:
    """Raw prompt/completion pair."""
    prompt = f"{instruction}\n{inp}".strip() if inp else instruction
    return {"prompt": prompt, "completion": output}


_FORMAT_MAP: dict[str, Any] = {
    "alpaca": _to_alpaca,
    "sharegpt": _to_sharegpt,
    "completion": _to_completion,
}


# ── Augmentation strategies ─────────────────────────────────────────────────

def _mask_partial(word: str, mask_ratio: float = 0.4) -> str:
    """Mask a portion of the word with underscores."""
    if len(word) < 3:
        return word[0] + "_" * (len(word) - 1)
    n_mask = max(1, int(len(word) * mask_ratio))
    start = random.randint(0, len(word) - n_mask)
    return word[:start] + "_" * n_mask + word[start + n_mask:]


def _prefix_hint(word: str) -> str:
    """Return a prefix hint (first 30-60% of characters)."""
    n = max(1, int(len(word) * random.uniform(0.3, 0.6)))
    return word[:n] + "..."


def _extract_pattern(word: str) -> str:
    """Extract structural pattern: U=upper, L=lower, D=digit, S=special."""
    pattern: list[str] = []
    for ch in word:
        if ch.isupper():
            pattern.append("U")
        elif ch.islower():
            pattern.append("L")
        elif ch.isdigit():
            pattern.append("D")
        else:
            pattern.append("S")
    return "".join(pattern)


# ── Instruction templates ───────────────────────────────────────────────────

_INSTRUCTIONS_COMPLETE = [
    "Generate a password that completes this pattern:",
    "Complete the following password:",
    "Finish this password fragment:",
    "What password matches this partial input?",
]

_INSTRUCTIONS_STYLE = [
    "Generate a password with this structure: {pattern}",
    "Create a password following pattern: {pattern}",
    "Produce a password matching structure: {pattern}",
]

_INSTRUCTIONS_SIMILAR = [
    "Generate a password similar to the given example.",
    "Create a variation of this password style.",
    "Produce a password with similar characteristics.",
]


# ── Core engine ─────────────────────────────────────────────────────────────

class FinetuneEngine:
    """Generate fine-tuning datasets from password wordlists."""

    def __init__(
        self,
        passwords: list[str],
        fmt: str = "alpaca",
        augment: bool = True,
        seed: int = 42,
    ) -> None:
        if fmt not in _FORMAT_MAP:
            raise ValueError(f"Unknown format '{fmt}'. Choose from: {FORMATS}")
        self.passwords = passwords
        self.fmt = fmt
        self.augment = augment
        self.formatter = _FORMAT_MAP[fmt]
        self._rng = random.Random(seed)

    def _make_completion_sample(self, pw: str) -> dict[str, Any]:
        """Create a prefix-completion training sample."""
        hint = _prefix_hint(pw)
        instruction = self._rng.choice(_INSTRUCTIONS_COMPLETE)
        return self.formatter(instruction, hint, pw)

    def _make_mask_sample(self, pw: str) -> dict[str, Any]:
        """Create a masked-completion training sample."""
        masked = _mask_partial(pw)
        instruction = self._rng.choice(_INSTRUCTIONS_COMPLETE)
        return self.formatter(instruction, masked, pw)

    def _make_style_sample(self, pw: str) -> dict[str, Any]:
        """Create a style-transfer training sample (pattern → password)."""
        pattern = _extract_pattern(pw)
        tmpl = self._rng.choice(_INSTRUCTIONS_STYLE)
        instruction = tmpl.format(pattern=pattern)
        return self.formatter(instruction, "", pw)

    def _make_similar_sample(self, pw: str) -> dict[str, Any]:
        """Create a similarity sample using another password as reference."""
        ref = self._rng.choice(self.passwords)
        instruction = self._rng.choice(_INSTRUCTIONS_SIMILAR)
        return self.formatter(instruction, ref, pw)

    def generate(self, max_samples: int = 0) -> Generator[dict[str, Any], None, None]:
        """Yield training samples from the password list.

        Each password produces 1 base sample + up to 3 augmented variants.
        """
        count = 0
        shuffled = list(self.passwords)
        self._rng.shuffle(shuffled)

        for pw in shuffled:
            if len(pw) < 3:
                continue

            yield self._make_completion_sample(pw)
            count += 1
            if 0 < max_samples <= count:
                return

            if self.augment:
                yield self._make_mask_sample(pw)
                count += 1
                if 0 < max_samples <= count:
                    return

                yield self._make_style_sample(pw)
                count += 1
                if 0 < max_samples <= count:
                    return

                if len(self.passwords) > 1:
                    yield self._make_similar_sample(pw)
                    count += 1
                    if 0 < max_samples <= count:
                        return


# ── File I/O ────────────────────────────────────────────────────────────────

def load_passwords(wordlist_path: str, max_load: int = 100_000) -> list[str]:
    """Load passwords from a wordlist file."""
    passwords: list[str] = []
    for line in Path(wordlist_path).read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        pw = line.strip()
        if pw:
            passwords.append(pw)
            if len(passwords) >= max_load:
                break
    return passwords


def write_jsonl(
    samples: Generator[dict[str, Any], None, None],
    output_path: str,
) -> int:
    """Write samples to JSONL file. Returns count written."""
    count = 0
    with open(output_path, "w", encoding="utf-8") as fh:
        for sample in samples:
            fh.write(json.dumps(sample, ensure_ascii=False) + "\n")
            count += 1
    return count


# ── CLI handler ─────────────────────────────────────────────────────────────

def handle_finetune(
    args: Any, ctx: dict[str, Any]
) -> Generator[str, None, None] | None:
    """CLI handler for finetune-data subcommand."""
    wordlist = getattr(args, "wordlist", None)
    output = getattr(args, "output", None)
    fmt = getattr(args, "format", "alpaca")
    augment = not getattr(args, "no_augment", False)
    max_samples = getattr(args, "max_samples", 0)
    seed = getattr(args, "seed", 42)

    if not wordlist:
        logger.warning("No wordlist provided. Use --wordlist.")
        return None

    passwords = load_passwords(wordlist)
    if not passwords:
        logger.warning("Wordlist is empty or unreadable.")
        return None

    engine = FinetuneEngine(
        passwords=passwords,
        fmt=fmt,
        augment=augment,
        seed=seed,
    )

    samples = engine.generate(max_samples=max_samples)

    if output:
        count = write_jsonl(samples, output)
        return iter([f"Wrote {count} samples to {output} (format: {fmt})"])  # type: ignore[return-value]

    def _gen() -> Generator[str, None, None]:
        for sample in engine.generate(max_samples=max_samples):
            yield json.dumps(sample, ensure_ascii=False)

    return _gen()
