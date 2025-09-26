#!/usr/bin/env python3
import os
import stat
import subprocess
from pathlib import Path
import plistlib
import sys

####
# NB! this script makes it such that the update is run every 4 hours.
# it does so by writing an info.plist to your mac, and then making an executable on your machine.
# proceed with caution...
###

LABEL = "com.receiptbuddy.update"     # unique id for launchd
INTERVAL_SECONDS = 240 * 60            # every 4 hours - 3 times a day

def project_root() -> Path:
    return Path(__file__).resolve().parent

def write_run_update_sh(proj: Path) -> Path:
    logs = proj / "logs"
    logs.mkdir(exist_ok=True)
    script = proj / "run_update.sh"
    venv_activate = proj / ".venv" / "bin" / "activate"
    # if your venv path differs, edit this
    script.write_text(
        "#!/bin/zsh\n"
        f"cd {proj}\n"
        f"source {venv_activate}\n"
        "python update.py >> logs/update.log 2>&1\n"
    )
    # chmod +x
    st = os.stat(script)
    os.chmod(script, st.st_mode | stat.S_IEXEC)
    print(f"Wrote and chmod +x {script}")
    return script

def write_launchd_plist(script_path: Path) -> Path:
    launch_agents = Path.home() / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)

    plist_path = launch_agents / f"{LABEL}.plist"
    plist_dict = {
        "Label": LABEL,
        "ProgramArguments": ["/bin/zsh", str(script_path)],
        "StartInterval": INTERVAL_SECONDS,                      # run every N seconds
        "WorkingDirectory": str(script_path.parent),
        "StandardOutPath": str(script_path.parent / "logs" / "launchd.out"),
        "StandardErrorPath": str(script_path.parent / "logs" / "launchd.err"),
        "EnvironmentVariables": {"PYTHONUNBUFFERED": "1"},
        # If you want it to run also right after login:
        # "RunAtLoad": True,
    }
    with plist_path.open("wb") as f:
        plistlib.dump(plist_dict, f)
    print(f"Wrote LaunchAgent: {plist_path}")
    return plist_path

def launchctl(cmd: list[str]) -> None:
    print(f"→ launchctl {' '.join(cmd)}")
    subprocess.run(["launchctl"] + cmd, check=True)

def load_launch_agent(plist_path: Path):
    # unload if already loaded, then load fresh
    try:
        launchctl(["unload", "-w", str(plist_path)])
    except Exception:
        pass
    launchctl(["load", "-w", str(plist_path)])
    print("LaunchAgent loaded")

def run_initial_setup(proj: Path):
    # Run setup.py once to ingest historical data
    print("▶ Running initial historical setup (setup.py)…")
    venv_python = proj / ".venv" / "bin" / "python"
    python_bin = venv_python if venv_python.exists() else sys.executable
    proc = subprocess.run([str(python_bin), "setup.py"], cwd=proj)
    if proc.returncode == 0:
        print("Initial setup completed")
    else:
        print("setup.py exited with non-zero status; check logs/ or console output.")

def main():
    proj = project_root()
    script = write_run_update_sh(proj)
    plist_path = write_launchd_plist(script)
    load_launch_agent(plist_path)
    run_initial_setup(proj)
    print("All set. Your updater will now run on a schedule.")

if __name__ == "__main__":
    main()