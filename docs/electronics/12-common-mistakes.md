# Common Mistakes

A catalog of frequent circuit design errors and how to avoid them.

## Power and Thermal

### Not Checking Power Dissipation
Every component that drops voltage while carrying current dissipates power as heat. **Always calculate P = V * I for every component in the signal path.**

The most common offenders:
- Voltage regulators (especially linear, dropping large voltages)
- Current-limiting resistors at high current
- Transistors in the linear region (during switching transitions or when used as a pass element)
- LEDs driven from high-voltage supplies

### Exceeding Absolute Maximum Ratings
Datasheet absolute maximum ratings are destruction limits, not operating conditions. **Design to stay within the recommended operating conditions**, not the absolute maximum.

- V_GS(max) on a MOSFET: exceeding this by even 1V for 1μs can destroy the gate oxide permanently
- Reverse voltage on electrolytic capacitors: can cause explosion
- Junction temperature on semiconductors: causes immediate or latent failure

### Ignoring Transient Conditions
The circuit may be fine at steady state but fail during:
- **Power-up:** Capacitors are discharged, regulators haven't started, logic is in undefined states
- **Power-down:** Voltages decay at different rates, creating unexpected voltage differences
- **Load transients:** Sudden current demand causes supply voltage dips
- **Input transients:** Automotive load dump, ESD, lightning (nearby)

## Grounding Errors

### Ground as a Perfect Conductor
Ground traces have resistance and inductance. Current through ground traces creates voltage drops. A 100mΩ ground trace carrying 1A has a 100mV drop — enough to corrupt a 12-bit ADC measurement.

**Fix:** Use a ground plane, star grounding, or Kelvin sensing.

### Mixing Analog and Digital Ground Returns
Digital switching currents flowing through analog ground creates noise on analog measurements.

**Fix:** Separate ground regions, connected at one point near the power supply. Route digital return currents through the digital ground area.

### Ground Loops
When two grounded instruments are connected, their different ground potentials drive current through the signal cable's ground wire, creating noise.

**Fix:** Use differential signaling. Break the ground loop with isolation (optocouplers, transformers, isolated power supplies).

## Component Selection Errors

### Using Voltage Dividers as Power Supplies
A voltage divider only works if the load current is negligible. Loading a voltage divider changes the output voltage and wastes power.

**Fix:** Use a voltage regulator. Reserve voltage dividers for sensing and biasing only.

### Ignoring Ceramic Capacitor Derating
A "10μF" X5R ceramic capacitor may have only 2μF at its rated voltage. The capacitance drops with DC bias.

**Fix:** Use 2x voltage rating, or use a larger value and verify with the manufacturer's derating curve. For timing circuits, use C0G/NP0 ceramics (no voltage derating).

### Wrong Capacitor Type for the Application
| Application | Wrong Choice | Right Choice |
|-------------|-------------|-------------|
| Timing/oscillator | Electrolytic (leaky, poor tolerance) | Film or C0G ceramic |
| Bypass cap | Electrolytic alone (too much ESR) | Ceramic 100nF + electrolytic |
| Power supply output | Ceramic only (not enough bulk) | Ceramic + electrolytic |
| DC blocking (audio) | X7R ceramic (microphonic) | Film capacitor |

### Assuming Typical β for BJT Design
BJT current gain varies 3:1 or more between individual devices of the same type. A circuit that works with β = 200 may fail with β = 80.

**Fix:** Design for β_min (from datasheet). Use overdrive factor of 3–10x for switches. For amplifiers, use voltage divider biasing that's insensitive to β.

### Not Checking Component Availability
Designing with obsolete, out-of-stock, or long-lead-time parts wastes the entire design effort.

**Fix:** Check availability on major distributors (Digi-Key, Mouser, LCSC) before committing to a part. Prefer parts with multiple sources.

## Circuit Topology Errors

### No Flyback Diode on Inductive Loads
When current through an inductor (relay, motor, solenoid) is interrupted, the inductor generates a voltage spike that destroys the switching transistor.

**Fix:** Always add a flyback diode reverse-biased across inductive loads.

### Floating Inputs
CMOS inputs left unconnected can float to any voltage, oscillate, or draw excessive current (both transistors partially on). This causes:
- Unpredictable behavior
- Excessive power consumption
- Oscillation and noise

**Fix:** Tie all unused CMOS inputs to VCC or GND (check datasheet for the safe state). Add pull-up or pull-down resistors on inputs that may be temporarily undriven.

### No Bypass Capacitors
ICs without bypass capacitors malfunction in subtle ways — increased noise, reduced timing accuracy, intermittent glitches, susceptibility to nearby interference.

**Fix:** 100nF ceramic capacitor on every IC's power pins, as close to the IC as physically possible. No exceptions.

### Driving Capacitive Loads from Op-Amps
Most op-amps become unstable when driving capacitive loads (>100pF). The capacitance adds a pole inside the feedback loop, reducing phase margin.

**Fix:** Add a small series resistor (10–100Ω) between the op-amp output and the capacitive load. This isolates the capacitance from the feedback loop.

### Unprotected GPIO Pins
Microcontroller and FPGA I/O pins can be damaged by:
- Voltages above VCC + 0.3V or below GND - 0.3V
- ESD events
- Inductive kickback
- Accidental connection to a different voltage domain

**Fix:** Add series resistors (100Ω–1kΩ) and ESD clamp diodes on any pin connected to the outside world.

## SPICE Simulation Pitfalls

### Trusting Ideal Models
SPICE default models are ideal — zero-ESR capacitors, noiseless resistors, infinite-bandwidth op-amps. Real circuits have parasitics that SPICE won't show unless you model them.

**Fix:** Use realistic models. Add ESR to capacitors (especially electrolytics). Use manufacturer SPICE models for ICs when available.

### Wrong Convergence Settings
SPICE may fail to converge or give wrong results with default settings when:
- Circuits have very high gain (feedback loops with >60dB loop gain)
- Circuits have abrupt transitions (comparators, switching regulators)
- Initial conditions are far from the operating point

**Fix:** Try `.options reltol=0.001` (tighter tolerance) or `.options ITL1=500` (more iterations). Set initial conditions with `.ic` statements. For oscillators, add a startup perturbation.

### Not Running Long Enough
Transient simulations must run long enough for the circuit to reach steady state. An oscillator takes several cycles to stabilize. A feedback loop takes several time constants to settle.

**Fix:** Run the transient analysis for at least 5–10 periods of the lowest frequency of interest. For RC circuits, run for at least 5 * τ (time constant).

### Forgetting SPICE Unit Conventions
SPICE uses different case conventions than standard engineering notation:
- `M` = milli (10^-3), NOT mega
- `MEG` = mega (10^6)
- `mil` = 25.4 μm (a unit of length, not milli)

Writing `1M` when you mean 1 megaohm gives you 1 milliohm — a factor of 10^9 error.

## Signal Integrity

### Impedance Mismatch in High-Speed Signals
Signals with rise times faster than twice the propagation delay of the trace need impedance matching. For FR4 PCB, propagation is roughly 6 inches/ns, so a 2ns rise time needs matching for traces longer than 6 inches.

**Fix:** Use controlled-impedance traces (50Ω or 100Ω differential) with proper termination.

### Crosstalk Between Traces
Parallel traces couple capacitively and inductively. Coupling increases with:
- Longer parallel runs
- Closer spacing
- Faster rise/fall times

**Fix:** Maintain spacing ≥ 3x trace width between sensitive signals. Use ground traces or ground planes between critical signals. Route sensitive signals on different layers with orthogonal orientation.

### Antenna Behavior of Traces
Any conductor can act as an antenna, both radiating and receiving. A trace becomes an efficient antenna when its length approaches λ/4 at the signal frequency (or harmonic).

**Fix:** Keep high-speed signal traces short. Use ground planes. Add filtering at connectors. Enclose the circuit in a grounded metal enclosure for EMI compliance.
