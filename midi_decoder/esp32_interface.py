import serial
import time
import json
from .midi_decoder import MidiFile

class ESP32MidiInterface:
    def __init__(self, port, baud_rate=115200):
        self.serial = serial.Serial(port, baud_rate)
        time.sleep(2)  # Allow ESP32 to reset and stabilize
        
    def send_note_events(self, midi_file_path):
        """Process MIDI file and send simplified events to ESP32"""
        midi = MidiFile(midi_file_path)
        note_events = self._extract_note_events(midi)
        
        # Send the number of events first
        event_count = len(note_events)
        self.serial.write(f"{{\"count\":{event_count}}}\n".encode())
        
        # Send each event with a small delay to prevent buffer overflow
        for event in note_events:
            json_event = json.dumps(event)
            self.serial.write(f"{json_event}\n".encode())
            time.sleep(0.01)  # Small delay between events
            
        print(f"Sent {event_count} note events to ESP32")
    
    def _extract_note_events(self, midi):
        """Extract note events from MIDI file with absolute timing"""
        current_time_ms = 0
        ticks_per_ms = self._calculate_ticks_per_ms(midi)
        note_events = []
        
        for track in midi.tracks:
            track_time_ms = 0
            
            for event in track.events:
                # Convert delta time to milliseconds
                track_time_ms += (event.delta_time / ticks_per_ms)
                
                # Only process note on/off events
                if (event.type == "midi" and 
                    event.parameters.get("event") in ["note_on", "note_off"]):
                    
                    note_event = {
                        "time": round(track_time_ms),  # Time in ms
                        "type": event.parameters.get("event"),
                        "note": event.parameters.get("note"),
                        "velocity": event.parameters.get("velocity"),
                        "channel": event.channel
                    }
                    note_events.append(note_event)
        
        # Sort events by time
        note_events.sort(key=lambda x: x["time"])
        return note_events
    
    def _calculate_ticks_per_ms(self, midi):
        """Calculate conversion from ticks to milliseconds"""
        if midi.time_division["type"] != "tpqn":
            raise ValueError("Only TPQN time division supported")
        
        ticks_per_quarter = midi.time_division["ticks"]
        
        # Find tempo (default 120 BPM if not specified)
        tempo_event = None
        for track in midi.tracks:
            for event in track.events:
                if (event.type == "meta" and 
                    event.parameters.get("meta_type") == 0x51):
                    tempo_event = event
                    break
            if tempo_event:
                break
        
        # Calculate microseconds per tick
        if tempo_event:
            microseconds_per_quarter = tempo_event.parameters.get("tempo")
        else:
            # Default tempo (120 BPM)
            microseconds_per_quarter = 500000
        
        microseconds_per_tick = microseconds_per_quarter / ticks_per_quarter
        ticks_per_ms = 1000 / microseconds_per_tick
        
        return ticks_per_ms