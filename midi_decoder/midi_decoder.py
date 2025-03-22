import os
class MidiFile:
    def __init__(self, filename):
        self.filename = filename
        self.format = None
        self.num_tracks = None
        self.time_division = None
        self.tracks = []
        self.parse()
    
    def parse(self):
        """Parse the entire MIDI file."""
        with open(self.filename, 'rb') as file:
            # Parse header chunk
            self._parse_header(file)
            
            # Parse each track chunk
            for i in range(self.num_tracks):
                track = MidiTrack()
                track.parse(file)
                self.tracks.append(track)
    
    def _parse_header(self, file):
        """Parse the MIDI file header chunk."""
        # Check for MThd marker
        chunk_type = file.read(4)
        if chunk_type != b'MThd':
            raise ValueError("Not a valid MIDI file - missing MThd marker")
        
        # Header length (should be 6)
        length = int.from_bytes(file.read(4), byteorder='big')
        if length != 6:
            raise ValueError(f"Unexpected header length: {length}")
        
        # Format type (0, 1, or 2)
        self.format = int.from_bytes(file.read(2), byteorder='big')
        
        # Number of tracks
        self.num_tracks = int.from_bytes(file.read(2), byteorder='big')
        
        # Time division
        time_division_bytes = file.read(2)
        time_division_value = int.from_bytes(time_division_bytes, byteorder='big')
        
        # Check if SMPTE format or ticks per quarter note
        if time_division_value & 0x8000:
            # SMPTE format
            frames_per_second = -(time_division_value >> 8)
            ticks_per_frame = time_division_value & 0xFF
            self.time_division = {"type": "smpte", "fps": frames_per_second, "tpf": ticks_per_frame}
        else:
            # Ticks per quarter note
            self.time_division = {"type": "tpqn", "ticks": time_division_value}


class MidiTrack:
    def __init__(self):
        self.events = []
        self.length = None
    
    def parse(self, file):
        """Parse a single MIDI track chunk."""
        # Check for MTrk marker
        chunk_type = file.read(4)
        if chunk_type != b'MTrk':
            raise ValueError("Invalid track - missing MTrk marker")
        
        # Track length
        self.length = int.from_bytes(file.read(4), byteorder='big')
        
        # Track end position for validation
        end_position = file.tell() + self.length
        
        # Running status for MIDI events
        running_status = None
        
        # Parse all events in the track
        while file.tell() < end_position:
            event = MidiEvent()
            running_status = event.parse(file, running_status)
            self.events.append(event)
        
        # Validate we've read exactly the right number of bytes
        if file.tell() != end_position:
            raise ValueError("Track length mismatch")


class MidiEvent:
    def __init__(self):
        self.delta_time = None
        self.type = None
        self.channel = None
        self.parameters = {}
    
    def parse(self, file, running_status):
        """Parse a single MIDI event."""
        # Parse variable-length delta time
        self.delta_time = self._parse_variable_length(file)
        
        # Read the status byte
        status_byte = file.read(1)[0]
        
        # Check if this is a running status (status byte omitted)
        if status_byte < 0x80:
            if running_status is None:
                raise ValueError("Running status used without prior status byte")
            # Use the previous status byte and rewind to reread the data byte
            file.seek(file.tell() - 1)
            status_byte = running_status
        else:
            # Update running status for next event
            running_status = status_byte
        
        # Handle different event types
        if status_byte == 0xFF:
            # Meta event
            self.type = "meta"
            self._parse_meta_event(file)
        elif status_byte == 0xF0 or status_byte == 0xF7:
            # SysEx event
            self.type = "sysex"
            self._parse_sysex_event(file, status_byte)
        else:
            # MIDI event
            self._parse_midi_event(status_byte, file)
        
        return running_status
    
    def _parse_variable_length(self, file):
        """Parse a variable-length value."""
        value = 0
        while True:
            byte = file.read(1)[0]
            value = (value << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                break
        return value
    
    def _parse_meta_event(self, file):
        """Parse a meta event."""
        meta_type = file.read(1)[0]
        length = self._parse_variable_length(file)
        data = file.read(length)
        
        self.parameters["meta_type"] = meta_type
        self.parameters["data"] = data
        
        # Interpret specific meta events
        if meta_type == 0x01:
            # Text event
            self.parameters["text"] = data.decode('ascii', errors='replace')
        elif meta_type == 0x03:
            # Track name
            self.parameters["name"] = data.decode('ascii', errors='replace')
        elif meta_type == 0x51:
            # Tempo
            if length != 3:
                raise ValueError(f"Unexpected tempo event length: {length}")
            tempo = (data[0] << 16) | (data[1] << 8) | data[2]
            self.parameters["tempo"] = tempo
            self.parameters["bpm"] = 60000000 / tempo
        # Additional meta event types can be added here
    
    def _parse_sysex_event(self, file, status_byte):
        """Parse a system exclusive event."""
        length = self._parse_variable_length(file)
        self.parameters["data"] = file.read(length)
    
    def _parse_midi_event(self, status_byte, file):
        """Parse a standard MIDI event."""
        self.type = "midi"
        self.channel = status_byte & 0x0F
        message_type = status_byte >> 4
        
        if message_type == 0x8:
            # Note Off
            self.parameters["event"] = "note_off"
            self.parameters["note"] = file.read(1)[0]
            self.parameters["velocity"] = file.read(1)[0]
        elif message_type == 0x9:
            # Note On
            self.parameters["event"] = "note_on"
            self.parameters["note"] = file.read(1)[0]
            self.parameters["velocity"] = file.read(1)[0]
            # Note On with velocity 0 is equivalent to Note Off
            if self.parameters["velocity"] == 0:
                self.parameters["event"] = "note_off"
        elif message_type == 0xA:
            # Polyphonic Key Pressure (Aftertouch)
            self.parameters["event"] = "poly_aftertouch"
            self.parameters["note"] = file.read(1)[0]
            self.parameters["pressure"] = file.read(1)[0]
        elif message_type == 0xB:
            # Control Change
            self.parameters["event"] = "control_change"
            self.parameters["controller"] = file.read(1)[0]
            self.parameters["value"] = file.read(1)[0]
        elif message_type == 0xC:
            # Program Change
            self.parameters["event"] = "program_change"
            self.parameters["program"] = file.read(1)[0]
        elif message_type == 0xD:
            # Channel Pressure (Aftertouch)
            self.parameters["event"] = "channel_aftertouch"
            self.parameters["pressure"] = file.read(1)[0]
        elif message_type == 0xE:
            # Pitch Bend
            self.parameters["event"] = "pitch_bend"
            lsb = file.read(1)[0]
            msb = file.read(1)[0]
            self.parameters["value"] = (msb << 7) | lsb
        else:
            raise ValueError(f"Unknown MIDI message type: {message_type}")