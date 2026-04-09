# Design Brief: 48V Battery Support for E-MAAX PRO X Regulator

## 1. Objective

Extend the E-MAAX PRO X7 alternator regulator to support 48V nominal battery systems in addition to the existing 12V and 24V systems, across all currently supported battery chemistries (Lead-acid, AGM, Gel, Carbon Foam/FireFly, LiFePO4, generic Lithium, and custom profiles).

## 2. Current Design Summary

The E-MAAX PRO X7 is a microcontroller-based marine alternator regulator built around a PIC32MX570F512L MCU. It controls alternator field output via PWM-driven power MOSFETs to regulate battery charging through Warm-up, Bulk+Absorb, and Float stages. The system includes:

- **Power MOSFETs**: SUM70090E (N-CH, 100V/50A) and SQM50P08-25L (P-CH, 80V/50A) for field drive
- **Internal power supply**: MC34063A buck/boost converter producing ~7.5V rail, followed by LD2981 linear regulators for 5V and 3.3V logic rails
- **Sensing**: MCP3428 16-bit sigma-delta ADC for current shunt measurements; PIC32 internal ADC (10-bit) for voltage sensing via resistor dividers
- **Interfaces**: USB (via PIC32 USB peripheral), Wi-Fi (ESP32-WROOM-32E), NMEA-2000/CAN (MCP2562 transceiver), regulator-to-regulator opto-isolated serial link
- **Protection**: TVS diodes (MMBZ27VCL, 22V working), zener clamps, PTC resettable fuses, reverse polarity protection

**Current electrical limits:**

| Parameter | Rating |
|---|---|
| Maximum operating supply voltage | 40V |
| Maximum voltage at Battery Voltage Sensor leads | 40V |
| Maximum voltage at Alternator Current Shunt leads | 40V |
| Maximum operating Field current | 20A |

The system auto-detects 12V or 24V at power-up and scales all regulation parameters accordingly. The "Detected System Voltage" parameter currently accepts values of 12, 24, or 0 (not detected).

## 3. 48V System Voltage Requirements

A 48V nominal battery system operates across a significantly wider voltage range than the current 40V maximum:

| Chemistry | Nominal (V) | Bulk/Absorb Target (V) | Float Target (V) | Max Expected (V) |
|---|---|---|---|---|
| Lead-acid (24-cell) | 48.0 | 57.6 | 54.0 | ~60 |
| AGM (24-cell) | 48.0 | 57.6-58.8 | 54.0-55.2 | ~60 |
| Gel (24-cell) | 48.0 | 56.4-57.6 | 54.0-55.2 | ~59 |
| LiFePO4 (16S) | 51.2 | 57.6 | 54.4-55.2 | ~58.5 |
| Carbon Foam (24-cell) | 48.0 | 57.6-58.8 | 54.0-55.2 | ~60 |

**Design voltage envelope**: The regulator must operate reliably across **36V-62V** at the B+ supply input to accommodate deeply discharged through fully charging 48V batteries, with transient tolerance to **~70V** for load-dump and alternator overshoot events.

## 4. Impact Analysis & Required Changes

### 4.1 Power Supply Path (CRITICAL)

**Problem**: The MC34063A buck/boost converter currently steps the battery bus voltage down to ~7.5V for the logic supply chain. The MC34063A has a maximum input voltage of 40V, which is insufficient for 48V systems.

**Options**:
- **A) Replace MC34063A** with a wide-input buck converter rated for 80V+ input (e.g., LM5164 or TPS54260 family). This is the cleanest solution but requires PCB layout changes in the power supply section.
- **B) Add a pre-regulator stage** ahead of the MC34063A (e.g., a simple resistor-zener pre-drop or a high-voltage LDO). Less efficient but minimizes board changes.
- **Recommendation**: Option A. The MC34063A is used for multiple internal supply functions and a purpose-built wide-input buck will be more efficient and reliable at 48V+ input. The 220uH inductor (SRR1210-221M, 1.7A) and associated passives will also need to be re-evaluated for the new converter.

**Downstream regulators**: The LD2981CU50TR (5V) and LD2981CU33TR (3.3V) are fed from the ~7.5V intermediate rail, not directly from the battery bus, so they remain valid as long as the intermediate rail stays in range.

### 4.2 Power MOSFETs (OK with margin concerns)

- **SUM70090E** (N-CH, 100V, 50A): Adequate for 48V. At 60V charging voltage, Vds margin is ~40V. Acceptable.
- **SQM50P08-25L** (P-CH, 80V, 50A): Marginal. At 60V + transients, this leaves only ~20V margin. For a marine environment with alternator load-dump transients, this is risky.

**Recommendation**: Replace the P-CH MOSFET with an 100V+ rated part (e.g., SQM50P10 series or equivalent) or add transient clamping. Evaluate whether the existing TVS/snubber network provides sufficient clamping.

### 4.3 Voltage Sensing (REQUIRES RESCALING)

The battery voltage is measured via a resistor divider feeding the PIC32's 10-bit ADC (0-3.3V input range). The current divider is scaled for a 0-40V input range.

**For 48V support**: The divider ratio must be changed to accommodate 0-70V input while maintaining adequate resolution. At 10-bit/3.3V, a 70V full-scale gives ~68mV/count. For the current "Regulation Band" parameter (default 0.05V tolerance), this requires at least 1 count of resolution, which is achievable but tight.

**Options**:
- **A) Switchable divider**: Use an analog mux or FET-switched resistor to select the divider ratio based on detected system voltage. Preserves resolution at 12V/24V.
- **B) Fixed wider-range divider**: Simple but reduces voltage resolution at 12V by ~1.75x.
- **C) External ADC for voltage**: Route battery voltage through the MCP3428 (16-bit) instead of the PIC32 internal ADC. This provides 1uV-level resolution regardless of range, but requires firmware rework and may consume one of the limited MCP3428 channels.
- **Recommendation**: Option B for minimum hardware change, with firmware compensation. The MCP3428 is already used for current sensing and may not have spare channels. The 68mV resolution at 48V is adequate for regulation within the 0.05V band when combined with the regulation algorithm's averaging.

### 4.4 Current Sensing (LARGELY OK)

The MCP3428 ADC measures voltage across external shunts. The shunt voltage is low (50mV at 500A full scale) and independent of system voltage. The shunt signal conditioning path should be unaffected.

**However**: The "Maximum operating voltage at Alternator Current Shunt leads" is currently 40V. The alternator-side shunt sits at the battery bus potential. For 48V systems, the common-mode voltage at the shunt amplifier/ADC input will exceed 40V.

**Action**: Verify the input protection and common-mode rejection of the shunt signal path. The MCP3428 has differential inputs but limited common-mode range. If the shunt signal is referenced to battery ground (as indicated by the harness pinout), the differential signal remains in range but the protection components (TVS, zener clamps) on the shunt leads need to be rated for the higher bus voltage.

### 4.5 TVS and Protection Diodes (MUST BE UPGRADED)

- **MMBZ27VCL** (22V working, 38V clamp): Used for bus-referenced signal protection. Must be replaced with higher-voltage variants for any signal that rides at battery potential.
- **Zener diodes**: BZX84C5V1 (5.1V) and BZX84C10 (10V) used for logic-level clamping are OK. BZX84C3V3 (3.3V) for logic rail clamping is OK.
- **BSS192P** (P-CH MOSFET, 250V): Used for high-side switching/protection. Adequate for 48V.

### 4.6 Electrolytic Capacitors

- **EEU-FS1K101** (100uF, 80V): Currently on the power bus. At 60V charging + transients, this is marginal. **Replace with 100V-rated capacitor**.
- **UVR1E471MPD** (470uF, 25V): Used on the intermediate 7.5V rail. Unaffected.

### 4.7 Ignition Input

The ignition input accepts 12V or 24V via the white wire. For 48V systems, the ignition source may be 48V. The input conditioning circuit (likely a voltage divider and/or zener clamp to MCU GPIO level) must handle 48V input.

**Action**: Review and potentially re-scale the ignition input divider/protection.

### 4.8 Firmware Changes

| Area | Change Required |
|---|---|
| System voltage detection | Add 48V detection (likely ~48V nominal at power-up) |
| Charge profile parameters | Add 48V voltage set points for all 8 profiles (0-7) |
| Voltage scaling | Update ADC-to-voltage conversion factors for the new divider ratio |
| Warning/Fault thresholds | Add 48V-appropriate thresholds for Warning Battery Voltage (currently 10-30V range) and Fault Battery Voltage (currently 10-30V range) — range must extend to ~62V |
| USB/Wi-Fi settings UI | Extend valid ranges for voltage parameters; add "48" to Detected System Voltage |
| NMEA-2000 reporting | Ensure PGN data fields accommodate 48V-range values |
| Regulator-to-regulator protocol | Verify peer state exchange handles 48V parameters |

### 4.9 Harness and Connectors

The existing power cable is 14 AWG with 300V insulation. At 48V and typical alternator field currents (up to 20A), the wiring is adequate. The 18 AWG signal leads are also sufficient. No harness changes required.

### 4.10 Thermal Considerations

Higher bus voltage at the same field current means higher power dissipation in the field drive MOSFETs if they operate in linear mode during transitions. The existing IP56 polypropylene enclosure with its thermal management must be evaluated for worst-case 48V operation. The existing regulator temperature fault (70C) and warning thresholds remain applicable.

## 5. Bill of Materials Changes Summary

| Current Part | Issue | Proposed Replacement | Notes |
|---|---|---|---|
| MC34063ADR (buck/boost, 40V max) | Input voltage exceeded | Wide-input buck (80V+ rated) | PCB layout change required |
| SQM50P08-25L (P-CH 80V MOSFET) | Marginal voltage margin | 100V+ P-CH MOSFET | Pin-compatible preferred |
| EEU-FS1K101 (100uF/80V cap) | Marginal at 60V + transients | 100V rated equivalent | Same footprint preferred |
| MMBZ27VCL (22Vwm TVS) | Working voltage exceeded | Higher-voltage TVS | SOT-23 footprint |
| Voltage divider resistors | Ratio change for 70V range | New values TBD | 0805 footprint, same positions |

All other components (PIC32MX, MCP3428, ESP32, MCP2562, LD2981 regulators, opto-couplers, current sense path, logic gates, connectors) remain unchanged.

## 6. PCB Impact Assessment

- **Minimal layout change** if a pin-compatible wide-input buck replaces the MC34063A in the same footprint area. The SRR1210 inductor footprint may need adjustment depending on the replacement converter's requirements.
- **Component swaps** (MOSFETs, capacitors, TVS) should target same-footprint replacements (TO-263, radial, SOT-23) to avoid PCB respins.
- **Resistor value changes** for voltage dividers are component-level only (same 0805 footprint).

**Estimated PCB impact**: Minor revision (resistor/component value changes) to moderate revision (if buck converter footprint changes).

## 7. Testing & Validation Requirements

1. **Bench verification** of internal power supply operation across 36V-62V input, including startup at low voltage (deeply discharged 48V battery)
2. **Charge profile validation** for each battery chemistry at 48V nominal: verify correct Warm-up, Bulk+Absorb, and Float voltage targets and transitions
3. **Auto-detection** test: confirm the regulator correctly identifies 12V, 24V, and 48V systems at power-up
4. **Transient testing**: verify survival and correct behavior during alternator load-dump events (voltage spikes to ~70V)
5. **Thermal testing** at 48V with maximum field current (20A) in the IP56 enclosure at elevated ambient
6. **Interface verification**: USB utility (EmX.exe), Wi-Fi web interface, and NMEA-2000 reporting with 48V-range values
7. **Backward compatibility**: confirm 12V and 24V operation is unaffected by hardware changes

## 8. Risk Summary

| Risk | Severity | Mitigation |
|---|---|---|
| MC34063A replacement requires PCB layout change | Medium | Select pin-compatible or small-footprint wide-input buck; evaluate pre-regulator option as fallback |
| P-CH MOSFET transient failure at 48V | High | Replace with 100V+ part; add clamping if needed |
| Reduced voltage measurement resolution | Low | 68mV/count at 48V is adequate for regulation band; firmware averaging compensates |
| Firmware scope creep from 48V profiles | Medium | Leverage existing profile structure; 48V is a 4x scaling of 12V parameters in most cases |
| EMI/EMC re-qualification at higher voltage | Medium | Plan for re-testing; existing shielding and filtering topology should transfer |
