"""
subhunter_engine.py: Rust subdomain enumerator wrapper (SubHunter).

Wraps SubHunter (nicoo/SubHunter), a fast Rust-based subdomain
enumerator that resolves subdomains using concurrent DNS queries.
Provides clone, build, and execution capabilities with result parsing.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import json
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
    "name": "subhunter_engine",
    "version": __version__,
    "category": "enumeration",
    "description": "Rust subdomain enumerator wrapper for SubHunter",
    "source_url": "https://github.com/nicoo/SubHunter",
}

_REPO_URL = "https://github.com/nicoo/SubHunter.git"
_DEFAULT_BRANCH = "main"


@dataclass
class SubHunterResult:
    """Result from a SubHunter enumeration run."""

    domain: str
    subdomains: list[str] = field(default_factory=list)
    resolved: dict[str, list[str]] = field(default_factory=dict)
    total_found: int = 0
    total_resolved: int = 0
    elapsed_seconds: float = 0.0
    wordlist_used: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "domain": self.domain,
            "subdomains": self.subdomains,
            "resolved": self.resolved,
            "total_found": self.total_found,
            "total_resolved": self.total_resolved,
            "elapsed_seconds": self.elapsed_seconds,
            "wordlist_used": self.wordlist_used,
        }

    def export_subdomains(self, output_file: str | Path) -> Path:
        """Export discovered subdomains to a file.

        Args:
            output_file: Destination path.

        Returns:
            Path to written file.
        """
        out = Path(output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            "\n".join(sorted(self.subdomains)) + "\n",
            encoding="utf-8",
        )
        return out


@dataclass
class SubHunterConfig:
    """Configuration for a SubHunter enumeration run."""

    domain: str = ""
    wordlist: str = ""
    threads: int = 50
    timeout_secs: int = 5
    resolvers: list[str] = field(default_factory=list)
    output_file: str = ""
    verbose: bool = False

    def validate(self) -> list[str]:
        """Return validation errors."""
        errors: list[str] = []
        if not self.domain:
            errors.append("domain is required")
        if self.threads < 1:
            errors.append("threads must be >= 1")
        if self.timeout_secs < 1:
            errors.append("timeout_secs must be >= 1")
        return errors


class SubHunterEngine:
    """Engine wrapping the SubHunter Rust tool for subdomain enumeration."""

    def __init__(
        self,
        install_dir: str | Path | None = None,
    ) -> None:
        """Initialize SubHunter engine.

        Args:
            install_dir: Directory for SubHunter clone and build.
                         Defaults to ~/.local/share/wlf/subhunter.
        """
        if install_dir is None:
            self._install_dir = Path.home() / ".local" / "share" / "wlf" / "subhunter"
        else:
            self._install_dir = Path(install_dir)
        self._binary: str | None = None

    @property
    def install_dir(self) -> Path:
        return self._install_dir

    @property
    def is_installed(self) -> bool:
        """Check if SubHunter is cloned and has Cargo.toml."""
        return (self._install_dir / "Cargo.toml").exists()

    @property
    def is_built(self) -> bool:
        """Check if SubHunter binary exists."""
        binary = self._install_dir / "target" / "release" / "subhunter"
        if binary.exists():
            self._binary = str(binary)
            return True
        system_bin = shutil.which("subhunter")
        if system_bin:
            self._binary = system_bin
            return True
        return False

    def clone(self, force: bool = False) -> Path:
        """Clone SubHunter repository.

        Args:
            force: Re-clone even if present.

        Returns:
            Path to cloned repo.

        Raises:
            RuntimeError: If clone fails.
        """
        if self._install_dir.exists():
            if not force and self.is_installed:
                logger.info("SubHunter already cloned at %s", self._install_dir)
                return self._install_dir
            shutil.rmtree(self._install_dir)

        self._install_dir.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Cloning SubHunter into %s", self._install_dir)

        result = subprocess.run(
            ["git", "clone", "--depth", "1", "-b", _DEFAULT_BRANCH,
             _REPO_URL, str(self._install_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone SubHunter: {result.stderr.strip()}")

        return self._install_dir

    def build(self, release: bool = True) -> str:
        """Build SubHunter from source using cargo.

        Requires Rust toolchain (rustc, cargo) to be installed.

        Args:
            release: Build in release mode (recommended).

        Returns:
            Path to the compiled binary.

        Raises:
            RuntimeError: If build fails or cargo is not available.
        """
        if not self.is_installed:
            self.clone()

        cargo = shutil.which("cargo")
        if not cargo:
            raise RuntimeError(
                "Rust toolchain not found. Install via https://rustup.rs/ first."
            )

        args = [cargo, "build"]
        if release:
            args.append("--release")

        logger.info("Building SubHunter (release=%s)", release)

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(self._install_dir),
        )
        if result.returncode != 0:
            raise RuntimeError(f"Build failed: {result.stderr.strip()}")

        profile = "release" if release else "debug"
        binary = self._install_dir / "target" / profile / "subhunter"
        if not binary.exists():
            binaries = list((self._install_dir / "target" / profile).glob("*"))
            executables = [
                b for b in binaries
                if b.is_file() and os.access(b, os.X_OK) and not b.suffix
            ]
            if executables:
                binary = executables[0]
            else:
                raise RuntimeError(
                    f"Binary not found after build. "
                    f"Check {self._install_dir / 'target' / profile}"
                )

        self._binary = str(binary)
        logger.info("SubHunter built: %s", self._binary)
        return self._binary

    def _get_binary(self) -> str:
        """Locate or build the SubHunter binary.

        Returns:
            Path to SubHunter executable.

        Raises:
            RuntimeError: If binary not available and build fails.
        """
        if self._binary and Path(self._binary).exists():
            return self._binary

        if self.is_built:
            return self._binary  # type: ignore[return-value]

        return self.build()

    def enumerate(
        self,
        config: SubHunterConfig,
        timeout: int = 300,
    ) -> SubHunterResult:
        """Run subdomain enumeration.

        Args:
            config: Enumeration configuration.
            timeout: Max seconds for the scan.

        Returns:
            SubHunterResult with discovered subdomains.

        Raises:
            ValueError: If config is invalid.
            RuntimeError: If enumeration fails.
        """
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid config: {'; '.join(errors)}")

        binary = self._get_binary()

        args = [binary, "-d", config.domain]

        if config.wordlist:
            args.extend(["-w", config.wordlist])

        if config.threads != 50:
            args.extend(["-t", str(config.threads)])

        fd, tmp_out = tempfile.mkstemp(suffix=".txt", prefix="subhunter_")
        os.close(fd)

        if config.output_file:
            out_path = config.output_file
        else:
            out_path = tmp_out

        args.extend(["-o", out_path])

        if config.verbose:
            args.append("-v")

        logger.info("Running SubHunter: %s", " ".join(args))

        import time
        start_time = time.monotonic()

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        elapsed = time.monotonic() - start_time

        if result.returncode != 0:
            logger.warning(
                "SubHunter returned code %d: %s",
                result.returncode, result.stderr.strip(),
            )

        subdomains = self._parse_output(out_path, result.stdout)

        hunt_result = SubHunterResult(
            domain=config.domain,
            subdomains=sorted(subdomains),
            total_found=len(subdomains),
            elapsed_seconds=round(elapsed, 2),
            wordlist_used=config.wordlist,
        )

        if tmp_out != out_path:
            try:
                os.unlink(tmp_out)
            except OSError:
                pass

        return hunt_result

    def _parse_output(self, output_file: str, stdout: str) -> list[str]:
        """Parse SubHunter output to extract subdomains.

        Args:
            output_file: Path to output file.
            stdout: Stdout from the process.

        Returns:
            List of discovered subdomain strings.
        """
        subdomains: set[str] = set()

        out_path = Path(output_file)
        if out_path.exists() and out_path.stat().st_size > 0:
            with open(out_path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        host = stripped.split()[0] if " " in stripped else stripped
                        if "." in host:
                            subdomains.add(host.lower())

        for line in stdout.splitlines():
            stripped = line.strip()
            if stripped and "." in stripped and not stripped.startswith("["):
                parts = stripped.split()
                for part in parts:
                    if "." in part and all(
                        c.isalnum() or c in ".-_" for c in part
                    ):
                        subdomains.add(part.lower())

        return list(subdomains)

    def generate_subdomain_wordlist(
        self,
        results: list[SubHunterResult],
        output_file: str | Path,
        include_base_domains: bool = False,
    ) -> Path:
        """Generate a wordlist from SubHunter enumeration results.

        Extracts subdomain prefixes to create a reusable wordlist
        for future enumeration against other targets.

        Args:
            results: List of SubHunterResult objects.
            output_file: Output wordlist path.
            include_base_domains: Include the base domains as entries.

        Returns:
            Path to the generated wordlist.
        """
        prefixes: set[str] = set()

        for res in results:
            base = res.domain.lower()
            for sub in res.subdomains:
                sub_lower = sub.lower()
                if sub_lower.endswith(f".{base}"):
                    prefix = sub_lower[: -(len(base) + 1)]
                    if prefix:
                        prefixes.add(prefix)
                        parts = prefix.split(".")
                        for part in parts:
                            if part:
                                prefixes.add(part)

            if include_base_domains:
                prefixes.add(base)

        out = Path(output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            "\n".join(sorted(prefixes)) + "\n",
            encoding="utf-8",
        )
        logger.info("Subdomain wordlist generated: %s (%d entries)", out, len(prefixes))
        return out

    def check_rust_toolchain(self) -> dict[str, Any]:
        """Check if the Rust toolchain is available.

        Returns:
            Dict with rustc_version, cargo_version, and available flag.
        """
        info: dict[str, Any] = {"available": False, "rustc_version": "", "cargo_version": ""}

        for tool, key in [("rustc", "rustc_version"), ("cargo", "cargo_version")]:
            try:
                result = subprocess.run(
                    [tool, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    info[key] = result.stdout.strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        info["available"] = bool(info["rustc_version"] and info["cargo_version"])
        return info
