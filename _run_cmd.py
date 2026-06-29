#!/usr/bin/env python3
"""One-off runner to capture command output to file."""
import os
import subprocess
import sys

os.chdir("/Users/luan.bui/Documents/code/wc26-bnaul")
env = os.environ.copy()
env["CLAWCUP_TOKEN"] = "wca_fys30-n1UAAvGZrBT1uj01hKfQKgr165m_QCmXLwV9k"
env["CLAWCUP_SIGNING_SECRET"] = "wca_sec_GmHNtXEgIQ0ch4sO0ZvrC21aMdhJ-66C-46ewYWfxZM"

out_path = "/Users/luan.bui/Documents/code/wc26-bnaul/_cmd_output.txt"
lines = []

for cmd in [["python3", "wc26_bnaul.py", "me"], ["python3", "wc26_bnaul.py", "fixtures"]]:
    lines.append(f"=== {' '.join(cmd)} ===")
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    lines.append(f"exit_code: {r.returncode}")
    if r.stdout:
        lines.append("--- stdout ---")
        lines.append(r.stdout.rstrip())
    if r.stderr:
        lines.append("--- stderr ---")
        lines.append(r.stderr.rstrip())
    lines.append("")

with open(out_path, "w") as f:
    f.write("\n".join(lines))

print(f"Wrote output to {out_path}")