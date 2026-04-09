#!/usr/bin/env python3
"""Convert a circuit JSON description to an ngspice netlist (.cir) file.

Usage:
    python3 json2netlist.py <input.json> <output.cir>
    python3 json2netlist.py < input.json > output.cir
"""

import json
import sys
import re

# ---------------------------------------------------------------------------
# Built-in SPICE models and subcircuits
# ---------------------------------------------------------------------------

BUILTIN_MODELS = {
    "LED_RED": ".model LED_RED D(IS=1e-20 N=1.8 RS=5 BV=5 IBV=100u EG=1.9 CJO=20p)",
    "LED_GREEN": ".model LED_GREEN D(IS=1e-20 N=2.0 RS=6 BV=5 IBV=100u EG=2.2 CJO=20p)",
    "LED_BLUE": ".model LED_BLUE D(IS=1e-20 N=2.5 RS=8 BV=5 IBV=100u EG=2.8 CJO=20p)",
    "1N4148": ".model 1N4148 D(IS=2.52e-9 N=1.752 RS=0.568 BV=100 IBV=100u CJO=4p)",
    "1N4001": ".model 1N4001 D(IS=29.5e-9 N=1.73 RS=0.17 BV=50 IBV=5u CJO=25p)",
    "2N3904": ".model 2N3904 NPN(IS=6.734f BF=416.4 NF=1.259 VAF=74.03 IKF=66.78m ISE=6.734f NE=1.259 BR=0.7389 NR=2 VAR=28 IKR=0.7389 ISC=0 NC=2 RB=10 RE=0 RC=1 CJE=3.638p CJC=4.493p TF=301.2p TR=239.5n)",
    "2N3906": ".model 2N3906 PNP(IS=1.41f BF=180.7 NF=1.5 VAF=18.7 IKF=80m ISE=0 NE=1.5 BR=4.977 NR=2 VAR=20 IKR=0 ISC=0 NC=2 RB=10 RE=0 RC=2.5 CJE=9.728p CJC=4.067p TF=500p TR=67n)",
}

# NE555 behavioral subcircuit for ngspice
BUILTIN_SUBCIRCUITS = {
    "NE555": """\
* NE555 behavioral model for ngspice
* Pins: GND TRIG OUT RESET CTRL THRESH DISCH VCC
.subckt NE555 GND TRIG OUT RESET CTRL THRESH DISCH VCC
* Internal voltage references
R_ctrl VCC CTRL_INT 5k
R_ctrl2 CTRL_INT GND_INT 5k
R_ctrl3 GND_INT GND 5k
* Control voltage output (2/3 VCC by default)
R_cv CTRL_INT CTRL 10
* Comparator thresholds
* Upper comparator: THRESH vs CTRL (2/3 VCC)
B_upper_cmp upper_cmp GND V = V(THRESH,GND) > V(CTRL,GND) ? 5 : 0
* Lower comparator: TRIG vs 1/2 CTRL (1/3 VCC)
B_lower_cmp lower_cmp GND V = V(TRIG,GND) < V(CTRL,GND)/2 ? 5 : 0
* SR latch (behavioral)
* S = lower_cmp (set when TRIG < 1/3 VCC)
* R = upper_cmp OR !RESET (reset when THRESH > 2/3 VCC or RESET low)
B_reset reset_active GND V = V(RESET,GND) < 0.7 ? 5 : 0
B_latch_r latch_r GND V = (V(upper_cmp,GND) > 2.5) + (V(reset_active,GND) > 2.5) > 0.5 ? 5 : 0
* Simple SR latch using RC + behavioral
R_sr sr_node GND 1Meg
C_sr sr_node GND 1n IC=0
B_sr_drive sr_drive GND V = V(lower_cmp,GND) > 2.5 ? 5 : (V(latch_r,GND) > 2.5 ? 0 : V(sr_node,GND))
R_sr_couple sr_drive sr_node 100
* Output stage
B_out OUT GND V = V(sr_node,GND) > 2.5 ? (V(VCC,GND) - 1.5) : 0.1
* Discharge transistor (smooth behavioral conductance — avoids switch convergence)
* When sr_node LOW (output high): discharge OFF (high impedance)
* When sr_node HIGH→LOW: discharge ON (50 ohm to ground)
B_disch DISCH GND I = V(DISCH,GND) / (50 + 1e6 * (1 + tanh((V(sr_node,GND) - 2.5) * 10)) / 2)
.ends NE555""",
}

# SPICE element prefixes for component types
ELEMENT_PREFIXES = {
    "R": "R",
    "C": "C",
    "L": "L",
    "D": "D",
    "vdc": "V",
    "vac": "V",
    "vpulse": "V",
    "idc": "I",
}

# Components that use subcircuits (instantiated with X prefix)
SUBCIRCUIT_TYPES = set(BUILTIN_SUBCIRCUITS.keys())


def parse_value(val):
    """Pass through value strings — ngspice handles SI suffixes natively."""
    return str(val)


def generate_component_line(comp):
    """Generate a SPICE netlist line for a single component."""
    ref = comp["ref"]
    ctype = comp["type"]

    # Subcircuit instance (IC)
    if ctype in SUBCIRCUIT_TYPES:
        pins = comp["pins"]
        # NE555 pin order: GND TRIG OUT RESET CTRL THRESH DISCH VCC
        pin_order = {
            "NE555": ["GND", "TRIG", "OUT", "RESET", "CTRL", "THRESH", "DISCH", "VCC"],
        }
        order = pin_order.get(ctype)
        if order is None:
            order = sorted(pins.keys())
        node_list = " ".join(pins[p] for p in order)
        prefix = ref if ref.upper().startswith("X") else f"X{ref}"
        return f"{prefix} {node_list} {ctype}"

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


def collect_models(components):
    """Determine which .model and .subckt cards are needed."""
    models_needed = set()
    subcircuits_needed = set()

    for comp in components:
        ctype = comp["type"]
        if ctype in SUBCIRCUIT_TYPES:
            subcircuits_needed.add(ctype)
        model = comp.get("model")
        if model and model in BUILTIN_MODELS:
            models_needed.add(model)

    return models_needed, subcircuits_needed


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


def convert(circuit):
    """Convert a circuit dict to ngspice netlist lines."""
    title = circuit.get("title", "Untitled Circuit")
    components = circuit["components"]
    analysis = circuit["analysis"]
    plots = circuit.get("plots", [])

    lines = [f"* {title}", ""]

    # Collect and emit models/subcircuits
    models_needed, subcircuits_needed = collect_models(components)

    if subcircuits_needed:
        lines.append("* --- Subcircuit definitions ---")
        for name in sorted(subcircuits_needed):
            lines.append(BUILTIN_SUBCIRCUITS[name])
            lines.append("")

    if models_needed:
        lines.append("* --- Device models ---")
        for name in sorted(models_needed):
            lines.append(BUILTIN_MODELS[name])
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

    # Control block (always include .control/run for batch mode)
    if plots:
        lines.extend(generate_plots(plots))
    else:
        lines.extend([".control", "run", ".endc"])
    lines.append("")

    lines.append(".end")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) == 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        with open(input_path) as f:
            circuit = json.load(f)
        netlist = convert(circuit)
        with open(output_path, "w") as f:
            f.write(netlist)
        print(f"Wrote netlist to {output_path}")
    elif len(sys.argv) == 1:
        circuit = json.load(sys.stdin)
        sys.stdout.write(convert(circuit))
    else:
        print(f"Usage: {sys.argv[0]} [input.json output.cir]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
