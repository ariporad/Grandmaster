/**
 * This file is a test bed for getting the LED patterns right.
 * 
 * It is no longer used. See board.ino for its successor.
 */
#include <FastLED.h>

#define LED_PIN 3
#define NUM_LEDS 50
#define LED_BRIGHTNESS 64
#define LED_TYPE WS2811
#define LED_COLOR_ORDER RGB
CRGB leds[NUM_LEDS];

#define LEDS_UPDATES_PER_SECOND 100

CRGBPalette16 led_palette;
TBlendType led_blending = LINEARBLEND;
uint8_t led_speed = 1;
uint8_t led_max_brightness = 255;
uint8_t led_blink_time = 100;
uint8_t led_blink_brightness = 150;
uint8_t led_time_to_next_blink = led_blink_time;

const uint32_t LED_COMPUTER_COLOR = 0x6666FF;
const uint32_t LED_HUMAN_COLOR = CRGB::HotPink;

extern const TProgmemPalette16 led_palette_both_players PROGMEM;

void setup()
{
	delay(3000); // power-up safety delay
	FastLED.addLeds<LED_TYPE, LED_PIN, LED_COLOR_ORDER>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
	FastLED.setBrightness(LED_BRIGHTNESS);

	// led_set_pallete_fail();
	// led_set_pallete_bootup();
	// led_set_pallete_getting_ready();
	// led_set_pallete_ready();
	// led_set_pallete_human_turn();
	// led_set_pallete_expo_human_think();
}

uint8_t led_position = 0;

void loop()
{
	// ChangePalettePeriodically();
	led_position = led_position + led_speed; /* motion speed */

	uint8_t brightness = led_max_brightness;

	if (led_time_to_next_blink == 0) {
		led_time_to_next_blink = led_blink_time;
	}

	if (led_time_to_next_blink-- >= (led_blink_time / 2)) {
		brightness -= led_blink_brightness;
	}

	led_apply_palette(led_position, brightness);

	FastLED.show();
	FastLED.delay(1000 / LEDS_UPDATES_PER_SECOND);
}

void led_apply_palette(uint8_t colorIndex, uint8_t brightness)
{
	for (int i = 0; i < NUM_LEDS; ++i)
	{
		leds[i] = ColorFromPalette(led_palette, colorIndex, brightness, led_blending);
		colorIndex += 3;
	}
}

void led_set_animation(int speed, int new_blink_time, int blink_intensity)
{
	led_speed = speed;
	led_max_brightness = 255;
	led_blink_time = new_blink_time;
	led_blink_brightness = blink_intensity;
	led_time_to_next_blink = new_blink_time;
}

void led_set_animation_blink()
{
	led_set_animation(0, 100, 100);
}

void led_set_animation_spin()
{
	led_set_animation(1, 0, 0);
}

void led_set_animation_blink_and_spin()
{
	led_set_animation(1, 100, 100);
}

void led_set_pallete(uint8_t id) {
	switch (id)
	{
	case 0: return led_set_pallete_fail();
	case 1: return led_set_pallete_bootup();
	case 2: return led_set_pallete_getting_ready();
	case 3: return led_set_pallete_ready();
	case 4: return led_set_pallete_human_turn();
	case 5: return led_set_pallete_expo_human_think();
	case 6: return led_set_pallete_computer_move();
	case 7: return led_set_pallete_computer_think();
	default:
		break;
	}
}

void led_set_pallete_fail() // ID: 0
{
	led_set_animation_blink();
	fill_solid(led_palette, 16, CRGB::Red);
}

void led_set_pallete_bootup() // ID: 1
{
	led_set_animation_blink_and_spin();
	led_palette = RainbowColors_p;
}

void led_set_pallete_getting_ready() // ID: 2
{
	led_set_animation_spin();
	led_palette = RainbowStripeColors_p;
}

void led_set_pallete_ready() // ID: 3
{
	led_set_animation_spin();
	led_palette = led_palette_both_players;
}

void led_set_pallete_human_turn() // ID: 4
{
	led_set_animation_spin();
	fill_solid(led_palette, 16, LED_HUMAN_COLOR);
	led_palette[0] = CRGB::Black;
	led_palette[1] = CRGB::Black;
	led_palette[4] = CRGB::Black;
	led_palette[5] = CRGB::Black;
	led_palette[8] = CRGB::Black;
	led_palette[9] = CRGB::Black;
	led_palette[12] = CRGB::Black;
	led_palette[13] = CRGB::Black;
}

void led_set_pallete_expo_human_think() // ID: 5
{
	led_set_animation_blink();
	fill_solid(led_palette, 16, LED_HUMAN_COLOR);
}

void led_set_pallete_computer_move() // ID: 6
{
	led_set_animation_spin();
	fill_solid(led_palette, 16, LED_COMPUTER_COLOR);
	led_palette[0] = CRGB::Black;
	led_palette[1] = CRGB::Black;
	led_palette[4] = CRGB::Black;
	led_palette[5] = CRGB::Black;
	led_palette[8] = CRGB::Black;
	led_palette[9] = CRGB::Black;
	led_palette[12] = CRGB::Black;
	led_palette[13] = CRGB::Black;
}

void led_set_pallete_computer_think() // ID: 7
{
	led_set_animation_blink();
	fill_solid(led_palette, 16, LED_COMPUTER_COLOR);
}

const TProgmemPalette16 led_palette_both_players PROGMEM =
	{
		LED_COMPUTER_COLOR,
		LED_COMPUTER_COLOR,
		CRGB::Black,
		CRGB::Black,
		LED_HUMAN_COLOR,
		LED_HUMAN_COLOR,
		CRGB::Black,
		CRGB::Black,

		LED_COMPUTER_COLOR,
		LED_COMPUTER_COLOR,
		CRGB::Black,
		CRGB::Black,
		LED_HUMAN_COLOR,
		LED_HUMAN_COLOR,
		CRGB::Black,
		CRGB::Black
	};