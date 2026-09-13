#!/usr/bin/env python3
"""Native Homebrew evidence for the tap's current DSL and migrated app installs.

Run on disposable macOS CI runners only. This exercises the existing cask hooks,
including the three legacy apps' scoped quarantine removal; it does not modify
Gatekeeper, execute the apps, or install Hermes (which has its own native gate).
"""
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TAP = "frankhommers/tap"
APPS = {
    "git-auto-sync": "Git Auto Sync.app",
    "mcp-manager": "MCP Manager.app",
    "rclone-mount-manager": "Rclone Mount Manager.app",
}


def require_tap_trusted(raw):
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Homebrew returned invalid tap-trust JSON") from exc
    taps = state.get("taps") if isinstance(state, dict) else None
    if not isinstance(taps, list) or TAP not in taps:
        raise RuntimeError(f"Homebrew did not record explicit trust for {TAP}")


def main():
    if platform.system() != "Darwin" or os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("This installer verification requires a disposable macOS Actions runner")
    logs = Path(os.environ["RUNNER_TEMP"]) / "cask-validation"
    logs.mkdir(parents=True, exist_ok=True)
    apps = Path(os.environ["RUNNER_TEMP"]) / "cask-validation-apps"
    apps.mkdir(exist_ok=True)

    def run(label, *argv):
        result = subprocess.run(argv, capture_output=True, text=True)
        (logs / f"{label}.stdout.log").write_text(result.stdout)
        (logs / f"{label}.stderr.log").write_text(result.stderr)
        (logs / f"{label}.json").write_text(json.dumps({
            "command": argv, "exitCode": result.returncode,
        }, indent=2) + "\n")
        print(f"{label}: exit {result.returncode}", flush=True)
        print(result.stdout + result.stderr, flush=True)
        if result.returncode:
            raise RuntimeError(f"{label} failed")
        if re.search(r"Calling .*deprecated", result.stdout + result.stderr):
            raise RuntimeError(f"{label} emitted a Homebrew DSL deprecation")
        return result.stdout

    run("brew-version", "brew", "--version")
    run("trust-tap", "brew", "trust", TAP)
    require_tap_trusted(run("trust-before-tap", "brew", "trust", "--json=v1"))
    run("tap", "brew", "tap", TAP, str(ROOT))
    require_tap_trusted(run("trust-after-tap", "brew", "trust", "--json=v1"))
    tap = Path(run("tap-path", "brew", "--repository", TAP).strip())
    # Explicitly use the PR bytes even if brew tap chose a default-branch clone.
    for source in sorted((ROOT / "casks").glob("*.rb")):
        shutil.copyfile(source, tap / "casks" / source.name)
    tokens = [f"{TAP}/{p.stem}" for p in sorted((ROOT / "casks").glob("*.rb"))]
    info = json.loads(run("info", "brew", "info", "--json=v2", "--cask", *tokens))
    if {cask["token"] for cask in info["casks"]} != {p.stem for p in (ROOT / "casks").glob("*.rb")}:
        raise RuntimeError("Homebrew did not parse every checked-in cask")
    run("style", "brew", "style", "--cask", *tokens)
    run("audit", "brew", "audit", "--cask", *tokens)

    verified = []
    for token, bundle in APPS.items():
        name = f"{TAP}/{token}"
        run(f"{token}-fetch", "brew", "fetch", "--cask", name)
        run(f"{token}-install", "brew", "install", "--cask", f"--appdir={apps}", name)
        app = apps / bundle
        with (app / "Contents/Info.plist").open("rb") as stream:
            metadata = plistlib.load(stream)
        executable = app / "Contents/MacOS" / metadata["CFBundleExecutable"]
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise RuntimeError(f"Missing app executable: {executable}")
        file_info = run(f"{token}-executable", "/usr/bin/file", str(executable))
        if "Mach-O" not in file_info or platform.machine() not in file_info:
            raise RuntimeError("Wrong installed executable architecture")
        attributes = run(f"{token}-attributes", "/usr/bin/xattr", str(app)).splitlines()
        if "com.apple.quarantine" in attributes:
            raise RuntimeError("Migrated postflight did not preserve the existing root-attribute removal")
        verified.append({"token": token, "app": str(app), "executable": str(executable),
                         "architecture": platform.machine(), "rootQuarantineRemoved": True})
    report = {"parsedCasks": sorted(c["token"] for c in info["casks"]), "installed": verified}
    (logs / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
