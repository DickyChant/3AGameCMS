#!/usr/bin/env python3
import argparse
import glob
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial


def collect_files(pattern: str):
    """Expand a directory or glob pattern into a sorted list of root files."""
    if os.path.isdir(pattern):
        files = glob.glob(os.path.join(pattern, "*.root"))
    else:
        files = glob.glob(pattern)
    files = sorted(files)
    if not files:
        raise RuntimeError(f"No input files found for: {pattern}")
    return files


def run_one(cmd):
    """Run a single command; return (cmd, rc, stdout, stderr)."""
    try:
        res = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
        return cmd, res.returncode, res.stdout, res.stderr
    except Exception as exc:
        return cmd, 1, "", f"exception: {exc}"


def main():
    parser = argparse.ArgumentParser(description="Lightweight launcher to run localrun.py over many files in parallel.")
    parser.add_argument("--pattern", required=True, help="Input glob or directory (e.g. /path/to/*.root or /path/to/dir/)")
    parser.add_argument("--year", required=True, help="Year tag passed to localrun.py (e.g. 2022, 2022EE, 2018, ...)")
    parser.add_argument("-o", "--out", required=True, help="Output directory")
    parser.add_argument("--data", action="store_true", help="Run as data (adds -d); default is MC (-m)")
    parser.add_argument("-n", "--nEve", type=int, default=None, help="Max events to process")
    parser.add_argument("--njobs", type=int, default=4, help="Number of parallel jobs")
    args = parser.parse_args()

    files = collect_files(args.pattern)

    this_dir = os.path.dirname(os.path.realpath(__file__))
    localrun = os.path.realpath(os.path.join(this_dir, "..", "test", "localrun.py"))
    if not os.path.exists(localrun):
        raise RuntimeError(f"Cannot find localrun.py at {localrun}")

    base_flags = ["--year", args.year, "-o", args.out]
    base_flags.append("-d" if args.data else "-m")
    if args.nEve is not None:
        base_flags += ["-n", str(args.nEve)]

    commands = []
    for f in files:
        cmd = ["python3", localrun] + base_flags + ["-i", f]
        commands.append(" ".join(cmd))

    print(f"[launcher] Prepared {len(commands)} jobs; running with njobs={args.njobs}")

    failures = []
    with ThreadPoolExecutor(max_workers=args.njobs) as ex:
        futures = {ex.submit(run_one, c): c for c in commands}
        for fut in as_completed(futures):
            cmd, rc, out, err = fut.result()
            if rc != 0:
                failures.append((cmd, rc, err.strip()))

    if failures:
        print(f"[launcher] {len(failures)} jobs failed:")
        for cmd, rc, err in failures:
            print(f"  rc={rc} cmd={cmd}")
            if err:
                print(f"    stderr: {err}")
        sys.exit(1)
    else:
        print("[launcher] All jobs finished successfully.")


if __name__ == "__main__":
    main()

