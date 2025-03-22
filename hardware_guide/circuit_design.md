# Piano Circuit Interface Design

## Overview

This document provides guidance on how to connect the ESP32 to your piano circuit hardware. The design focuses on translating digital signals from the ESP32 to appropriate electrical signals that can drive the mechanical components of a piano.

## Components Needed

1. **ESP32 Development Board** - Main controller
2. **Level Shifters** - If your piano circuit operates at a different voltage than 3.3V
3. **Optocouplers** - For electrical isolation between ESP32 and piano
4. **Transistors** - For current amplification (e.g., TIP120 or MOSFET)
5. **Diodes** - For back-EMF protection
6. **Resistors** - For current limiting
7. **Capacitors** - For noise filtering
8. **Power Supply** - Appropriate for your piano mechanism

## Connection Diagram

```
ESP32 GPIO Pin → Resistor (330Ω) → Optocoupler Input → Optocoupler Output → Transistor Base → Piano Circuit
```

## Design Considerations

### Voltage Levels

The ESP32 operates at 3.3V, but your piano circuit might require different voltage levels (5V, 12V, 24V). Use level shifters or design your transistor circuit appropriately.

### Current Requirements

ESP32 GPIO pins can typically source/sink ~12mA safely. If your piano mechanism requires more current:

1. Use transistors as switches
2. Ensure adequate heat dissipation
3. Use appropriate power supplies

### Isolation

Optocouplers provide electrical isolation, which protects:

- The ESP32 from voltage spikes
- Against ground loops
- From potential damage due to inductance in solenoids/motors

### EMI/RFI Protection

If your piano uses solenoids or motors:

1. Add flyback diodes across inductive loads
2. Use capacitors for noise suppression
3. Keep signal wires away from power wires

## Wiring Guidelines

1. Use shielded cables for long wire runs
2. Keep power and signal grounds separate but connected at one point
3. Add ferrite beads on long cable runs
4. Label all connections clearly

## Testing

Before connecting to the actual piano circuit:

1. Test with LEDs to visualize the note signals
2. Measure voltages and currents to ensure they're within expected ranges
3. Start with a small subset of notes before scaling to the full keyboard

## Piano-Specific Interfaces

### Solenoid-Based Systems

For systems using solenoids to press keys:

- Each solenoid typically needs 12-24V
- Requires transistors capable of handling the solenoid current (typically 100-500mA)
- Flyback diodes are essential

### Motor-Based Systems

For systems using motors:

- May require H-bridge drivers for bidirectional control
- Consider using dedicated motor driver ICs
- Ensure proper current handling capability

## Scaling Considerations

For a full 88-key piano:

1. Consider using shift registers or I/O expanders to increase available pins
2. Multiplexing techniques can reduce the pin count requirements
3. Power supply must be sized appropriately for maximum simultaneous notes