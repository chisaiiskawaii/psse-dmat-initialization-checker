#!/usr/bin/env python
"""Summarize POC P/Q/V initialization values from PSS/E OUTX files."""

from __future__ import print_function

import argparse
import csv
import math
import os
import sys

TARGET_TIME = 4.9000
CHANNELS = {"poc_voltage": 5, "poc_active_power": 7, "poc_reactive_power": 9}


def choose_output_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:  # Python 2 supplied with older PSS/E releases
        import Tkinter as tk
        import tkFileDialog as filedialog
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select the Output folder")
    root.destroy()
    return folder


def load_dyntools():
    try:
        import dyntools
        return dyntools
    except ImportError:
        raise RuntimeError(
            "Could not import PSS/E dyntools. Run this script with the Python "
            "environment supplied/configured by PSS/E."
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
    study = parts[psse_index - 2] if psse_index >= 2 else ""
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
    for path in find_outx_files(output_folder):
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
    with open(destination, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_folder", nargs="?", help="Path to the Output folder")
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

    destination = os.path.join(output_folder, "DMAT_Initialization_Summary.csv")
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
