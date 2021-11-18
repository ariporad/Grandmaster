#include <Wire.h>

//
// Constants
//

// We use the built-in LED as a status indicator: we turn it on if the program panics
#define STATUS_LED_PIN 13

#define MAGNET_PIN 2

#define CMD_MAGNET_ON 1
#define CMD_MAGNET_OFF 2

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

	Serial.println("Ready!");
	send_status();
}

void loop()
{
	// Check for Serial communication
	if (Serial.available())
	{
		int cmd = Serial.parseInt();

		// Commands (ie. magnet control) are negative so as to disambiguate with setting motor speeds
		switch (cmd)
		{
		case CMD_MAGNET_ON:
			magnet_enabled = true;
			Serial.println("Magnet Enabled");
			break;
		case CMD_MAGNET_OFF:
			magnet_enabled = false;
			Serial.println("Magnet Disabled");
			break;
		default:
			Serial.println("Unknown Command!");
			break;
		}
		digitalWrite(MAGNET_PIN, magnet_enabled ? HIGH : LOW);
		send_status();
	}
}

void send_status()
{
	Serial.print("[BOARD] Grandmaster OK: Magnet is ");
	if (magnet_enabled)
	{
		Serial.print("ENABLED (");
		Serial.print(CMD_MAGNET_OFF);
		Serial.print(" to disable)");
	}
	else
	{
		Serial.print("DISABLED (");
		Serial.print(CMD_MAGNET_ON);
		Serial.print(" to enable)");
	}
	Serial.println("!");
}
