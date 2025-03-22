from esp32_interface import ESP32MidiInterface

def play_midi_file(file_path, serial_port):
    """Play a MIDI file on the ESP32-connected piano"""
    esp32 = ESP32MidiInterface(serial_port)
    esp32.send_note_events(file_path)
    print(f"Playback of {file_path} initiated on ESP32")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python example.py <midi_file> <serial_port>")
        print("Example: python example.py song.mid COM3")
        print("Example: python example.py song.mid /dev/ttyUSB0")
        sys.exit(1)
        
    midi_file = sys.argv[1]
    serial_port = sys.argv[2]
    play_midi_file(midi_file, serial_port)