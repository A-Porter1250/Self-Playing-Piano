#include <Arduino.h>
#include <ArduinoJson.h>

// Pin definitions for piano circuit interface
const int NUM_KEYS = 88;  // Standard piano
const int FIRST_NOTE = 21; // A0 is MIDI note 21
int notePins[NUM_KEYS];    // Array to hold output pin numbers

// For ESP32 pinout - adjust based on your specific requirements
void setupPinMapping() {
  // This is an example mapping - adjust to your hardware
  // Map MIDI notes to ESP32 GPIO pins
  for (int i = 0; i < NUM_KEYS; i++) {
    // Skip pins used for special functions
    // Use GPIO pins 2-33 (avoiding 6-11 which are used for flash)
    int pin = i + 12;  // Start at pin 12
    if (pin >= 34) {
      pin = pin - 28; // Skip to another range
    }
    notePins[i] = pin;
    pinMode(notePins[i], OUTPUT);
    digitalWrite(notePins[i], LOW);
  }
}

// Note event structure
struct NoteEvent {
  unsigned long timeMs;
  uint8_t type;      // 0 = note off, 1 = note on
  uint8_t note;
  uint8_t velocity;
};

// Queue for note events
const int MAX_EVENTS = 1000;
NoteEvent eventQueue[MAX_EVENTS];
int eventCount = 0;
int currentEvent = 0;
unsigned long startTime = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  
  // Initialize pin mapping
  setupPinMapping();
  
  Serial.println("ESP32 Piano Controller Ready");
  Serial.println("Send note events in JSON format");
}

// Process incoming JSON events
void processJsonEvent(const char* json) {
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, json);
  
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Check if this is an initialization message with event count
  if (doc.containsKey("count")) {
    // New song starting
    eventCount = 0;
    currentEvent = 0;
    int count = doc["count"];
    Serial.print("Receiving new song with ");
    Serial.print(count);
    Serial.println(" events");
    return;
  }
  
  // Otherwise, it's a note event
  if (eventCount < MAX_EVENTS) {
    NoteEvent event;
    event.timeMs = doc["time"];
    event.type = (doc["type"] == "note_on") ? 1 : 0;
    event.note = doc["note"];
    event.velocity = doc["velocity"];
    
    eventQueue[eventCount++] = event;
    
    // If this is the first event, prepare to start playing
    if (eventCount == 1) {
      Serial.println("First event received, ready to play");
    }
  } else {
    Serial.println("Event queue full!");
  }
}

// Serial buffer
const int BUFFER_SIZE = 256;
char serialBuffer[BUFFER_SIZE];
int bufferPos = 0;

void loop() {
  // 1. Read events from serial
  while (Serial.available()) {
    char c = Serial.read();
    
    // Process complete lines (JSON objects)
    if (c == '\n' || c == '\r') {
      if (bufferPos > 0) {
        serialBuffer[bufferPos] = '\0';  // Null terminate
        processJsonEvent(serialBuffer);
        bufferPos = 0; // Reset buffer
      }
    } else if (bufferPos < BUFFER_SIZE - 1) {
      serialBuffer[bufferPos++] = c;
    }
  }
  
  // 2. Check if we need to start playback
  if (eventCount > 0 && currentEvent == 0 && Serial.availableForWrite() > 0) {
    Serial.println("Starting playback!");
    startTime = millis();
    currentEvent = 0;
  }
  
  // 3. Process events based on timing
  while (currentEvent < eventCount) {
    NoteEvent& event = eventQueue[currentEvent];
    unsigned long currentTime = millis() - startTime;
    
    // If it's time to play this event
    if (currentTime >= event.timeMs) {
      // Map MIDI note to pin
      int noteIndex = event.note - FIRST_NOTE;
      
      if (noteIndex >= 0 && noteIndex < NUM_KEYS) {
        if (event.type == 1 && event.velocity > 0) {
          // Note on
          digitalWrite(notePins[noteIndex], HIGH);
          Serial.print("♪ ON: ");
        } else {
          // Note off
          digitalWrite(notePins[noteIndex], LOW);
          Serial.print("♪ OFF: ");
        }
        
        Serial.print(event.note);
        Serial.print(" at ");
        Serial.print(currentTime);
        Serial.print("ms (scheduled: ");
        Serial.print(event.timeMs);
        Serial.println("ms)");
      }
      
      currentEvent++;
    } else {
      // Not time yet for the next event
      break;
    }
  }
  
  // 4. Check if playback is complete
  if (currentEvent >= eventCount && eventCount > 0) {
    Serial.println("Playback complete!");
    
    // Reset for next song
    eventCount = 0;
    currentEvent = 0;
  }
}