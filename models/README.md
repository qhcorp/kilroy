# SPICE Model Library

This directory contains SPICE model files used by `tools/json2netlist.py` to generate ngspice netlists.

## External Libraries

### KiCad-Spice-Library

Community-maintained collection of ngspice-compatible SPICE models, vendored at `kicad-spice-library/`.

- **Source**: https://github.com/kicad-spice-library/KiCad-Spice-Library
- **Contents**: ~1,100 model files (.lib, .mod, .sub) covering transistors, diodes, op-amps, ICs, etc.
- **Update**: Re-clone from source and replace the directory

## How Models Are Used

Circuit JSON files reference model files via the `includes` array:

```json
{
  "includes": ["Models/Diode/led.lib", "Models/Manufacturer/TRT-Electronics/2n3904.lib"],
  "components": [...]
}
```

`json2netlist.py` resolves these paths relative to the models directory and emits `.include` directives in the generated netlist.

## Compatibility Notes

Some models use LTspice-specific A-device syntax (SCHMITT, SRFLOP) that requires ngspice XSPICE mode. Prefer models built from standard SPICE primitives (R, C, D, MOSFET) when possible. Always test a model with `ngspice -b` before relying on it in a pipeline.
