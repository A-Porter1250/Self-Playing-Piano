# Self-Playing Piano

A project to create a self-playing piano system using MIDI files and an ESP32 microcontroller.

## Overview
This project aims to develop a system that can automatically play piano pieces without human intervention. The system decodes MIDI files on a computer, sends simplified note events to an ESP32 microcontroller, which then controls the piano's physical keys through appropriate circuitry.

## Features
- MIDI file parsing and interpretation
- Efficient communication protocol between computer and ESP32
- Accurate timing of note events
- Support for note velocity (dynamics)
- Real-time playback status feedback

## Components

### Software
- `midi_decoder/` - Python package for MIDI file processing
- `esp32_firmware/` - Arduino code for the ESP32 microcontroller
- `hardware_guide/` - Documentation for the physical interface to the piano

## Getting Started

### Prerequisites
- Python 3.6+
- Arduino IDE with ESP32 support
- ESP32 development board
- Piano with accessible key mechanism
- Electronic components (see hardware guide)

### Installation

1. **Python Dependencies**
   ```bash
   pip install pyserial
   ```

2. **ESP32 Firmware**
   - Open `esp32_firmware/midi_piano_controller.ino` in Arduino IDE
   - Configure for your ESP32 board
   - Upload the firmware

3. **Hardware Setup**
   - Follow the instructions in `hardware_guide/circuit_design.md`
   - Adapt pin assignments in the ESP32 code as needed

### Usage

```bash
# Using the example script
python midi_decoder/example.py path/to/midi_file.mid COM3
```

Or in your own Python code:

```python
from midi_decoder import ESP32MidiInterface

esp32 = ESP32MidiInterface("/dev/ttyUSB0")  # Adjust port as needed
esp32.send_note_events("path/to/midi_file.mid")
```

## License
[MIT License](LICENSE)