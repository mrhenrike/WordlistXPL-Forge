"""hashcat_monitor.py - Hashcat & John the Ripper progress monitoring.

Monitors cracking sessions by parsing status output (Hashcat text/JSON,
JtR --status output), restore files, and potfile entries.  Provides
speed, progress, ETA, recovered counts, and device temperature readings.

Supported tools:
  - Hashcat 6.x+ (--status, --status-json, .restore, .potfile)
  - John the Ripper (--status, .rec, .pot)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Status parsing (Hashcat --status / --status-json) ─────────────────────────

class HashcatStatus:
    """Parsed Hashcat status snapshot."""

    def __init__(self) -> None:
        self.session: str = ""
        self.status: str = ""
        self.hash_type: str = ""
        self.hash_target: str = ""
        self.time_started: str = ""
        self.speed_total: str = ""
        self.speed_devices: list[str] = []
        self.recovered: str = ""
        self.recovered_count: int = 0
        self.recovered_total: int = 0
        self.progress: str = ""
        self.progress_pct: float = 0.0
        self.rejected: str = ""
        self.restore_point: str = ""
        self.candidates: str = ""
        self.eta: str = ""
        self.temperatures: list[str] = []
        self.raw: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "status": self.status,
            "hash_type": self.hash_type,
            "hash_target": self.hash_target,
            "time_started": self.time_started,
            "speed_total": self.speed_total,
            "speed_devices": self.speed_devices,
            "recovered": self.recovered,
            "recovered_count": self.recovered_count,
            "recovered_total": self.recovered_total,
            "progress": self.progress,
            "progress_pct": round(self.progress_pct, 2),
            "eta": self.eta,
            "rejected": self.rejected,
            "restore_point": self.restore_point,
            "candidates": self.candidates,
            "temperatures": self.temperatures,
        }

    def format_text(self) -> str:
        sep = "─" * 60
        lines = [
            sep,
            "  Hashcat Session Monitor",
            sep,
            f"  Session:      {self.session}",
            f"  Status:       {self.status}",
            f"  Hash type:    {self.hash_type}",
            f"  Target:       {self.hash_target[:50]}",
            f"  Started:      {self.time_started}",
            sep,
            f"  Speed total:  {self.speed_total}",
        ]
        for i, spd in enumerate(self.speed_devices):
            lines.append(f"    Device #{i + 1}: {spd}")
        lines.extend([
            sep,
            f"  Recovered:    {self.recovered}",
            f"  Progress:     {self.progress}  ({self.progress_pct:.1f}%)",
            f"  ETA:          {self.eta}",
            f"  Rejected:     {self.rejected}",
            f"  Restore pt:   {self.restore_point}",
            f"  Candidates:   {self.candidates}",
        ])
        if self.temperatures:
            lines.append(sep)
            lines.append("  Temperatures:")
            for t in self.temperatures:
                lines.append(f"    {t}")
        lines.append(sep)
        return "\n".join(lines)


def parse_status_json(data: dict[str, Any]) -> HashcatStatus:
    """Parse Hashcat --status-json output."""
    s = HashcatStatus()
    s.raw = data
    s.session = str(data.get("session", ""))
    status_code = data.get("status", -1)
    _STATUS_MAP: dict[int, str] = {
        0: "Init", 1: "Autotune", 2: "Selftest",
        3: "Running", 4: "Paused", 5: "Exhausted",
        6: "Cracked", 7: "Aborted", 8: "Quit",
        9: "Bypass", 10: "Checkpoint",
    }
    s.status = _STATUS_MAP.get(int(status_code), f"Unknown({status_code})")
    s.hash_type = str(data.get("hash_type", ""))
    s.hash_target = str(data.get("hash_target", ""))
    s.time_started = str(data.get("time_start", ""))

    devices = data.get("devices", [])
    total_speed = 0
    for dev in devices:
        spd = int(dev.get("speed", 0))
        total_speed += spd
        s.speed_devices.append(f"{spd:,} H/s")
        temp = dev.get("temp")
        if temp is not None:
            s.temperatures.append(f"Device #{dev.get('device_id', '?')}: {temp}°C")
    s.speed_total = f"{total_speed:,} H/s"

    rec = data.get("recovered_hashes", [0, 0])
    if isinstance(rec, list) and len(rec) >= 2:
        s.recovered_count = int(rec[0])
        s.recovered_total = int(rec[1])
        s.recovered = f"{rec[0]}/{rec[1]}"
    else:
        s.recovered = str(rec)

    progress_list = data.get("progress", [0, 0])
    if isinstance(progress_list, list) and len(progress_list) >= 2:
        done = int(progress_list[0])
        total = int(progress_list[1])
        s.progress = f"{done:,}/{total:,}"
        s.progress_pct = (done / total * 100.0) if total > 0 else 0.0
    else:
        s.progress = str(progress_list)

    s.eta = str(data.get("estimated_stop", ""))
    s.rejected = str(data.get("rejected", 0))
    s.restore_point = str(data.get("restore_point", ""))
    cands = data.get("candidates", {})
    if isinstance(cands, dict):
        s.candidates = f"{cands.get('password_candidates_base64', '')}"
    else:
        s.candidates = str(cands)

    return s


def parse_status_text(text: str) -> HashcatStatus:
    """Parse Hashcat legacy text status output."""
    s = HashcatStatus()

    def _extract(pattern: str, default: str = "") -> str:
        m = re.search(pattern, text, re.MULTILINE)
        return m.group(1).strip() if m else default

    s.session = _extract(r"Session\.+:\s*(.+)")
    s.status = _extract(r"Status\.+:\s*(.+)")
    s.hash_type = _extract(r"Hash\.Type\.+:\s*(.+)")
    s.hash_target = _extract(r"Hash\.Target\.+:\s*(.+)")
    s.time_started = _extract(r"Time\.Started\.+:\s*(.+)")
    s.speed_total = _extract(r"Speed\.#\*\.+:\s*(.+)")

    for m in re.finditer(r"Speed\.#(\d+)\.+:\s*(.+)", text):
        s.speed_devices.append(m.group(2).strip())

    s.recovered = _extract(r"Recovered\.+:\s*(.+)")
    rec_match = re.search(r"Recovered\.+:\s*(\d+)/(\d+)", text)
    if rec_match:
        s.recovered_count = int(rec_match.group(1))
        s.recovered_total = int(rec_match.group(2))

    s.progress = _extract(r"Progress\.+:\s*(.+)")
    pct_match = re.search(r"Progress\.+:.*\((\d+(?:\.\d+)?)%\)", text)
    if pct_match:
        s.progress_pct = float(pct_match.group(1))

    s.eta = _extract(r"Time\.Estimated\.+:\s*(.+)")
    s.rejected = _extract(r"Rejected\.+:\s*(.+)")
    s.restore_point = _extract(r"Restore\.Point\.+:\s*(.+)")
    s.candidates = _extract(r"Candidates\.#\d+\.+:\s*(.+)")

    for m in re.finditer(r"Hardware\.Mon\.#(\d+)\.+:\s*Temp:\s*(\d+)c", text, re.IGNORECASE):
        s.temperatures.append(f"Device #{m.group(1)}: {m.group(2)}°C")

    return s


# ── Restore file parser ──────────────────────────────────────────────────────

class RestoreInfo:
    """Parsed Hashcat restore file info."""

    def __init__(self) -> None:
        self.session: str = ""
        self.restore_point: int = 0
        self.args: str = ""
        self.cwd: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "restore_point": self.restore_point,
            "args": self.args,
            "cwd": self.cwd,
        }


def parse_restore_file(path: str) -> RestoreInfo | None:
    """Parse a Hashcat .restore file (binary header + text args)."""
    p = Path(path)
    if not p.is_file():
        logger.warning("Restore file not found: %s", path)
        return None

    info = RestoreInfo()
    info.session = p.stem

    try:
        raw = p.read_bytes()
        if len(raw) < 256:
            logger.warning("Restore file too small: %s", path)
            return None
        text_part = raw[256:].decode("utf-8", errors="ignore")
        lines = [l.strip() for l in text_part.splitlines() if l.strip()]
        if lines:
            info.args = lines[0]
        if len(lines) > 1:
            info.cwd = lines[1]
    except Exception as e:
        logger.warning("Failed to parse restore file %s: %s", path, e)
        return None

    return info


# ── Potfile reader ────────────────────────────────────────────────────────────

def count_potfile(potfile: str) -> int:
    """Count recovered hashes in a potfile."""
    if not Path(potfile).is_file():
        return 0
    count = 0
    for line in Path(potfile).read_text(encoding="utf-8", errors="ignore").splitlines():
        if ":" in line:
            count += 1
    return count


# ── Monitor engine ────────────────────────────────────────────────────────────

class HashcatMonitor:
    """Hashcat session monitoring engine."""

    def __init__(
        self,
        session: str | None = None,
        restore_file: str | None = None,
        status_file: str | None = None,
    ) -> None:
        self.session = session or ""
        self.restore_file = restore_file
        self.status_file = status_file

    def read_status(self) -> HashcatStatus | None:
        """Read and parse current status."""
        if self.status_file:
            p = Path(self.status_file)
            if not p.is_file():
                logger.warning("Status file not found: %s", self.status_file)
                return None
            content = p.read_text(encoding="utf-8", errors="ignore")
            try:
                data = json.loads(content)
                return parse_status_json(data)
            except json.JSONDecodeError:
                return parse_status_text(content)
        return None

    def read_restore(self) -> RestoreInfo | None:
        """Read restore file info."""
        if self.restore_file:
            return parse_restore_file(self.restore_file)
        if self.session:
            default_path = f"{self.session}.restore"
            if Path(default_path).is_file():
                return parse_restore_file(default_path)
        return None

    def summary(self) -> dict[str, Any]:
        """Generate session summary."""
        result: dict[str, Any] = {"session": self.session}

        status = self.read_status()
        if status:
            result["status"] = status.to_dict()

        restore = self.read_restore()
        if restore:
            result["restore"] = restore.to_dict()

        return result


# ── John the Ripper status parsing ────────────────────────────────────────────

class JtRStatus:
    """Parsed John the Ripper status snapshot."""

    def __init__(self) -> None:
        self.session: str = ""
        self.status: str = ""
        self.hash_type: str = ""
        self.speed: str = ""
        self.progress: str = ""
        self.progress_pct: float = 0.0
        self.eta: str = ""
        self.recovered: str = ""
        self.recovered_count: int = 0
        self.recovered_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": "john",
            "session": self.session,
            "status": self.status,
            "hash_type": self.hash_type,
            "speed": self.speed,
            "recovered": self.recovered,
            "recovered_count": self.recovered_count,
            "recovered_total": self.recovered_total,
            "progress": self.progress,
            "progress_pct": round(self.progress_pct, 2),
            "eta": self.eta,
        }

    def format_text(self) -> str:
        sep = "─" * 60
        lines = [
            sep,
            "  John the Ripper Session Monitor",
            sep,
            f"  Session:      {self.session}",
            f"  Status:       {self.status}",
            f"  Hash type:    {self.hash_type}",
            f"  Speed:        {self.speed}",
            sep,
            f"  Recovered:    {self.recovered}",
            f"  Progress:     {self.progress}  ({self.progress_pct:.1f}%)",
            f"  ETA:          {self.eta}",
            sep,
        ]
        return "\n".join(lines)


def parse_jtr_status(text: str) -> JtRStatus:
    """Parse John the Ripper status output."""
    s = JtRStatus()

    def _extract(pattern: str, default: str = "") -> str:
        m = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        return m.group(1).strip() if m else default

    s.session = _extract(r"Session\s*:\s*(.+)")
    s.status = _extract(r"Status\s*:\s*(.+)", "unknown")
    s.hash_type = _extract(r"Hash\s+type\s*:\s*(.+)")

    speed_raw = _extract(r"(?:Guesses|c/s)\s*:\s*(.+)")
    if not speed_raw:
        speed_raw = _extract(r"(\d+[\d,]*\s*(?:p/s|c/s|g/s))")
    s.speed = speed_raw

    rec_match = re.search(r"(\d+)g\s+(\d+):\d+:\d+:\d+", text)
    if rec_match:
        s.recovered_count = int(rec_match.group(1))
    rec_match2 = re.search(r"Loaded\s+(\d+)\s+password", text, re.IGNORECASE)
    if rec_match2:
        s.recovered_total = int(rec_match2.group(1))
    s.recovered = f"{s.recovered_count}/{s.recovered_total}"

    pct_match = re.search(r"(\d+(?:\.\d+)?)%", text)
    if pct_match:
        s.progress_pct = float(pct_match.group(1))
        s.progress = f"{s.progress_pct:.1f}%"

    s.eta = _extract(r"ETA\s*:\s*(.+)")
    if not s.eta:
        s.eta = _extract(r"Remaining\s*:\s*(.+)")

    return s


def parse_jtr_pot(potfile: str) -> int:
    """Count recovered hashes in a JtR potfile."""
    if not Path(potfile).is_file():
        return 0
    count = 0
    for line in Path(potfile).read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        if ":" in line and line.strip():
            count += 1
    return count


# ── CLI handler ───────────────────────────────────────────────────────────────

def handle_hcmon(
    args: Any, ctx: dict[str, Any]
) -> Generator[str, None, None] | None:
    """CLI handler for cracker monitoring (Hashcat + JtR)."""
    session = getattr(args, "session", None)
    restore_file = getattr(args, "restore_file", None)
    status_file = getattr(args, "status_file", None)
    tool = getattr(args, "tool", "hashcat")
    fmt = getattr(args, "format", "text")

    if not any([session, restore_file, status_file]):
        logger.warning(
            "Provide --session, --restore-file, or --status-file."
        )
        return None

    if tool == "john" and status_file:
        content = Path(status_file).read_text(encoding="utf-8", errors="ignore")
        jtr_status = parse_jtr_status(content)
        if fmt == "json":
            def _gen_jtr_json() -> Generator[str, None, None]:
                yield json.dumps(jtr_status.to_dict(), indent=2, ensure_ascii=False)
            return _gen_jtr_json()

        def _gen_jtr_text() -> Generator[str, None, None]:
            yield jtr_status.format_text()
        return _gen_jtr_text()

    monitor = HashcatMonitor(
        session=session,
        restore_file=restore_file,
        status_file=status_file,
    )

    status = monitor.read_status()
    restore = monitor.read_restore()

    if fmt == "json":
        def _gen_json() -> Generator[str, None, None]:
            yield json.dumps(monitor.summary(), indent=2, ensure_ascii=False)
        return _gen_json()

    def _gen_text() -> Generator[str, None, None]:
        if status:
            yield status.format_text()
        elif restore:
            sep = "─" * 60
            yield sep
            yield "  Hashcat Restore Info"
            yield sep
            yield f"  Session:       {restore.session}"
            yield f"  Restore point: {restore.restore_point}"
            yield f"  Args:          {restore.args}"
            yield f"  CWD:           {restore.cwd}"
            yield sep
        else:
            yield "No status or restore data found."

    return _gen_text()
