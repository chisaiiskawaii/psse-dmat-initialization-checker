#!/usr/bin/env python
"""Summarize POC P/Q/V initialization values from PSS/E OUTX files."""

from __future__ import print_function

import argparse
import csv
import math
import os
import subprocess
import sys

TARGET_TIME = 4.9000
CHANNELS = {"poc_voltage": 5, "poc_active_power": 7, "poc_reactive_power": 9}
DLL_DIRECTORY_HANDLES = []

# PSS/E 34.5 workstation configuration. The script can initially be started
# by VS Code with another Python version; it will restart itself with Python 2.7.
PSSE34_PYTHON = r"C:\Python27\python.exe"
PSSE34_ROOT = r"C:\Program Files (x86)\PTI\PSSE34"
PSSE34_PSSBIN = os.path.join(PSSE34_ROOT, "PSSBIN")
PSSE34_PSSPY = os.path.join(PSSE34_ROOT, "PSSPY27")
PSSE34_DYNTOOLS = os.path.expandvars(
    r"%USERPROFILE%\Downloads\Temporary\_Script\_Spotswood\Temporary\_Script\_Spotswood"
)


def relaunch_with_psse34_python():
    """Restart under PSS/E 34.5's Python 2.7 when launched by VS Code."""
    if sys.version_info[0:2] == (2, 7):
        return None
    if not os.path.isfile(PSSE34_PYTHON):
        return None
    if not os.path.isfile(os.path.join(PSSE34_PSSPY, "psse34.py")):
        return None

    command = [PSSE34_PYTHON, os.path.abspath(__file__)] + sys.argv[1:]
    child_environment = os.environ.copy()
    child_environment["PATH"] = os.pathsep.join([
        PSSE34_PSSBIN,
        PSSE34_PSSPY,
        PSSE34_DYNTOOLS,
        child_environment.get("PATH", ""),
    ])
    child_environment["PYTHONPATH"] = os.pathsep.join([
        PSSE34_PSSPY,
        PSSE34_DYNTOOLS,
        child_environment.get("PYTHONPATH", ""),
    ])
    print(
        "VS Code started Python %d.%d. Restarting with PSS/E 34.5 Python 2.7..."
        % (sys.version_info[0], sys.version_info[1])
    )
    return subprocess.call(command, env=child_environment)


def choose_output_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:  # Python 2 supplied with older PSS/E releases
        import Tkinter as tk
        import tkFileDialog as filedialog
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    root.update()
    folder = filedialog.askdirectory(
        parent=root,
        title="Select one DMAT study folder (or Output for all studies)",
        mustexist=True,
    )
    root.destroy()
    return folder


def _add_runtime_directory(path):
    """Add a possible PSS/E Python/DLL directory to this process."""
    if not path or not os.path.isdir(path):
        return
    if path not in sys.path:
        sys.path.insert(0, path)
    current_path = os.environ.get("PATH", "")
    if path.lower() not in [item.lower() for item in current_path.split(os.pathsep)]:
        os.environ["PATH"] = path + os.pathsep + current_path
    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory:
        try:
            DLL_DIRECTORY_HANDLES.append(add_dll_directory(path))
        except OSError:
            pass


def _find_psse_dyntools():
    """Return possible directories containing dyntools.py."""
    roots = []
    for variable in ("PSSPYTHON_PATH", "PSSE_ROOT", "PSSE_LOCATION", "PSSBIN"):
        value = os.environ.get(variable)
        if value:
            roots.extend(value.split(os.pathsep))
    roots.extend([
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "PTI"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "PTI"),
        PSSE34_DYNTOOLS,
        os.path.join(os.environ.get("USERPROFILE", ""), "Downloads"),
    ])

    found = []
    seen = set()
    for root in roots:
        root = os.path.abspath(os.path.expandvars(root))
        if not os.path.isdir(root) or root.lower() in seen:
            continue
        seen.add(root.lower())
        for current, dirs, files in os.walk(root):
            relative = os.path.relpath(current, root)
            depth = 0 if relative == "." else relative.count(os.sep) + 1
            if depth >= 6:
                dirs[:] = []
            dirs[:] = [
                item for item in dirs
                if item.lower() not in ("doc", "docs", "examples", "example", "help")
            ]
            if "dyntools.py" in [name.lower() for name in files]:
                found.append(current)

    version_tag = "PSSPY%d%d" % (sys.version_info[0], sys.version_info[1])
    found.sort(key=lambda path: (version_tag not in path.upper(), path.lower()))
    return found


def load_dyntools():
    # Prefer the known PSS/E 34.5 paths on the configured workstation.
    for path in (PSSE34_PSSBIN, PSSE34_PSSPY, PSSE34_DYNTOOLS):
        _add_runtime_directory(path)
    try:
        import psse34
    except ImportError:
        pass
    try:
        import dyntools
        return dyntools
    except ImportError:
        pass

    candidates = _find_psse_dyntools()
    errors = []
    for python_dir in candidates:
        _add_runtime_directory(python_dir)
        # PSSBIN is commonly beside the PSSPYxx folders or one level higher.
        parent = os.path.dirname(python_dir)
        for dll_dir in (
            os.path.join(parent, "PSSBIN"),
            os.path.join(os.path.dirname(parent), "PSSBIN"),
        ):
            _add_runtime_directory(dll_dir)
        for module_name in ("psse36", "psse35", "psse34"):
            try:
                __import__(module_name)
                break
            except ImportError:
                continue
        try:
            import dyntools
            return dyntools
        except Exception as exc:
            errors.append("%s -> %s" % (python_dir, exc))

    version = "%d.%d (%s-bit)" % (
        sys.version_info[0], sys.version_info[1], 64 if sys.maxsize > 2 ** 32 else 32
    )
    details = ""
    if candidates:
        details = "\nDetected PSS/E folders, but they could not be loaded:\n  " + "\n  ".join(errors)
    raise RuntimeError(
        "Could not import PSS/E dyntools using Python %s. "
        "Run the script from the PSS/E Command Prompt, or use a Python version "
        "supported by your PSS/E installation.%s" % (version, details)
    )


def find_outx_files(output_folder):
    matches = []
    for current, dirs, files in os.walk(output_folder):
        if os.path.basename(current).lower() != "psse":
            continue
        for name in files:
            if name.lower().endswith(".outx"):
                matches.append(os.path.join(current, name))
    return sorted(matches, key=lambda value: value.lower())


def study_and_test_names(path, output_folder):
    relative = os.path.relpath(path, output_folder)
    parts = relative.split(os.sep)
    # Expected: <study>/<test>/PSSE/<file>.outx. Fall back gracefully.
    psse_index = next((i for i, item in enumerate(parts) if item.lower() == "psse"), None)
    if psse_index is None:
        return "", ""
    test = parts[psse_index - 1] if psse_index >= 1 else ""
    # When the selected root is one DMAT study, the relative structure is
    # <test>/PSSE/<file>.outx, so use the selected folder name as the study.
    study = (
        parts[psse_index - 2]
        if psse_index >= 2
        else os.path.basename(os.path.normpath(output_folder))
    )
    return study, test


def nearest_index(times, target):
    if not times:
        raise ValueError("OUTX file contains no time samples")
    return min(range(len(times)), key=lambda index: abs(float(times[index]) - target))


def is_finite(value):
    try:
        return math.isfinite(float(value))
    except AttributeError:  # Python 2 compatibility
        value = float(value)
        return not math.isnan(value) and not math.isinf(value)
    except (TypeError, ValueError):
        return False


def read_outx(path, dyntools, target_time, max_time_error):
    # outvrsn=1 is the extended OUTX format used by current PSS/E releases.
    try:
        channel_file = dyntools.CHNF(path, outvrsn=1)
    except TypeError:
        channel_file = dyntools.CHNF(path)
    _title, channel_ids, channel_data = channel_file.get_data()

    times = list(channel_data.get("time", []))
    index = nearest_index(times, target_time)
    actual_time = float(times[index])
    if abs(actual_time - target_time) > max_time_error:
        raise ValueError(
            "Nearest sample is %.6f s, more than %.6f s from target"
            % (actual_time, max_time_error)
        )

    result = {"sample_time_s": actual_time}
    for label, channel_number in CHANNELS.items():
        if channel_number not in channel_data:
            raise KeyError("Channel %s is missing" % channel_number)
        values = channel_data[channel_number]
        if index >= len(values):
            raise IndexError("Channel %s has fewer samples than time" % channel_number)
        result[label] = float(values[index])
        result[label + "_channel_name"] = str(channel_ids.get(channel_number, ""))

    values = [result[name] for name in CHANNELS]
    if not all(is_finite(value) for value in values):
        result["status"] = "FAIL"
        result["remarks"] = "One or more POC values are NaN or infinite"
    else:
        result["status"] = "READ OK"
        result["remarks"] = "Review P/Q/V against the expected test setpoints"
    return result


def analyse(output_folder, target_time, max_time_error):
    dyntools = load_dyntools()
    rows = []
    outx_files = find_outx_files(output_folder)
    print("Found %d OUTX file(s) below: %s" % (len(outx_files), output_folder))
    for position, path in enumerate(outx_files, 1):
        print("[%d/%d] Reading %s" % (
            position, len(outx_files), os.path.relpath(path, output_folder)
        ))
        study, test = study_and_test_names(path, output_folder)
        row = {
            "study": study,
            "test": test,
            "outx_file": os.path.basename(path),
            "relative_path": os.path.relpath(path, output_folder),
            "target_time_s": target_time,
        }
        try:
            row.update(read_outx(path, dyntools, target_time, max_time_error))
        except Exception as exc:
            row["status"] = "FAIL"
            row["remarks"] = "%s: %s" % (type(exc).__name__, exc)
            print("        FAIL: %s" % row["remarks"])
        rows.append(row)
    return rows


def write_csv(rows, destination):
    columns = [
        "study", "test", "outx_file", "relative_path", "target_time_s",
        "sample_time_s", "poc_voltage", "poc_active_power",
        "poc_reactive_power", "status", "remarks",
        "poc_voltage_channel_name", "poc_active_power_channel_name",
        "poc_reactive_power_channel_name",
    ]
    # Python 2's csv module requires binary mode; Python 3 uses newline="".
    if sys.version_info[0] < 3:
        handle = open(destination, "wb")
    else:
        handle = open(destination, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    finally:
        handle.close()


def main():
    relaunched_result = relaunch_with_psse34_python()
    if relaunched_result is not None:
        return relaunched_result

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_folder", nargs="?",
        help="Path to one DMAT study folder or the parent Output folder",
    )
    parser.add_argument("--time", type=float, default=TARGET_TIME, help="Target time in seconds")
    parser.add_argument(
        "--max-time-error", type=float, default=0.01,
        help="Maximum permitted distance from the target sample (default: 0.01 s)",
    )
    args = parser.parse_args()
    output_folder = args.output_folder or choose_output_folder()
    if not output_folder:
        print("No folder selected.")
        return 1
    output_folder = os.path.abspath(output_folder)
    if not os.path.isdir(output_folder):
        print("Folder does not exist: %s" % output_folder)
        return 1

    try:
        rows = analyse(output_folder, args.time, args.max_time_error)
    except Exception as exc:
        print("ERROR: %s" % exc)
        return 1

    # Keep the report beside this program, not inside the source study folders.
    program_folder = os.path.dirname(os.path.abspath(__file__))
    destination = os.path.join(program_folder, "DMAT_Initialization_Summary.csv")
    write_csv(rows, destination)
    failures = sum(1 for row in rows if row.get("status") == "FAIL")
    print("Processed %d OUTX file(s); %d failed to read." % (len(rows), failures))
    print("Summary written to: %s" % destination)
    try:
        os.startfile(destination)
    except (AttributeError, OSError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
