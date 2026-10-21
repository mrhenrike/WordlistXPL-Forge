"""
ttpassgen_engine.py: Rule-driven password dictionary generator via TTPassGen.

Wraps the TTPassGen tool (tp7309/TTPassGen) for generating password
dictionaries from user-defined rules. Supports automatic clone/install,
rule-based generation with charset specifications, length constraints,
and combination modes.

TTPassGen generates passwords based on rule definitions that specify
character sets, repetition counts, and ordering. This module provides
a Python interface to build rules, invoke the generator, and stream
results into the WLF pipeline.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

MANIFEST: dict[str, Any] = {
    "name": "ttpassgen_engine",
    "version": __version__,
    "category": "generator",
    "description": "Rule-driven password dictionary generator wrapping TTPassGen",
    "source_url": "https://github.com/tp7309/TTPassGen",
}

_REPO_URL = "https://github.com/tp7309/TTPassGen.git"
_DEFAULT_BRANCH = "master"


@dataclass
class TTPassGenConfig:
    """Configuration for a TTPassGen generation run."""

    rules: list[str] = field(default_factory=list)
    output_file: str = ""
    min_length: int = 1
    max_length: int = 32
    dict_files: list[str] = field(default_factory=list)
    global_repeat: int = 1

    def validate(self) -> list[str]:
        """Return a list of validation errors, empty if config is valid."""
        errors: list[str] = []
        if not self.rules:
            errors.append("At least one rule is required")
        if self.min_length < 0:
            errors.append("min_length must be non-negative")
        if self.max_length < self.min_length:
            errors.append("max_length must be >= min_length")
        if self.global_repeat < 1:
            errors.append("global_repeat must be >= 1")
        return errors


class TTPassGenRule:
    """Builder for TTPassGen rule expressions.

    TTPassGen uses a compact rule syntax:
      [chars]{min,max}  : character set with repetition range
      $dict_name        : reference to dictionary file
      Operators: + (concatenate), | (alternate)

    Example rules:
      "[?l]{4,6}"       : 4 to 6 lowercase letters
      "[?d]{3,3}"       : exactly 3 digits
      "[abc]{1,2}"      : 1 or 2 chars from {a, b, c}
    """

    CHARSETS: dict[str, str] = {
        "lowercase": "?l",
        "uppercase": "?u",
        "digits": "?d",
        "special": "?s",
        "printable": "?a",
    }

    @staticmethod
    def charset_range(charset: str, min_rep: int, max_rep: int) -> str:
        """Build a charset rule segment.

        Args:
            charset: One of CHARSETS keys or a literal char set string.
            min_rep: Minimum repetitions.
            max_rep: Maximum repetitions.

        Returns:
            TTPassGen rule segment string.
        """
        cs = TTPassGenRule.CHARSETS.get(charset, charset)
        return f"[{cs}]{{{min_rep},{max_rep}}}"

    @staticmethod
    def literal(text: str) -> str:
        """Wrap a literal string as a rule segment.

        Args:
            text: Literal text to include.

        Returns:
            Rule segment for the literal.
        """
        return text

    @staticmethod
    def dict_ref(name: str) -> str:
        """Create a dictionary reference for use in rules.

        Args:
            name: Dictionary name (matches a loaded dict file).

        Returns:
            Rule segment referencing the dictionary.
        """
        return f"${name}"

    @staticmethod
    def combine(*segments: str, separator: str = "") -> str:
        """Concatenate rule segments.

        Args:
            segments: Rule segments to combine.
            separator: Optional separator between segments.

        Returns:
            Combined rule string.
        """
        return separator.join(segments)


class TTPassGenEngine:
    """Engine wrapping TTPassGen for password dictionary generation."""

    def __init__(
        self,
        install_dir: str | Path | None = None,
        python_cmd: str = "python3",
    ) -> None:
        """Initialize TTPassGen engine.

        Args:
            install_dir: Directory for TTPassGen installation.
                         Defaults to ~/.local/share/wlf/ttpassgen.
            python_cmd: Python interpreter to use for TTPassGen.
        """
        if install_dir is None:
            base = Path.home() / ".local" / "share" / "wlf" / "ttpassgen"
            self._install_dir = base
        else:
            self._install_dir = Path(install_dir)
        self._python_cmd = python_cmd
        self._installed = False

    @property
    def install_dir(self) -> Path:
        return self._install_dir

    @property
    def is_installed(self) -> bool:
        """Check if TTPassGen is available locally."""
        if self._installed:
            return True
        setup_py = self._install_dir / "setup.py"
        ttpassgen_dir = self._install_dir / "ttpassgen"
        self._installed = setup_py.exists() and ttpassgen_dir.is_dir()
        return self._installed

    def clone(self, force: bool = False) -> Path:
        """Clone TTPassGen repository.

        Args:
            force: If True, remove existing installation and re-clone.

        Returns:
            Path to the cloned repository.

        Raises:
            RuntimeError: If clone fails.
        """
        if self._install_dir.exists() and not force:
            if self.is_installed:
                logger.info("TTPassGen already cloned at %s", self._install_dir)
                return self._install_dir
            shutil.rmtree(self._install_dir)

        if self._install_dir.exists() and force:
            shutil.rmtree(self._install_dir)

        self._install_dir.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Cloning TTPassGen into %s", self._install_dir)

        result = subprocess.run(
            ["git", "clone", "--depth", "1", "-b", _DEFAULT_BRANCH, _REPO_URL,
             str(self._install_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to clone TTPassGen: {result.stderr.strip()}"
            )

        self._installed = True
        return self._install_dir

    def install(self) -> None:
        """Install TTPassGen in editable mode into current environment.

        Raises:
            RuntimeError: If installation fails.
        """
        if not self.is_installed:
            self.clone()

        logger.info("Installing TTPassGen from %s", self._install_dir)
        result = subprocess.run(
            [self._python_cmd, "-m", "pip", "install", "-e",
             str(self._install_dir)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to install TTPassGen: {result.stderr.strip()}"
            )

    def _find_cli(self) -> str:
        """Locate the ttpassgen CLI entry point.

        Returns:
            Path to the ttpassgen executable or module invocation.
        """
        cli = shutil.which("ttpassgen")
        if cli:
            return cli
        return f"{self._python_cmd} -m ttpassgen"

    def generate(
        self,
        config: TTPassGenConfig,
        output_file: str | Path | None = None,
        timeout: int = 600,
    ) -> Path:
        """Generate a password dictionary using TTPassGen rules.

        Args:
            config: Generation configuration with rules and constraints.
            output_file: Destination file path. Uses config.output_file
                         or a temp file if not specified.
            timeout: Max seconds for generation process.

        Returns:
            Path to the generated wordlist file.

        Raises:
            ValueError: If config is invalid.
            RuntimeError: If generation fails.
        """
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid config: {'; '.join(errors)}")

        if output_file:
            out_path = Path(output_file)
        elif config.output_file:
            out_path = Path(config.output_file)
        else:
            fd, tmp = tempfile.mkstemp(suffix=".txt", prefix="ttpassgen_")
            os.close(fd)
            out_path = Path(tmp)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        cli = self._find_cli()
        cmd_parts = cli.split()

        for rule in config.rules:
            args = list(cmd_parts)
            args.extend(["--rule", rule])
            args.extend(["--output", str(out_path)])

            if config.dict_files:
                for df in config.dict_files:
                    args.extend(["--dict_file", df])

            if config.global_repeat > 1:
                args.extend(["--global_repeat", str(config.global_repeat)])

            logger.info("Running TTPassGen: %s", " ".join(args))

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self._install_dir) if self.is_installed else None,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"TTPassGen generation failed for rule '{rule}': "
                    f"{result.stderr.strip()}"
                )

        logger.info("Wordlist generated: %s", out_path)
        return out_path

    def generate_streaming(
        self,
        config: TTPassGenConfig,
        timeout: int = 600,
    ) -> subprocess.Popen[str]:
        """Start TTPassGen in streaming mode, outputting to stdout.

        Args:
            config: Generation configuration.
            timeout: Not enforced; caller manages the process lifetime.

        Returns:
            Popen process with stdout available for line-by-line reading.

        Raises:
            ValueError: If config is invalid.
        """
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid config: {'; '.join(errors)}")

        cli = self._find_cli()
        cmd_parts = cli.split()

        rule = config.rules[0] if config.rules else ""
        args = list(cmd_parts)
        args.extend(["--rule", rule])
        args.extend(["--output", "/dev/stdout"])

        if config.dict_files:
            for df in config.dict_files:
                args.extend(["--dict_file", df])

        logger.info("Starting TTPassGen streaming: %s", " ".join(args))
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self._install_dir) if self.is_installed else None,
        )
        return proc

    def build_common_rules(self) -> list[str]:
        """Return a set of commonly useful TTPassGen rules.

        Returns:
            List of rule strings for typical password patterns.
        """
        rules = [
            "[?l]{6,8}",
            "[?l?u]{6,10}",
            "[?l]{4,6}[?d]{2,4}",
            "[?u]{1,1}[?l]{5,7}[?d]{1,3}",
            "[?l?d?s]{8,12}",
            "[?u]{1,1}[?l]{3,5}[?s]{1,1}[?d]{2,4}",
        ]
        return rules

    def estimate_keyspace(self, rule: str) -> dict[str, Any]:
        """Estimate the keyspace size for a given rule.

        This is a rough estimate based on charset sizes and repetition ranges.
        Does not account for dictionary references or complex rule interactions.

        Args:
            rule: TTPassGen rule string.

        Returns:
            Dictionary with charset_size, min_length, max_length,
            min_candidates, max_candidates.
        """
        import re as _re

        _charset_sizes: dict[str, int] = {
            "?l": 26, "?u": 26, "?d": 10, "?s": 33, "?a": 95,
        }

        pattern = _re.compile(r"\[([^\]]+)\]\{(\d+),(\d+)\}")
        segments = pattern.findall(rule)

        if not segments:
            return {
                "charset_size": 0,
                "min_length": 0,
                "max_length": 0,
                "min_candidates": 0,
                "max_candidates": 0,
            }

        total_min_len = 0
        total_max_len = 0
        min_candidates = 1
        max_candidates = 1

        for charset_str, min_r, max_r in segments:
            min_rep = int(min_r)
            max_rep = int(max_r)
            total_min_len += min_rep
            total_max_len += max_rep

            cs_size = 0
            for token in ["?l", "?u", "?d", "?s", "?a"]:
                if token in charset_str:
                    cs_size += _charset_sizes[token]
            if cs_size == 0:
                cs_size = len(charset_str)

            seg_min = cs_size ** min_rep if min_rep > 0 else 1
            seg_max = sum(cs_size ** r for r in range(min_rep, max_rep + 1))
            min_candidates *= seg_min
            max_candidates *= seg_max

        return {
            "charset_size": cs_size,
            "min_length": total_min_len,
            "max_length": total_max_len,
            "min_candidates": min_candidates,
            "max_candidates": max_candidates,
        }
