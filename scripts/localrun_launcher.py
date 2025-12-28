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


def run_one(cmd, env=None):
    """Run a single command; return (cmd, rc, stdout, stderr)."""
    try:
        # Use provided env or current environment (which should have PYTHONPATH set)
        run_env = env if env is not None else os.environ.copy()
        res = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True, env=run_env)
        return cmd, res.returncode, res.stdout, res.stderr
    except Exception as exc:
        return cmd, 1, "", f"exception: {exc}"


def format_tail(text: str, tail: int) -> str:
    """Return the full text or only the last N lines with an indicator."""
    stripped = text.strip()
    if not stripped or tail == 0:
        return stripped
    lines = stripped.splitlines()
    if len(lines) <= tail:
        return stripped
    return "\n".join(["[...]"] + lines[-tail:])


def find_cmssw_base():
    """Try to find CMSSW_BASE from environment or by walking up from script location."""
    cmssw_base = os.environ.get("CMSSW_BASE")
    if cmssw_base and os.path.exists(cmssw_base):
        return cmssw_base
    # Try to infer from script location: .../CMSSW_X_Y_Z/src/PhysicsTools/...
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parts = script_dir.split(os.sep)
    try:
        idx = parts.index("src")
        if idx > 0:
            candidate = os.sep.join(parts[:idx])
            if os.path.exists(os.path.join(candidate, "src", "PhysicsTools")):
                return candidate
    except ValueError:
        pass
    return None


def find_cmssw_release_base():
    """Try to find CMSSW_RELEASE_BASE from environment or python3 executable path."""
    cmssw_rel = os.environ.get("CMSSW_RELEASE_BASE")
    if cmssw_rel and os.path.exists(cmssw_rel):
        return cmssw_rel
    # Try to infer from python3 executable: .../CMSSW_X_Y_Z/external/.../bin/python3
    try:
        import shutil
        python3_path = shutil.which("python3") or sys.executable
        if python3_path and "CMSSW" in python3_path:
            parts = python3_path.split(os.sep)
            try:
                # Find CMSSW_X_Y_Z in path
                for i, part in enumerate(parts):
                    if part.startswith("CMSSW_") and i > 0:
                        candidate = os.sep.join(parts[:i])
                        if os.path.exists(os.path.join(candidate, "src", "PhysicsTools")):
                            return candidate
            except (IndexError, ValueError):
                pass
    except Exception:
        pass
    return None


def setup_cmssw_paths():
    """
    Setup PYTHONPATH for CMSSW modules. Returns the updated PYTHONPATH string.
    """
    cmssw_base = find_cmssw_base()
    cmssw_rel = find_cmssw_release_base() or os.environ.get("CMSSW_RELEASE_BASE")
    
    extra_paths = []
    if cmssw_base:
        extra_paths.append(os.path.join(cmssw_base, "python"))
        extra_paths.append(os.path.join(cmssw_base, "src"))
    if cmssw_rel:
        extra_paths.append(os.path.join(cmssw_rel, "python"))
        extra_paths.append(os.path.join(cmssw_rel, "src"))
    
    if extra_paths:
        # Update sys.path for this process
        for p in reversed(extra_paths):
            if p not in sys.path and os.path.exists(p):
                sys.path.insert(0, p)
        # Update PYTHONPATH env var for subprocesses
        existing = os.environ.get("PYTHONPATH", "").split(os.pathsep)
        combined = [p for p in extra_paths if os.path.exists(p)] + [p for p in existing if p and p not in extra_paths]
        os.environ["PYTHONPATH"] = os.pathsep.join(combined)
    
    return os.environ.get("PYTHONPATH", "")


def assert_cmssw_env():
    """
    Fail fast with a helpful hint if CMSSW Python modules are not importable.
    This prevents submitting a batch of jobs that will all fail immediately.
    """
    setup_cmssw_paths()
    
    try:
        # Check for the framework module (always needed) and analysis modules
        import PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor  # type: ignore
        import PhysicsTools.NanoAODTools.postprocessing.analysis.modules  # type: ignore
    except ModuleNotFoundError as exc:
        cmssw_base = find_cmssw_base()
        msg = (
            "[launcher] CMSSW environment not set for python3.\n"
            "Try:\n"
            '  source /cvmfs/cms.cern.ch/cmsset_default.sh\n'
            "  cd /home/sqian/Codes/3a_analysis/CMSSW_14_0_7/src\n"
            '  eval "$(scram ru -sh)"\n'
            "  cd -\n"
        )
        if cmssw_base:
            msg += (
                f"Detected CMSSW_BASE={cmssw_base}, but modules still not importable.\n"
                "Ensure PYTHONPATH includes $CMSSW_BASE/python and $CMSSW_BASE/src:\n"
                f'  export PYTHONPATH="{cmssw_base}/python:{cmssw_base}/src:$PYTHONPATH"\n'
            )
        msg += "Then rerun this launcher."
        raise RuntimeError(msg) from exc


def main():
    parser = argparse.ArgumentParser(description="Lightweight launcher to run localrun.py over many files in parallel.")
    parser.add_argument("--pattern", required=True, help="Input glob or directory (e.g. /path/to/*.root or /path/to/dir/)")
    parser.add_argument("--year", required=True, help="Year tag passed to localrun.py (e.g. 2022, 2022EE, 2018, ...)")
    parser.add_argument("-o", "--out", required=True, help="Output directory")
    parser.add_argument("--data", action="store_true", help="Run as data (adds -d); default is MC (-m)")
    parser.add_argument("-n", "--nEve", type=int, default=None, help="Max events to process")
    parser.add_argument("--njobs", type=int, default=4, help="Number of parallel jobs")
    parser.add_argument("--print-cmds", action="store_true", help="Print each command before dispatch")
    parser.add_argument("--print-logs", action="store_true", help="Print stdout/stderr for each finished job")
    parser.add_argument("--tail", type=int, default=20, help="When printing logs, number of trailing lines to show (0 = full)")
    parser.add_argument("--keep-and-drop", dest="keep_and_drop", help="Path to keep_and_drop.txt file (passed to localrun.py)", default=None, type=str)
    parser.add_argument("--postfix", dest="postfix", help="Postfix for output files (e.g., _Skim, passed to localrun.py)", default=None, type=str)
    parser.add_argument("--group-size", dest="group_size", type=int, default=1, help="Group N input files into one output file (default: 1, i.e., one output per input)")
    args = parser.parse_args()

    assert_cmssw_env()
    # Ensure subprocesses inherit the correct PYTHONPATH and use CMSSW python3
    subprocess_env = os.environ.copy()
    # Try to find CMSSW python3, otherwise use the launcher's python3
    import shutil
    launcher_python3 = sys.executable
    # Check if we can find CMSSW python3 from release base
    cmssw_rel = find_cmssw_release_base() or os.environ.get("CMSSW_RELEASE_BASE")
    if cmssw_rel:
        cmssw_python3_pattern = os.path.join(cmssw_rel, "external", "*", "bin", "python3")
        candidates = glob.glob(cmssw_python3_pattern)
        if candidates:
            launcher_python3 = candidates[0]
            if args.print_cmds:
                print(f"[launcher] Using CMSSW python3: {launcher_python3}")
    
    files = collect_files(args.pattern)

    this_dir = os.path.dirname(os.path.realpath(__file__))
    localrun = os.path.realpath(os.path.join(this_dir, "..", "test", "localrun.py"))
    if not os.path.exists(localrun):
        raise RuntimeError(f"Cannot find localrun.py at {localrun}")

    base_flags = ["--year", args.year, "-o", args.out]
    base_flags.append("-d" if args.data else "-m")
    if args.nEve is not None:
        base_flags += ["-n", str(args.nEve)]
    if args.keep_and_drop is not None:
        base_flags += ["--keep-and-drop", args.keep_and_drop]
    if args.postfix is not None:
        base_flags += ["--postfix", args.postfix]
    
    commands = []
    if args.group_size > 1:
        # Group files: process N files together, hadd into one output
        for i in range(0, len(files), args.group_size):
            group = files[i:i + args.group_size]
            # Create hadd output name based on first file in group
            first_file = os.path.basename(group[0])
            hadd_name = first_file.replace('.root', f'_group{i//args.group_size}.root')
            if args.postfix:
                hadd_name = hadd_name.replace('.root', f'{args.postfix}.root')

            # Create command with multiple -i arguments and --hadd-output
            cmd = [launcher_python3, localrun] + base_flags
            for f in group:
                cmd += ["-i", f]
            cmd += ["--hadd-output", hadd_name]
            commands.append(" ".join(cmd))
            if args.print_cmds:
                print(f"[launcher] cmd (group {i//args.group_size + 1}): {commands[-1]}")
    else:
        # One file per job (default)
        for f in files:
            cmd = [launcher_python3, localrun] + base_flags + ["-i", f]
            commands.append(" ".join(cmd))
            if args.print_cmds:
                print(f"[launcher] cmd: {commands[-1]}")

    print(f"[launcher] Prepared {len(commands)} jobs; running with njobs={args.njobs}")

    failures = []
    with ThreadPoolExecutor(max_workers=args.njobs) as ex:
        futures = {ex.submit(run_one, c, subprocess_env): c for c in commands}
        for fut in as_completed(futures):
            cmd, rc, out, err = fut.result()
            if args.print_logs or rc != 0:
                print(f"[job] rc={rc} cmd={cmd}")
                if out.strip():
                    print("[stdout]")
                    print(format_tail(out, args.tail))
                if err.strip():
                    print("[stderr]")
                    print(format_tail(err, args.tail))
                print("-" * 60)
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

