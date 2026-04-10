#!/usr/bin/env python3
"""Convert a circuit JSON description to an ngspice netlist (.cir) file.

Usage:
    python3 json2netlist.py <input.json> <output.cir> [--models-dir <path>]
    python3 json2netlist.py < input.json > output.cir
"""

import json
import os
import sys
import re


def parse_value(val):
    """Pass through value strings — ngspice handles SI suffixes natively."""
    return str(val)


def generate_component_line(comp):
    """Generate a SPICE netlist line for a single component."""
    ref = comp["ref"]
    ctype = comp["type"]

    # Subcircuit instance (IC) — referenced via .include from external model library
    if ctype.startswith("X") or "pins" in comp:
        pins = comp["pins"]
        pin_order = comp.get("pin_order")
        if pin_order is None:
            pin_order = sorted(pins.keys())
        node_list = " ".join(pins[p] for p in pin_order)
        subckt_name = comp.get("subcircuit", ctype)
        prefix = ref if ref.upper().startswith("X") else f"X{ref}"
        return f"{prefix} {node_list} {subckt_name}"

    # BJT transistor (Q prefix, 3 nodes: collector, base, emitter + model)
    if ctype == "Q":
        nodes = comp["nodes"]
        if len(nodes) != 3:
            raise ValueError(f"{ref}: BJT requires 3 nodes [collector, base, emitter], got {len(nodes)}")
        model = comp.get("model", "Q_DEFAULT")
        c, b, e = nodes
        prefix = ref if ref.upper().startswith("Q") else f"Q{ref}"
        return f"{prefix} {c} {b} {e} {model}"

    # Two-terminal components
    nodes = comp["nodes"]
    if len(nodes) != 2:
        raise ValueError(f"{ref}: expected 2 nodes, got {len(nodes)}")

    n1, n2 = nodes

    if ctype in ("R", "C", "L"):
        value = parse_value(comp["value"])
        return f"{ref} {n1} {n2} {value}"

    if ctype == "D":
        model = comp.get("model", "D_DEFAULT")
        return f"{ref} {n1} {n2} {model}"

    if ctype == "vdc":
        value = parse_value(comp["value"])
        prefix = ref if ref.upper().startswith("V") else f"V{ref}"
        return f"{prefix} {n1} {n2} DC {value}"

    if ctype == "vac":
        dc = comp.get("dc", "0")
        amp = parse_value(comp["value"])
        freq = parse_value(comp["freq"])
        prefix = ref if ref.upper().startswith("V") else f"V{ref}"
        return f"{prefix} {n1} {n2} DC {dc} AC {amp} SIN(0 {amp} {freq})"

    if ctype == "vpulse":
        params = comp["pulse"]
        prefix = ref if ref.upper().startswith("V") else f"V{ref}"
        v1 = params.get("v1", "0")
        v2 = params.get("v2", "5")
        td = params.get("td", "0")
        tr = params.get("tr", "1n")
        tf = params.get("tf", "1n")
        pw = params.get("pw", "1m")
        per = params.get("per", "2m")
        return f"{prefix} {n1} {n2} PULSE({v1} {v2} {td} {tr} {tf} {pw} {per})"

    if ctype in ("idc",):
        value = parse_value(comp["value"])
        prefix = ref if ref.upper().startswith("I") else f"I{ref}"
        return f"{prefix} {n1} {n2} DC {value}"

    raise ValueError(f"{ref}: unknown component type '{ctype}'")


def resolve_includes(includes, models_dir):
    """Resolve include paths and validate they exist. Returns list of absolute paths."""
    resolved = []
    for inc in includes:
        # Try as-is (absolute or relative to CWD)
        if os.path.isfile(inc):
            resolved.append(os.path.abspath(inc))
            continue
        # Try relative to models_dir
        candidate = os.path.join(models_dir, inc)
        if os.path.isfile(candidate):
            resolved.append(os.path.abspath(candidate))
            continue
        # Try inside kicad-spice-library
        candidate = os.path.join(models_dir, "kicad-spice-library", inc)
        if os.path.isfile(candidate):
            resolved.append(os.path.abspath(candidate))
            continue
        raise FileNotFoundError(
            f"Model file not found: '{inc}'\n"
            f"  Searched: {inc}, {os.path.join(models_dir, inc)}, "
            f"{os.path.join(models_dir, 'kicad-spice-library', inc)}"
        )
    return resolved


def generate_analysis(analysis):
    """Generate the analysis control line."""
    atype = analysis["type"]

    if atype == "tran":
        step = analysis["step"]
        stop = analysis["stop"]
        uic = " UIC" if analysis.get("uic", False) else ""
        return f".tran {step} {stop}{uic}"

    if atype == "dc":
        source = analysis["source"]
        start = analysis["start"]
        stop = analysis["stop"]
        step = analysis["step"]
        return f".dc {source} {start} {stop} {step}"

    if atype == "ac":
        variation = analysis.get("variation", "dec")
        points = analysis["points"]
        fstart = analysis["fstart"]
        fstop = analysis["fstop"]
        return f".ac {variation} {points} {fstart} {fstop}"

    raise ValueError(f"Unknown analysis type: {atype}")


def generate_plots(plots):
    """Generate .control block for plots."""
    lines = [".control", "run"]
    for plot in plots:
        signals = " ".join(plot["signals"])
        lines.append(f"plot {signals}")
    lines.append(".endc")
    return lines


def generate_meas_statements(measures):
    """Generate ngspice .meas statements and a meta structure for check_measures.py.

    Returns (netlist_lines, meta_entries) where meta_entries carry the mapping
    from measure IDs to ngspice variable names, computation type, and acceptance
    criteria.
    """
    lines = []
    meta = []

    for m in measures:
        mid = m["id"]
        mtype = m["type"]
        signal = m["signal"]
        desc = m.get("description", "")
        accept = m["accept"]
        from_t = m.get("from")
        to_t = m.get("to")

        def _window():
            parts = []
            if from_t:
                parts.append(f"from={from_t}")
            if to_t:
                parts.append(f"to={to_t}")
            return " ".join(parts)

        def _edge_keyword():
            edge = m.get("edge", "rising")
            return "RISE" if edge == "rising" else "FALL"

        if mtype in ("max", "min", "avg", "rms"):
            var = f"{mid}_{mtype}"
            lines.append(f".meas tran {var} {mtype.upper()} {signal} {_window()}")
            meta.append({
                "id": mid, "description": desc, "computation": "direct",
                "variables": [var],
                "accept_min": accept["min"], "accept_max": accept["max"],
            })

        elif mtype == "peak_to_peak":
            var_max = f"{mid}_max"
            var_min = f"{mid}_min"
            lines.append(f".meas tran {var_max} MAX {signal} {_window()}")
            lines.append(f".meas tran {var_min} MIN {signal} {_window()}")
            meta.append({
                "id": mid, "description": desc, "computation": "difference",
                "variables": [var_max, var_min],
                "accept_min": accept["min"], "accept_max": accept["max"],
            })

        elif mtype == "frequency":
            edge_kw = _edge_keyword()
            td = from_t or "0"
            var1 = f"{mid}_cross1"
            var2 = f"{mid}_cross2"
            lines.append(f".meas tran {var1} WHEN {signal}={m['threshold']} {edge_kw}=1 TD={td}")
            lines.append(f".meas tran {var2} WHEN {signal}={m['threshold']} {edge_kw}=2 TD={td}")
            meta.append({
                "id": mid, "description": desc, "computation": "reciprocal_difference",
                "variables": [var1, var2],
                "accept_min": accept["min"], "accept_max": accept["max"],
            })

        elif mtype == "period":
            edge_kw = _edge_keyword()
            td = from_t or "0"
            var1 = f"{mid}_cross1"
            var2 = f"{mid}_cross2"
            lines.append(f".meas tran {var1} WHEN {signal}={m['threshold']} {edge_kw}=1 TD={td}")
            lines.append(f".meas tran {var2} WHEN {signal}={m['threshold']} {edge_kw}=2 TD={td}")
            meta.append({
                "id": mid, "description": desc, "computation": "plain_difference",
                "variables": [var1, var2],
                "accept_min": accept["min"], "accept_max": accept["max"],
            })

        elif mtype == "duty_cycle":
            td = from_t or "0"
            var_rise1 = f"{mid}_rise1"
            var_fall1 = f"{mid}_fall1"
            var_rise2 = f"{mid}_rise2"
            lines.append(f".meas tran {var_rise1} WHEN {signal}={m['threshold']} RISE=1 TD={td}")
            lines.append(f".meas tran {var_fall1} WHEN {signal}={m['threshold']} FALL=1 TD={td}")
            lines.append(f".meas tran {var_rise2} WHEN {signal}={m['threshold']} RISE=2 TD={td}")
            meta.append({
                "id": mid, "description": desc, "computation": "ratio",
                "variables": [var_rise1, var_fall1, var_rise2],
                "accept_min": accept["min"], "accept_max": accept["max"],
            })

        elif mtype == "find_when":
            edge_kw = _edge_keyword()
            td = m.get("td", "0")
            var = f"{mid}_when"
            lines.append(f".meas tran {var} WHEN {signal}={m['value']} {edge_kw}=1 TD={td}")
            meta.append({
                "id": mid, "description": desc, "computation": "direct",
                "variables": [var],
                "accept_min": accept["min"], "accept_max": accept["max"],
            })

        else:
            raise ValueError(f"Unknown measure type: {mtype}")

    return lines, meta


def convert(circuit, models_dir=None):
    """Convert a circuit dict to ngspice netlist lines."""
    title = circuit.get("title", "Untitled Circuit")
    components = circuit["components"]
    analysis = circuit["analysis"]
    plots = circuit.get("plots", [])
    measures = circuit.get("measures", [])
    includes = circuit.get("includes", [])

    lines = [f"* {title}", ""]

    # Include external model files
    if includes:
        if models_dir is None:
            # Default: models/ relative to repo root (parent of tools/)
            models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
        resolved = resolve_includes(includes, models_dir)
        lines.append("* --- Model includes ---")
        for path in resolved:
            lines.append(f".include {path}")
        lines.append("")

    # Simulation options
    lines.append("* --- Options ---")
    lines.append(".options reltol=1e-3 abstol=1e-9 method=gear")
    lines.append("")

    # Component instances
    lines.append("* --- Circuit ---")
    for comp in components:
        lines.append(generate_component_line(comp))
    lines.append("")

    # Analysis
    lines.append("* --- Analysis ---")
    lines.append(generate_analysis(analysis))
    lines.append("")

    # Measurement statements (placed before .control block)
    meas_meta = []
    if measures:
        meas_lines, meas_meta = generate_meas_statements(measures)
        lines.append("* --- Measurements ---")
        lines.extend(meas_lines)
        lines.append("")

    # Control block (always include .control/run for batch mode)
    if plots:
        lines.extend(generate_plots(plots))
    else:
        lines.extend([".control", "run", ".endc"])
    lines.append("")

    lines.append(".end")
    return "\n".join(lines) + "\n", meas_meta


def main():
    models_dir = None
    args = sys.argv[1:]

    # Parse --models-dir flag
    if "--models-dir" in args:
        idx = args.index("--models-dir")
        if idx + 1 < len(args):
            models_dir = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            print("Error: --models-dir requires a path argument", file=sys.stderr)
            sys.exit(1)

    if len(args) == 2:
        input_path = args[0]
        output_path = args[1]
        with open(input_path) as f:
            circuit = json.load(f)
        netlist, meas_meta = convert(circuit, models_dir)
        with open(output_path, "w") as f:
            f.write(netlist)
        print(f"Wrote netlist to {output_path}")
        if meas_meta:
            meta_path = os.path.splitext(output_path)[0] + ".measures_meta.json"
            with open(meta_path, "w") as f:
                json.dump({"measures": meas_meta}, f, indent=2)
            print(f"Wrote measures meta to {meta_path}")
    elif len(args) == 0:
        circuit = json.load(sys.stdin)
        netlist, _ = convert(circuit, models_dir)
        sys.stdout.write(netlist)
    else:
        print(f"Usage: {sys.argv[0]} [input.json output.cir] [--models-dir <path>]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
