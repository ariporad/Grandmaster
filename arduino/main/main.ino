#include <Wire.h>
#include <Adafruit_MotorShield.h>

//
// Constants
//

// We use the built-in LED as a status indicator: we turn it on if the program panics
#define STATUS_LED_PIN 13

// On the Adafruit Motor Shield
#define X_MOTOR_PORT 1

// TODO: figure out these values
#define STEPS_PER_REV 200
#define REVS_PER_MINUTE 1000
#define STEPS_PER_SQUARE 1500
#define STEP_MODE INTERLEAVE

#define MAGNET_PIN 2

//
// State Variables
//

int cur_pos_x = 1;
bool magnet_enabled = false;

//
// Motors
//
Adafruit_MotorShield motorShield = Adafruit_MotorShield();
Adafruit_StepperMotor *xMotor = motorShield.getStepper(STEPS_PER_REV, X_MOTOR_PORT);

void setup()
{
	// Configure and turn off the panic LED, so we can see if we panic later on
	pinMode(STATUS_LED_PIN, OUTPUT);
	digitalWrite(STATUS_LED_PIN, LOW);

	// Setup the Serial interface
	Serial.begin(115200);
	Serial.setTimeout(50); // Make sure we don't spend too much time waiting for serial input

	// Connect to the Motor Shield
	motorShield.begin();

	// Configure other pins
	pinMode(MAGNET_PIN, OUTPUT);

	// Set the speed that motors will run at
	xMotor->setSpeed(REVS_PER_MINUTE);

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
		if (cmd < 0)
		{
			switch (cmd)
			{
			case -1:
				magnet_enabled = true;
				Serial.println("Magnet Enabled");
				break;
			case -2:
				magnet_enabled = false;
				Serial.println("Magnet Disabled");
				break;
			default:
				Serial.println("Unknown Command!");
				break;
			}
      send_status();
		}
		else if (cmd > 0)
		{
			int new_pos_x = max(1, min(8, cmd));
			int diff_pos_x = new_pos_x - cur_pos_x;
			int direction_x = FORWARD;

			if (diff_pos_x < 0)
			{
				direction_x = BACKWARD;
				diff_pos_x *= -1;
			}

			int steps_x = diff_pos_x * STEPS_PER_SQUARE;

			Serial.print("Moving: ");
			Serial.print(cur_pos_x);
			Serial.print(" -> ");
			Serial.print(new_pos_x);
			Serial.print(" (");
			Serial.print(diff_pos_x);
			Serial.print(" squares, ");
			Serial.print(steps_x);
			Serial.print(" steps ");
			Serial.print(direction_x == FORWARD ? "FORWARD" : "BACKWARD");
			Serial.println(")");
			xMotor->step(steps_x, direction_x, STEP_MODE);
			cur_pos_x = new_pos_x;
      Serial.println("Done!");
      send_status();
		}
	}

	digitalWrite(MAGNET_PIN, magnet_enabled ? HIGH : LOW);
}

void send_status() {
  Serial.print("Grandmaster OK: Magnet is ");
  Serial.print(magnet_enabled ? "ENABLED (-2 to disable)" : "DISABLED (-1 to enable)");
  Serial.print(" at Square #");
  Serial.print(cur_pos_x);
  Serial.print(" (1-8 to move)");
  Serial.println("!"); 
}
