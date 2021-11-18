#include <Wire.h>
#include <SpeedyStepper.h>

//
// Constants
//

// We use the built-in LED as a status indicator: we turn it on if the program panics
#define STATUS_LED_PIN 13

// Motors
// NOTE: X is forms, Y is ranks
#define X_STEP_PIN 2
#define Y_STEP_PIN 3
#define X_DIR_PIN 5
#define Y_DIR_PIN 6
#define STEPPERS_ENABLE_PIN 8
#define LIMIT_SWITCH_X_PIN 9
#define LIMIT_SWITCH_Y_PIN 10

// TODO: figure out these values
#define STEPS_PER_SQUARE 750

#define SPEED_STEPS_PER_SEC 500
#define ACCEL_STEPS_PER_SEC_PER_SEC 500

//
// State Variables
//

int cur_pos_x = 0; // 0-7, where 0 is A and 7 is H
int cur_pos_y = 0; // 0-7, where 0 is Rank 1 and 7 is Rank 7

//
// Motors
//
SpeedyStepper xMotor;
SpeedyStepper yMotor;

void setup()
{
	// Configure and turn off the panic LED, so we can see if we panic later on
	pinMode(STATUS_LED_PIN, OUTPUT);
	digitalWrite(STATUS_LED_PIN, LOW);

	// Setup the Serial interface
	Serial.begin(115200);
	Serial.setTimeout(50); // Make sure we don't spend too much time waiting for serial input

	// Setup the Motors
	pinMode(STEPPERS_ENABLE_PIN, OUTPUT);
	xMotor.connectToPins(X_STEP_PIN, X_DIR_PIN);
	yMotor.connectToPins(Y_STEP_PIN, Y_DIR_PIN);
	digitalWrite(STEPPERS_ENABLE_PIN, LOW);

	Serial.println("Ready!");
	send_status();
}

void loop()
{
	// Check for Serial communication
	if (Serial.available())
	{
		int cmd = Serial.parseInt();

		// Commands are intepreted as square numbers to move to, with the same notation as
		// Python Chess: A1 = 0 -> H8 = 63
		// TODO: Need to change this notation to allow moving past the edge of the board
		int new_pos = max(0, min(63, cmd));
		int new_pos_x = new_pos % 8;
		int new_pos_y = new_pos / 8;
		int diff_pos_x = new_pos_x - cur_pos_x;
		int diff_pos_y = new_pos_y - cur_pos_y;

		int steps_x = diff_pos_x * STEPS_PER_SQUARE;
		int steps_y = diff_pos_y * STEPS_PER_SQUARE;

		Serial.print("Moving: ");
		Serial.print(cur_pos_x);
		Serial.print(",");
		Serial.print(cur_pos_y);
		Serial.print(" -> ");
		Serial.print(new_pos_x);
		Serial.print(",");
		Serial.print(new_pos_y);
		Serial.print(" (");
		Serial.print(diff_pos_x);
		Serial.print(",");
		Serial.print(diff_pos_y);
		Serial.print(" squares, ");
		Serial.print(steps_x);
		Serial.print(",");
		Serial.print(steps_y);
		Serial.print(" steps");
		Serial.println(")");

		moveXYWithCoordination(steps_x, steps_y, SPEED_STEPS_PER_SEC, ACCEL_STEPS_PER_SEC_PER_SEC);

		cur_pos_x = new_pos_x;
		cur_pos_y = new_pos_y;

		Serial.println("Done!");
		send_status();
	}
}

void send_status()
{
	Serial.print("[GANTRY] Grandmaster OK:");
	Serial.print(" at Form #");
	Serial.print(cur_pos_x);
	Serial.print(" Rank #");
	Serial.print(cur_pos_y);
	Serial.print(" (0-63 to move)");
	Serial.println("!");
}

//
// move both X & Y motors together in a coordinated way, such that they each
// start and stop at the same time, even if one motor moves a greater distance
//
// From Stan's example
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
