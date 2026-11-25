# Light

## Purpose

Expose Tuya light power, dimming, white temperature, color, and effects. Source: [`light.py`](../../../custom_components/localtuya/light.py).

## Requirements

### Requirement: Capabilities from configured DPs

The light SHALL use its primary DP for power. Brightness, color temperature, color mode, color, and scene DPs are optional. It SHALL advertise HS and/or color temperature if those DPs exist, brightness when only dimming is mapped, or on/off otherwise. Turn-on SHALL group applicable changes in a single DP map; turn-off SHALL write `false` to the primary DP.

#### Scenario: Dimmer without color controls
- **WHEN** a light has a brightness DP but neither color nor temperature DP
- **THEN** its sole supported color mode is brightness

### Requirement: Scale brightness

Brightness SHALL be mapped linearly between Home Assistant `0–255` and the configured device limits (`29–1000` by default; each accepts `0–10000`), with rounding and output clamping.

#### Scenario: Set white brightness
- **WHEN** a white-mode dimmer is set to brightness `255`
- **THEN** the configured device upper brightness value is written

### Requirement: Scale white temperature

White temperature SHALL use a mired range derived from configured Kelvin limits (`2700–6500` by default; each accepts `1500–8000`) and a device upper limit equal to maximum brightness. The temperature command SHALL clamp to the mired range, honor the reverse-temperature toggle, and write white mode, brightness and temperature when using mapped controls.

#### Scenario: Reverse the temperature axis
- **WHEN** the reverse toggle is enabled
- **THEN** the temperature conversion flips the raw warm/cool axis in both the write and the report

### Requirement: Decode and write Tuya color representations

The light SHALL choose the RGB-prefixed color format when its cached color string is longer than 12 characters; otherwise use the three four-hex-digit HSV fields. The RGB-prefixed format uses RGB bytes, a four-digit hue, saturation scaled to `0–255`, and the raw brightness. The short format uses saturation times ten. A zero-saturation HS request with a brightness DP SHALL write white mode instead.

#### Scenario: Decode a short color report
- **WHEN** the color DP reports `007803e801f4` in color mode
- **THEN** it yields hue `120`, saturation `100%`, and raw brightness `500`

### Requirement: Scene and music commands

The light SHALL select the RGBW 255 scene table for scene DP IDs below `20`, RGB 1000 when the ID is at least `20` and brightness is not mapped, and RGBW 1000 otherwise. A scene value beginning with `scene` SHALL be written directly to the mode DP; other known scenes SHALL set mode `scene` and write the scene data separately.

#### Scenario: Select a stored scenario
- **WHEN** `Scenario 1` is requested using the RGBW 255 table
- **THEN** `scene_1` is sent to the mode DP

#### Scenario: Recognize custom scene data
- **WHEN** a `scene` mode report contains unknown scene data
- **THEN** the current effect is `Custom`

#### Scenario: Use dedicated music mode
- **WHEN** EFFECT is supported and a `Music` effect request does not match an entry in the selected scene table
- **THEN** `music` is written to the mode DP
