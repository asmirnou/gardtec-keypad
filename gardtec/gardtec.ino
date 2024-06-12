#include <assert.h>
#include <limits.h>
#include <string.h>
#include <CircularBuffer.hpp>
#include <SoftwareSerial.h>
#include <Wire.h>

const uint8_t keypadNum = 1;  // Can be 1, 2, 3 or 4

SoftwareSerial keypad(2, 3);  // RX, TX

typedef struct
{
  uint8_t value;
  uint8_t repeat;
} key_t;

CircularBuffer<key_t*, 50> keys;

uint8_t lastMessage[32];
uint8_t frame[37];
int frameLength = -1;
int writeCount = -1;
int copyCount = -1;
unsigned long syncTime;

void setup() {
  assert(keypadNum >= 1 && keypadNum <= 4);

  Wire.begin(0x56);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);

  keypad.begin(1560);
  Serial.begin(1560, SERIAL_7N1);
  while (!Serial) {
    ;  // Wait for serial port to connect (needed for native USB port only)
  }
}

void requestEvent() {
  Wire.write(&lastMessage[0], 32);
  copyCount++;
  if (copyCount > 10) {
    memset(&lastMessage[0], 0x00, 32);
  }
}

void receiveEvent(int howMany) {
  while (Wire.available()) {
    uint8_t k = Wire.read();
    if (k < 0x0C) {
      keys.push(new key_t{ k, 5 });
    }
  }
}

void loop() {
  sync();
  if (wait()) {
    transmit();
  }
}

void sync() {
  if (!Serial.available()) {
    return;
  }

  uint8_t c = reverse7(Serial.read());

  if (frameLength < 0) {
    if (c == 0x7F || (c >= 0x01 && c <= 0x07)) {
      frameLength = 0;
    } else {
      return;
    }
  }

  frame[frameLength++] = c;

  if (writeCount != -1 && ((frameLength == 1 + keypadNum) || (frameLength == 15 + keypadNum) || (frameLength == 29 + keypadNum))) {
    writeCount = 2;
    syncTime = micros();
  } else if (writeCount != -1 && ((frameLength == 8 + keypadNum) || (frameLength == 22 + keypadNum))) {
    writeCount = 1;
    syncTime = micros();
  } else if (frameLength == 37) {
    copy();
    frameLength = -1;
    writeCount = 0;
  } else {
    writeCount = 0;
  }
}

bool wait() {
  switch (writeCount) {
    case 2:
      return (micros() - syncTime > 700);
    case 1:
      return (micros() - syncTime > 2500);
    default:
      return false;
  }
}

void transmit() {
  uint8_t d;
  if (!pop(&d) || !matchesKeypad()) {
    if (isHeartbeat()) {
      d = 0xFF;
    } else {
      writeCount--;
      return;
    }
  }

  keypad.write(reverse(d));
  writeCount--;
}

void copy() {
  if (matchesKeypad()) {
    memcpy(&lastMessage[00], &frame[02], 0x0C);
    memcpy(&lastMessage[12], &frame[15], 0x0C);
    memcpy(&lastMessage[24], &frame[28], 0x08);
  } else {
    strncpy(&lastMessage[00], "System in use...Please WAIT     ", 32);
  }
  copyCount = -1;
}

bool pop(uint8_t* d) {
  bool selected = false;
  if (!keys.isEmpty()) {
    key_t* key = keys.first();

    while (!selected && key->repeat > 0) {
      key->repeat--;
      *d = encode(key->value);
      selected = true;
    }

    if (!selected) {
      key = keys.shift();
      delete key;
    }
  }
  return selected;
}

uint8_t reverse(uint8_t v) {
  uint8_t r = v;                     // r will be reversed bits of v; first get LSB of v
  int s = sizeof(v) * CHAR_BIT - 1;  // extra shift needed at end

  for (v >>= 1; v; v >>= 1) {
    r <<= 1;
    r |= v & 1;
    s--;
  }
  r <<= s;
  return r;
}

uint8_t reverse7(uint8_t v) {
  return reverse(v) >> 1;
}

uint8_t encode(uint8_t c) {
  uint8_t r = c << 4;
  r |= c % 2 ? 0x0F : 0x07;
  if (isHeartbeat()) {
    r >>= 3;
    r |= 0xC0;
  }
  return r;
}

bool isHeartbeat() {
  return writeCount == 2;
}

bool matchesKeypad() {
  return (frame[0] == 0x7F || frame[0] == keypadNum);
}
