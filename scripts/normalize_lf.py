"""One-time: normalize quartz/build.ts + patch literals to LF (core.autocrlf-safe workflow)."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BS, NL, BT = chr(92), chr(10), chr(96)
target = subprocess.run(
    ["git", "show", "54b5b14:quartz/build.ts"],
    capture_output=True, cwd=ROOT, encoding="utf-8", errors="replace").stdout.replace(BS + chr(13) + NL, NL)
Path(ROOT / "quartz" / "build.ts").write_text(target, encoding="utf-8", newline=NL)
print("build.ts normalized to LF (54b5b14 content), CRLF present:", BS + chr(13) in target)
