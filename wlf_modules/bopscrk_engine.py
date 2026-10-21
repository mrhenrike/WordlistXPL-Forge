"""
bopscrk_engine.py: Smart wordlist generator for targeted attacks.

Wraps bopscrk (R3nt0n/bopscrk) which generates personalized wordlists
from target profile data using transforms, combinations, leet speak,
case mutations, and optionally lyrics from artists the target likes.

Provides both a subprocess wrapper for the bopscrk CLI and a native
Python reimplementation of core transform logic for pipeline integration.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import itertools
import logging
import os
import shutil
import subprocess
import tempfile
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

MANIFEST: dict[str, Any] = {
    "name": "bopscrk_engine",
    "version": __version__,
    "category": "generator",
    "description": "Smart targeted wordlist generator wrapping bopscrk with native transforms",
    "source_url": "https://github.com/R3nt0n/bopscrk",
}

_REPO_URL = "https://github.com/R3nt0n/bopscrk.git"
_DEFAULT_BRANCH = "master"

_LEET_MAP: dict[str, str] = {
    "a": "4", "e": "3", "i": "1", "o": "0",
    "s": "5", "t": "7", "g": "9", "b": "8",
}

_LEET_MAP_EXTENDED: dict[str, list[str]] = {
    "a": ["4", "@"],
    "e": ["3"],
    "i": ["1", "!"],
    "o": ["0"],
    "s": ["5", "$"],
    "t": ["7", "+"],
    "g": ["9"],
    "b": ["8"],
    "l": ["1"],
    "z": ["2"],
}

_COMMON_SUFFIXES = [
    "", "1", "12", "123", "1234", "!", "!!", "@", "#",
    "01", "69", "666", "007", "2024", "2025", "2026",
    ".", "*", "_",
]

_COMMON_PREFIXES = [
    "", "the", "my", "x",
]


@dataclass
class TargetProfile:
    """Profile data for a targeted wordlist generation.

    Attributes:
        names: First names, nicknames, aliases of the target.
        surnames: Last names, family names.
        birth_dates: Dates in various formats (DDMMYYYY, YYYY, etc.).
        pets: Pet names.
        companies: Company or organization names.
        keywords: Additional keywords, interests, hobbies.
        cities: Cities, locations.
        phone_numbers: Phone numbers or fragments.
        artists: Artists/bands the target likes (for lyric extraction).
        custom_words: Additional custom base words.
        min_length: Minimum password length to generate.
        max_length: Maximum password length to generate.
        leet: Enable leet transformations.
        case_mutations: Enable case mutations.
        years_range: Range of years to append (start, end).
    """

    names: list[str] = field(default_factory=list)
    surnames: list[str] = field(default_factory=list)
    birth_dates: list[str] = field(default_factory=list)
    pets: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    phone_numbers: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    custom_words: list[str] = field(default_factory=list)
    min_length: int = 4
    max_length: int = 32
    leet: bool = True
    case_mutations: bool = True
    years_range: tuple[int, int] = (2020, 2027)

    def all_base_words(self) -> list[str]:
        """Collect all base words from profile fields."""
        words: list[str] = []
        for src in (
            self.names, self.surnames, self.pets,
            self.companies, self.keywords, self.cities,
            self.custom_words,
        ):
            words.extend(w.strip() for w in src if w.strip())
        return words

    def all_numbers(self) -> list[str]:
        """Collect all numeric components from profile."""
        nums: list[str] = []
        nums.extend(d.strip() for d in self.birth_dates if d.strip())
        nums.extend(p.strip() for p in self.phone_numbers if p.strip())
        for start_y in range(self.years_range[0], self.years_range[1]):
            nums.append(str(start_y))
        return nums


def apply_leet(word: str, extended: bool = False) -> list[str]:
    """Apply leet speak transformations to a word.

    Args:
        word: Input word.
        extended: If True, generate multiple variants per character.

    Returns:
        List of leet-transformed variants.
    """
    if not extended:
        result = word.lower()
        for orig, repl in _LEET_MAP.items():
            result = result.replace(orig, repl)
        return [result] if result != word.lower() else []

    variants: list[list[str]] = []
    for ch in word.lower():
        if ch in _LEET_MAP_EXTENDED:
            variants.append([ch] + _LEET_MAP_EXTENDED[ch])
        else:
            variants.append([ch])

    results: set[str] = set()
    for combo in itertools.product(*variants):
        candidate = "".join(combo)
        if candidate != word.lower():
            results.add(candidate)

    if len(results) > 500:
        basic = word.lower()
        for orig, repl in _LEET_MAP.items():
            basic = basic.replace(orig, repl)
        return [basic] if basic != word.lower() else []

    return list(results)


def apply_case_mutations(word: str) -> list[str]:
    """Generate case mutation variants of a word.

    Produces: lowercase, uppercase, capitalized, inverted, and
    first-char-lower-rest-upper.

    Args:
        word: Input word.

    Returns:
        List of unique case variants.
    """
    variants: set[str] = set()
    variants.add(word.lower())
    variants.add(word.upper())
    variants.add(word.capitalize())
    if len(word) > 1:
        variants.add(word[0].lower() + word[1:].upper())
        variants.add(word.swapcase())
    return list(variants)


def combine_words(
    words: list[str],
    max_depth: int = 2,
    separators: list[str] | None = None,
) -> Generator[str, None, None]:
    """Generate combinations of words with optional separators.

    Args:
        words: Base word list.
        max_depth: Maximum number of words to combine (2 or 3).
        separators: Separators between combined words.

    Yields:
        Combined word strings.
    """
    if separators is None:
        separators = ["", "_", ".", "-"]

    max_depth = min(max_depth, 3)

    for w1, w2 in itertools.permutations(words, 2):
        for sep in separators:
            yield f"{w1}{sep}{w2}"

    if max_depth >= 3 and len(words) >= 3:
        for combo in itertools.permutations(words[:15], 3):
            yield "".join(combo)


def append_numbers(
    words: list[str],
    numbers: list[str] | None = None,
) -> Generator[str, None, None]:
    """Append numeric suffixes to words.

    Args:
        words: Base word list.
        numbers: Number strings to append. Defaults to common suffixes.

    Yields:
        Words with number suffixes.
    """
    if numbers is None:
        numbers = [str(n) for n in range(100)]
        numbers.extend(["123", "1234", "12345", "2024", "2025", "2026"])

    for word in words:
        for num in numbers:
            yield f"{word}{num}"


def generate_from_profile(
    profile: TargetProfile,
    max_candidates: int = 500_000,
) -> list[str]:
    """Generate a targeted wordlist from a profile using native transforms.

    This is the core native generation pipeline:
    1. Collect base words from profile
    2. Apply case mutations
    3. Apply leet transformations
    4. Combine words (pairs)
    5. Append numbers and suffixes
    6. Filter by length constraints

    Args:
        profile: Target profile data.
        max_candidates: Maximum candidates to generate (safety limit).

    Returns:
        Sorted, deduplicated list of password candidates.
    """
    candidates: set[str] = set()
    base_words = profile.all_base_words()
    numbers = profile.all_numbers()

    candidates.update(base_words)

    if profile.case_mutations:
        for word in list(base_words):
            candidates.update(apply_case_mutations(word))

    if profile.leet:
        for word in list(base_words):
            candidates.update(apply_leet(word, extended=False))

    base_list = list(candidates)[:200]
    for combo in combine_words(base_list, max_depth=2, separators=["", "_"]):
        candidates.add(combo)
        if len(candidates) >= max_candidates:
            break

    expanded: set[str] = set()
    for word in list(candidates)[:5000]:
        for suffix in _COMMON_SUFFIXES:
            expanded.add(f"{word}{suffix}")
        for num in numbers[:50]:
            expanded.add(f"{word}{num}")
        if len(expanded) >= max_candidates:
            break

    candidates.update(expanded)

    filtered = sorted(
        c for c in candidates
        if profile.min_length <= len(c) <= profile.max_length
    )

    if len(filtered) > max_candidates:
        filtered = filtered[:max_candidates]

    return filtered


class BopscrkEngine:
    """Engine wrapping the bopscrk CLI tool."""

    def __init__(
        self,
        install_dir: str | Path | None = None,
        python_cmd: str = "python3",
    ) -> None:
        """Initialize bopscrk engine.

        Args:
            install_dir: Directory for bopscrk installation.
                         Defaults to ~/.local/share/wlf/bopscrk.
            python_cmd: Python interpreter for running bopscrk.
        """
        if install_dir is None:
            self._install_dir = Path.home() / ".local" / "share" / "wlf" / "bopscrk"
        else:
            self._install_dir = Path(install_dir)
        self._python_cmd = python_cmd

    @property
    def install_dir(self) -> Path:
        return self._install_dir

    @property
    def is_installed(self) -> bool:
        """Check if bopscrk is available locally."""
        return (self._install_dir / "bopscrk.py").exists() or (
            self._install_dir / "bopscrk" / "__init__.py"
        ).exists()

    def clone(self, force: bool = False) -> Path:
        """Clone bopscrk repository.

        Args:
            force: Re-clone even if already present.

        Returns:
            Path to cloned repo.

        Raises:
            RuntimeError: If clone fails.
        """
        if self._install_dir.exists():
            if not force and self.is_installed:
                logger.info("bopscrk already cloned at %s", self._install_dir)
                return self._install_dir
            shutil.rmtree(self._install_dir)

        self._install_dir.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Cloning bopscrk into %s", self._install_dir)

        result = subprocess.run(
            ["git", "clone", "--depth", "1", "-b", _DEFAULT_BRANCH,
             _REPO_URL, str(self._install_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone bopscrk: {result.stderr.strip()}")
        return self._install_dir

    def install(self) -> None:
        """Install bopscrk dependencies.

        Raises:
            RuntimeError: If installation fails.
        """
        if not self.is_installed:
            self.clone()

        req_file = self._install_dir / "requirements.txt"
        if req_file.exists():
            result = subprocess.run(
                [self._python_cmd, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.warning("Some bopscrk deps failed: %s", result.stderr.strip())

    def generate_cli(
        self,
        profile: TargetProfile,
        output_file: str | Path | None = None,
        timeout: int = 600,
    ) -> Path:
        """Generate wordlist using the bopscrk CLI.

        Constructs CLI arguments from the target profile and invokes
        bopscrk in non-interactive mode.

        Args:
            profile: Target profile with personal data.
            output_file: Output file path. Temp file if not given.
            timeout: Max seconds for execution.

        Returns:
            Path to the generated wordlist.

        Raises:
            RuntimeError: If bopscrk is not installed or generation fails.
        """
        if not self.is_installed:
            raise RuntimeError("bopscrk not installed. Call clone() first.")

        if output_file:
            out_path = Path(output_file)
        else:
            fd, tmp = tempfile.mkstemp(suffix=".txt", prefix="bopscrk_")
            os.close(fd)
            out_path = Path(tmp)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        main_script = self._install_dir / "bopscrk.py"
        if not main_script.exists():
            main_script = self._install_dir / "bopscrk" / "__main__.py"

        args = [
            self._python_cmd, str(main_script),
            "-o", str(out_path),
            "-min", str(profile.min_length),
            "-max", str(profile.max_length),
        ]

        all_words = profile.all_base_words()
        if all_words:
            args.extend(["-w", ",".join(all_words)])

        if not profile.leet:
            args.append("--no-leet")

        if not profile.case_mutations:
            args.append("--no-case")

        if profile.artists:
            args.extend(["-a", ",".join(profile.artists)])

        logger.info("Running bopscrk: %s", " ".join(args))

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self._install_dir),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"bopscrk generation failed: {result.stderr.strip()}"
            )

        logger.info("Wordlist generated: %s (%d bytes)", out_path, out_path.stat().st_size)
        return out_path

    def generate_native(
        self,
        profile: TargetProfile,
        output_file: str | Path | None = None,
        max_candidates: int = 500_000,
    ) -> Path:
        """Generate wordlist using native Python transforms.

        Falls back to this method when bopscrk CLI is not installed.

        Args:
            profile: Target profile.
            output_file: Output file path.
            max_candidates: Safety limit on candidate count.

        Returns:
            Path to generated wordlist.
        """
        candidates = generate_from_profile(profile, max_candidates)

        if output_file:
            out_path = Path(output_file)
        else:
            fd, tmp = tempfile.mkstemp(suffix=".txt", prefix="bopscrk_native_")
            os.close(fd)
            out_path = Path(tmp)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(candidates) + "\n", encoding="utf-8")
        logger.info(
            "Native generation complete: %s (%d candidates)",
            out_path, len(candidates),
        )
        return out_path
