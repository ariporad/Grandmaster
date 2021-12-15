#include <Wire.h>
#include "SpeedyStepper.h"

//
// Constants
//

// Motors
// NOTE: X is forms, Y is ranks
#define X_STEP_PIN 3
#define Y_STEP_PIN 2
#define X_DIR_PIN 6
#define Y_DIR_PIN 5
#define STEPPERS_ENABLE_PIN 8
#define LIMIT_SWITCH_X_MIN_PIN 11
#define LIMIT_SWITCH_X_MAX_PIN 9
#define LIMIT_SWITCH_Y_MAX_PIN 10

#define HOME_OFFSET_X 300
#define HOME_OFFSET_Y 130

int steps_per_square = -255;

#define HOMING_SPEED_STEPS_PER_SEC 100
#define SPEED_STEPS_PER_SEC 200
#define ACCEL_STEPS_PER_SEC_PER_SEC 100

#define UPDATE_INTERVAL_MS 100

//
// State Variables
//
int current_pos_x = 7; // 0-9, where 0 is A, 7 is H, and 8-9 are the graveyard
int current_pos_y = 7; // 0-7, where 0 is Rank 1 and 7 is Rank 7

//
// Motors
//
SpeedyStepper xMotor;
SpeedyStepper yMotor;

void setup()
{
	// Setup the Serial interface
	Serial.begin(115200);

	Serial.setTimeout(50); // Make sure we don't spend too much time waiting for serial input

	// Setup the Motors
	pinMode(STEPPERS_ENABLE_PIN, OUTPUT);
	xMotor.connectToPins(X_STEP_PIN, X_DIR_PIN);
	yMotor.connectToPins(Y_STEP_PIN, Y_DIR_PIN);
	digitalWrite(STEPPERS_ENABLE_PIN, LOW);

	pinMode(LIMIT_SWITCH_X_MIN_PIN, INPUT_PULLUP);
	pinMode(LIMIT_SWITCH_X_MAX_PIN, INPUT_PULLUP);
	pinMode(LIMIT_SWITCH_Y_MAX_PIN, INPUT_PULLUP);

	home();
	send_position();
}

void loop()
{
	// Check for Serial communication
	if (Serial.available())
	{
		uint8_t cmd = Serial.parseInt();

		/**
		 * The only valid command for the gantry is to move to a location, which is an 8-bit message in
		 * the form:
		 *   0bAAAABBBB where:
		 * AAAA is the index of the form to move to (one-indexed), and
		 * BBBB is the index of the rank to move to (one-indexed)
		 * 
		 * Both ranks and files are one-indexed to ensure that 0b00000000 is not a valid command, since
		 * it's often produced unintentionally and so is ignored.
		 */
		if (cmd != 0)
		{
			uint8_t new_pos_x = min(7, (cmd >> 4) - 1);
			uint8_t new_pos_y = min(7, (cmd & 0b1111) - 1);
			int diff_pos_x = new_pos_x - current_pos_x;
			int diff_pos_y = new_pos_y - current_pos_y;

			int steps_x = diff_pos_x * steps_per_square;
			int steps_y = diff_pos_y * steps_per_square;

			moveXYWithCoordination(steps_x, steps_y, SPEED_STEPS_PER_SEC, ACCEL_STEPS_PER_SEC_PER_SEC);

			send_position();

			current_pos_x = new_pos_x;
			current_pos_y = new_pos_y;
		}
	}

	// Occasionally, send an update even if nothing's changed. Don't do this every
	// loop to avoid overwhelming the serial connection.
	static unsigned long last_update_time = 0;
	if (millis() - last_update_time >= UPDATE_INTERVAL_MS)
	{
		send_position();
		last_update_time = millis();
	}
}

void send_position()
{
	/**
	 * Updates are in the same format as commands:
	 *   0bAAAABBBB where:
	 * AAAA is the index of the form to move to (one-indexed), and
	 * BBBB is the index of the rank to move to (one-indexed)
	 * 
	 * Both ranks and files are one-indexed to ensure that 0b00000000 is not a valid message, since
	 * it's often produced unintentionally and so is ignored.
	 */
	Serial.write(((current_pos_x + 1) << 4) | (current_pos_y + 1));
}

void home() {
	xMotor.moveToHomeInSteps(1, HOMING_SPEED_STEPS_PER_SEC, steps_per_square * 11, LIMIT_SWITCH_X_MAX_PIN);
	yMotor.moveToHomeInSteps(1, HOMING_SPEED_STEPS_PER_SEC, steps_per_square * 11, LIMIT_SWITCH_Y_MAX_PIN);
	moveXYWithCoordination(HOME_OFFSET_X, HOME_OFFSET_Y, HOMING_SPEED_STEPS_PER_SEC, ACCEL_STEPS_PER_SEC_PER_SEC);
}

/*
 * move both X & Y motors together in a coordinated way, such that they each
 * start and stop at the same time, even if one motor moves a greater distance
 *
 * Copied and modified from Stan's example (thank you!)
 */
void moveXYWithCoordination(long stepsX, long stepsY, float speedInStepsPerSecond, float accelerationInStepsPerSecondPerSecond)
{

	float speedInStepsPerSecond_X;
	float accelerationInStepsPerSecondPerSecond_X;
	float speedInStepsPerSecond_Y;
	float accelerationInStepsPerSecondPerSecond_Y;
	long absStepsX;
	long absStepsY;

	//
	// setup initial speed and acceleration values
	//
	speedInStepsPerSecond_X = speedInStepsPerSecond;
	accelerationInStepsPerSecondPerSecond_X = accelerationInStepsPerSecondPerSecond;

	speedInStepsPerSecond_Y = speedInStepsPerSecond;
	accelerationInStepsPerSecondPerSecond_Y = accelerationInStepsPerSecondPerSecond;

	//
	// determine how many steps each motor is moving
	//
	if (stepsX >= 0)
		absStepsX = stepsX;
	else
		absStepsX = -stepsX;

	if (stepsY >= 0)
		absStepsY = stepsY;
	else
		absStepsY = -stepsY;

	//
	// determine which motor is traveling the farthest, then slow down the
	// speed rates for the motor moving the shortest distance
	//
	if ((absStepsX > absStepsY) && (stepsX != 0))
	{
		//
		// slow down the motor traveling less far
		//
		float scaler = (float)absStepsY / (float)absStepsX;
		speedInStepsPerSecond_Y = speedInStepsPerSecond_Y * scaler;
		accelerationInStepsPerSecondPerSecond_Y = accelerationInStepsPerSecondPerSecond_Y * scaler;
	}

	if ((absStepsY > absStepsX) && (stepsY != 0))
	{
		//
		// slow down the motor traveling less far
		//
		float scaler = (float)absStepsX / (float)absStepsY;
		speedInStepsPerSecond_X = speedInStepsPerSecond_X * scaler;
		accelerationInStepsPerSecondPerSecond_X = accelerationInStepsPerSecondPerSecond_X * scaler;
	}

	//
	// setup the motion for the X motor
	//
	xMotor.setSpeedInStepsPerSecond(speedInStepsPerSecond_X);
	xMotor.setAccelerationInStepsPerSecondPerSecond(accelerationInStepsPerSecondPerSecond_X);
	xMotor.setupRelativeMoveInSteps(stepsX);

	//
	// setup the motion for the Y motor
	//
	yMotor.setSpeedInStepsPerSecond(speedInStepsPerSecond_Y);
	yMotor.setAccelerationInStepsPerSecondPerSecond(accelerationInStepsPerSecondPerSecond_Y);
	yMotor.setupRelativeMoveInSteps(stepsY);

	//
	// now execute the moves, looping until both motors have finished
	//
	while ((!xMotor.motionComplete()) || (!yMotor.motionComplete()))
	{
		xMotor.processMovement();
		yMotor.processMovement();
	}
}
