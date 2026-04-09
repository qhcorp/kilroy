#!/usr/bin/env python3
"""Run an ngspice simulation and verify .meas results against acceptance criteria.

Usage:
    python3 check_measures.py <netlist.cir> <measures_meta.json>

Exit codes:
    0 — all measures pass
    1 — one or more measures failed acceptance criteria
    2 — ngspice failed to run (convergence, syntax error, etc.)
    3 — one or more .meas statements could not be evaluated
"""

import json
import os
import re
import subprocess
import sys

# Regex for ngspice measurement output lines, e.g.:
#   output_high_max     =  1.82830e+00 at=  5.00000e+00
#   led_blink_freq_cross1  =  1.50234e+00
# The value may be followed by "at= ..." or "from= ... to= ..." which we ignore.
MEAS_RE = re.compile(
    r"^\s*(\w+)\s*=\s*([+-]?\d+\.?\d*(?:e[+-]?\d+)?)",
    re.MULTILINE | re.IGNORECASE,
)

# Regex for failed measurements, e.g.:
#  .meas tran led_blink_freq_cross1 when v(out)=2.5 rise=1 td=1s failed!
MEAS_FAILED_RE = re.compile(
    r"^\s*\.meas\s+tran\s+(\w+)\s+.*failed!\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def run_ngspice(netlist_path):
    """Run ngspice in batch mode and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        ["ngspice", "-b", netlist_path],
        capture_output=True, text=True, timeout=300,
    )
    return result.returncode, result.stdout, result.stderr


def parse_measurements(output):
    """Parse ngspice stdout+stderr for measurement results.

    Returns a dict mapping variable names to float values.
    Variables that ngspice reports as 'failed!' are mapped to None.
    """
    values = {}
    # First, find successful measurements
    for match in MEAS_RE.finditer(output):
        name = match.group(1)
        try:
            values[name] = float(match.group(2))
        except ValueError:
            pass
    # Then, mark failed measurements
    for match in MEAS_FAILED_RE.finditer(output):
        name = match.group(1)
        values[name] = None
    return values


def compute_measure(meta, parsed):
    """Compute a single measure's value from parsed ngspice variables.

    Returns (value, error_string). value is None if computation failed.
    """
    variables = meta["variables"]
    computation = meta["computation"]

    # Check all variables are present and not failed
    vals = []
    for var in variables:
        if var not in parsed:
            return None, f"variable '{var}' not found in ngspice output"
        if parsed[var] is None:
            return None, f"ngspice could not evaluate '{var}'"
        vals.append(parsed[var])

    if computation == "direct":
        return vals[0], None

    if computation == "difference":
        # peak_to_peak: max - min
        return vals[0] - vals[1], None

    if computation == "reciprocal_difference":
        # frequency: 1 / (cross2 - cross1)
        diff = vals[1] - vals[0]
        if abs(diff) < 1e-15:
            return None, "crossing times are identical — cannot compute frequency"
        return 1.0 / diff, None

    if computation == "plain_difference":
        # period: cross2 - cross1
        return vals[1] - vals[0], None

    if computation == "ratio":
        # duty_cycle: (fall1 - rise1) / (rise2 - rise1)
        denom = vals[2] - vals[0]
        if abs(denom) < 1e-15:
            return None, "rise times are identical — cannot compute duty cycle"
        return (vals[1] - vals[0]) / denom, None

    return None, f"unknown computation type: {computation}"


def check_measures(meta_path, parsed):
    """Evaluate all measures against acceptance criteria.

    Returns (results_list, has_failures, has_errors).
    """
    with open(meta_path) as f:
        meta_doc = json.load(f)

    results = []
    has_failures = False
    has_errors = False

    for m in meta_doc["measures"]:
        value, error = compute_measure(m, parsed)
        entry = {
            "id": m["id"],
            "description": m.get("description", ""),
            "accept_min": m["accept_min"],
            "accept_max": m["accept_max"],
            "variables": {v: parsed.get(v) for v in m["variables"]},
        }

        if error:
            entry["status"] = "ERROR"
            entry["error"] = error
            entry["measured"] = None
            has_errors = True
        elif m["accept_min"] <= value <= m["accept_max"]:
            entry["status"] = "PASS"
            entry["measured"] = value
        else:
            entry["status"] = "FAIL"
            entry["measured"] = value
            has_failures = True

        results.append(entry)

    return results, has_failures, has_errors


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <netlist.cir> <measures_meta.json>", file=sys.stderr)
        sys.exit(2)

    netlist_path = sys.argv[1]
    meta_path = sys.argv[2]

    # Run simulation
    try:
        exit_code, stdout, stderr = run_ngspice(netlist_path)
    except FileNotFoundError:
        output = {
            "summary": "ERROR: ngspice not found",
            "ngspice_exit_code": -1,
            "pass": False,
            "error": "ngspice is not installed or not in PATH",
            "measures": [],
        }
        print(json.dumps(output, indent=2))
        sys.exit(2)
    except subprocess.TimeoutExpired:
        output = {
            "summary": "ERROR: ngspice timed out after 300s",
            "ngspice_exit_code": -1,
            "pass": False,
            "error": "simulation timed out",
            "measures": [],
        }
        print(json.dumps(output, indent=2))
        sys.exit(2)

    if exit_code != 0:
        # Check for common convergence errors
        combined = stdout + stderr
        error_msg = "ngspice exited with non-zero status"
        for pattern in ["singular matrix", "no convergence", "timestep too small"]:
            if pattern in combined.lower():
                error_msg = f"ngspice simulation failed: {pattern}"
                break
        output = {
            "summary": f"ERROR: {error_msg}",
            "ngspice_exit_code": exit_code,
            "pass": False,
            "error": error_msg,
            "ngspice_stderr": stderr[:4000],
            "measures": [],
        }
        print(json.dumps(output, indent=2))
        sys.exit(2)

    # Parse measurements from combined stdout+stderr (ngspice prints to both)
    parsed = parse_measurements(stdout + "\n" + stderr)

    # Check against acceptance criteria
    results, has_failures, has_errors = check_measures(meta_path, parsed)

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    if has_errors:
        summary = f"ERROR: {errors} of {total} measures could not be evaluated"
    elif has_failures:
        summary = f"FAIL: {failed} of {total} measures failed"
    else:
        summary = f"PASS: {passed} of {total} measures passed"

    output = {
        "summary": summary,
        "ngspice_exit_code": exit_code,
        "pass": not has_failures and not has_errors,
        "measures": results,
    }

    # Write results file next to the netlist
    results_path = os.path.join(os.path.dirname(netlist_path), "measures_results.json")
    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)

    # Print to stdout for Kilroy tool.output capture
    print(json.dumps(output, indent=2))

    if has_errors:
        sys.exit(3)
    elif has_failures:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
