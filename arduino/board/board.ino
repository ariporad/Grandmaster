#include <Wire.h>

//
// Constants
//

// We use the built-in LED as a status indicator: we turn it on if the program panics
#define STATUS_LED_PIN 13

#define MAGNET_PIN 2

#define START_BUTTON_PIN 9
#define FUN_BUTTON_PIN 10
#define PLAYER_BUTTON_PIN 11
#define COMPUTER_BUTTON_PIN 12

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
	Serial.begin(115200);
	Serial.setTimeout(50); // Make sure we don't spend too much time waiting for serial input

	// Configure pins
	pinMode(MAGNET_PIN, OUTPUT);
  	pinMode(START_BUTTON_PIN, INPUT);
  	pinMode(FUN_BUTTON_PIN, INPUT);
  	pinMode(PLAYER_BUTTON_PIN, INPUT);
  	pinMode(COMPUTER_BUTTON_PIN, INPUT);
}

int loops_since_update = LOOPS_PER_UPDATE;

void loop()
{
	// Check for Serial communication
	if (Serial.available())
	{
		uint16_t raw_cmd = Serial.parseInt();

    send_status();
    
    if (raw_cmd != 0) {
  		uint16_t cmd_type = raw_cmd & 0b11;
  		uint16_t data = raw_cmd >> 2;
  
      Serial.print("COMMAND: raw: ");
      Serial.print(String(raw_cmd));
      Serial.print(", type: ");
      Serial.print(String(cmd_type));
      Serial.print(", data: ");
      Serial.println(String(data));
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
    }
	}

	check_buttons();

	loops_since_update++;
	if (loops_since_update >= LOOPS_PER_UPDATE) {
		send_status();
		loops_since_update = 0;
	}
}

bool last_start_button = false;
bool last_fun_button = false;
bool last_computer_button = false;
bool last_player_button = false;
void check_buttons() {
	// TODO: Keep button numbers in sync with Button in ArduinoController
	bool start_button = digitalRead(START_BUTTON_PIN);
	if (last_start_button != start_button) {
		Serial.print("TYPE:BUTTON_PRESS;BUTTON:2;PRESSED:");
		Serial.println(String(int(start_button)));
	}
	last_start_button = start_button;

	bool fun_button = digitalRead(FUN_BUTTON_PIN);
	if (last_fun_button != fun_button) {
		Serial.print("TYPE:BUTTON_PRESS;BUTTON:3;PRESSED:");
		Serial.println(String(int(fun_button)));
	}
	last_fun_button = fun_button;

	bool player_button = digitalRead(PLAYER_BUTTON_PIN);
	if (last_player_button != player_button) {
		Serial.print("TYPE:BUTTON_PRESS;BUTTON:1;PRESSED:");
		Serial.println(String(int(player_button)));
	}
	last_player_button = player_button;

	bool computer_button = digitalRead(COMPUTER_BUTTON_PIN);
	if (last_computer_button != computer_button) {
		Serial.print("TYPE:BUTTON_PRESS;BUTTON:0;PRESSED:");
		Serial.println(String(int(computer_button)));
	}
	last_computer_button = computer_button;

}

void send_status() {
	Serial.println("TYPE:ANNOUNCEMENT;NAME:BOARD");
	Serial.print("TYPE:STATUS;START:");
	Serial.print(String(digitalRead(START_BUTTON_PIN)));
	Serial.print(";FUN:");
	Serial.print(String(digitalRead(FUN_BUTTON_PIN)));
	Serial.print(";COMPUTER:");
	Serial.print(String(digitalRead(COMPUTER_BUTTON_PIN)));
	Serial.print(";PLAYER:");
	Serial.print(String(digitalRead(PLAYER_BUTTON_PIN)));
	Serial.println("");
}

void send_invalid_command() {
	Serial.println("TYPE:ERROR;CODE:INVALID_COMMAND");
}

/**
 * Magnet Command Format:
 * 0bA10
 * Where A is 1 to turn the magnet on, or 0 to turn it off.
 */
void cmd_magnet(uint16_t data) {
//  Serial.print("MAGNET DATA: ");
//  Serial.println(String(data));
	switch (data) {
		case 0:
			digitalWrite(MAGNET_PIN, LOW);
//      Serial.println("MAGNET OFF");
			break;
		case 1:
			digitalWrite(MAGNET_PIN, HIGH);
//      Serial.println("MAGNET ON");
			break;
		default:
//      Serial.println("MAGNET ERR");
			send_invalid_command();
			return;
	}
	Serial.print("TYPE:MAGNET_STATUS;ENABLED:");
	Serial.println(String(int(digitalRead(MAGNET_PIN))));
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
  digitalWrite(4 + idx, enabled ? HIGH : LOW);
}

void cmd_lights(uint16_t data) {

}
