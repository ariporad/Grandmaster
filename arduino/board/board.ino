#include <Wire.h>

//
// Constants
//

// We use the built-in LED as a status indicator: we turn it on if the program panics
#define STATUS_LED_PIN 13

#define MAGNET_PIN 2

// There are 4 buttons, which sensors/LEDs are 4 or 9 +0, 1, 2, 3
#define BUTTON_PIN_START 9
#define BUTTON_LED_START 4
#define NUM_BUTTONS 4

#define CMD_LIGHTS 0b00
#define CMD_BUTTON_LIGHT 0b01
#define CMD_MAGNET 0b10

#define LOOPS_PER_UPDATE 5000

//
// State Variables
//

bool magnet_enabled = false;
void setup()
{
	// Configure and turn off the panic LED, so we can see if we panic later on
	pinMode(STATUS_LED_PIN, OUTPUT);
	digitalWrite(STATUS_LED_PIN, LOW);

	// Setup the Serial interface
	Serial.begin(115200, SERIAL_8O2);
	Serial.setTimeout(50); // Make sure we don't spend too much time waiting for serial input

	// Configure pins
	for (int i = 0; i < NUM_BUTTONS; i++) {
		pinMode(BUTTON_PIN_START + i, INPUT);
		pinMode(BUTTON_LED_START + i, OUTPUT);
		digitalWrite(BUTTON_LED_START + i, LOW);
	}

	pinMode(MAGNET_PIN, OUTPUT);
    digitalWrite(MAGNET_PIN, LOW);

	setupLEDs();

	send_status();
}

int loops_since_update = LOOPS_PER_UPDATE;

void loop()
{
	// Check for Serial communication
	if (Serial.available()) read_command();

	check_buttons();

	updateLEDs();

	loops_since_update++;
	if (loops_since_update >= LOOPS_PER_UPDATE) {
		send_status();
		loops_since_update = 0;
	}
}

void read_command() {
	uint16_t raw_cmd = Serial.parseInt();
		
	if (raw_cmd == 0) return;

	uint16_t cmd_type = raw_cmd & 0b11;
	uint16_t data = raw_cmd >> 2;

	switch (cmd_type)
	{
	case CMD_MAGNET:
		cmd_magnet(data);
		break;
	case CMD_BUTTON_LIGHT:
		cmd_button_light(data);
		break;
	case CMD_LIGHTS:
		cmd_lights(data);
		break;
	default:
		send_invalid_command();	
		break;
	}
	send_status();
}

bool last_button_values[NUM_BUTTONS];

void check_buttons() {
	bool need_to_send_update = false;
	for (int i = 0; i < NUM_BUTTONS; i++) {
		bool cur_button_value = digitalRead(BUTTON_PIN_START + i);
		if (cur_button_value != last_button_values[i]) {
			last_button_values[i] = cur_button_value;
			need_to_send_update = true;
		}
	}
	if (need_to_send_update) send_status();
}

void send_status() {
	// 0b100M1234
	// Where M is magnet state, and 1234 is the state of each button
	uint8_t update = 0b10000000;
	for (int i = 0; i < NUM_BUTTONS; i++) {
		update |= (last_button_values[i] << i)
	}
	update |= digitalRead(MAGNET_PIN) << 4;
	Serial.write(update);
}

void send_invalid_command() {
}

/**
 * Magnet Command Format:
 * 0bA10
 * Where A is 1 to turn the magnet on, or 0 to turn it off.
 */
void cmd_magnet(uint16_t data) {
	switch (data) {
		case 0:
			digitalWrite(MAGNET_PIN, LOW);
			break;
		case 1:
			digitalWrite(MAGNET_PIN, HIGH);
			break;
		default:
			send_invalid_command();
			return;
	}
}

/**
 * Button Light Command Format:
 * 0bABB01
 * Where A is the action you want (1 for on, 0 for off), and BB is the offset of the LED (9 + BB) is
 * the pin to use.
 */
void cmd_button_light(uint16_t data) {
  uint8_t idx = data & 0b011;
  bool enabled = data & 0b100;
  digitalWrite(BUTTON_LED_START + idx, enabled ? HIGH : LOW);
}

#include <FastLED.h>

#define FANCY_LED_PIN 3
#define NUM_FANCY_LEDS 50
#define FANCY_LED_BRIGHTNESS 64
#define FANCY_LED_TYPE WS2811
#define FANCY_LED_COLOR_ORDER GRB
CRGB leds[NUM_FANCY_LEDS];

#define FANCY_LED_UPDATES_PER_SECOND 100
CRGBPalette16 currentPalette;
TBlendType currentBlending;

void setupLEDs()
{
	delay(3000); // power-up safety delay
	FastLED.addLeds<FANCY_LED_TYPE, FANCY_LED_PIN, FANCY_LED_COLOR_ORDER>(leds, NUM_FANCY_LEDS).setCorrection(TypicalLEDStrip);
	FastLED.setBrightness(FANCY_LED_BRIGHTNESS);

	currentPalette = RainbowColors_p;
	currentBlending = LINEARBLEND;
}

unsigned long next_led_update = 0;

void updateLEDs()
{
	// ChangePalettePeriodically();

	// FIXME: This doesn't account for overflow
	if (millis() < next_led_update) return;
	next_led_update = millis() + (1000 / FANCY_LED_UPDATES_PER_SECOND);

	static uint8_t startIndex = 0;
	startIndex = startIndex + 1; /* motion speed */

	FillLEDsFromPaletteColors(startIndex);

	FastLED.show();
}

void FillLEDsFromPaletteColors(uint8_t colorIndex)
{
	uint8_t brightness = 255;

	for (int i = 0; i < NUM_FANCY_LEDS; ++i)
	{
		leds[i] = ColorFromPalette(currentPalette, colorIndex, brightness, currentBlending);
		colorIndex += 3;
	}
}
void cmd_lights(uint16_t data) {
	// Not implemented yet, LEDs just always on
}
