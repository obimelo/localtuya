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

The light SHALL expose Kelvin color temperature and limits to Home Assistant (`2700–6500` K by default; each limit accepts `1500–8000` K). It SHALL clamp to those limits and map reciprocal Kelvin onto the device DP range from zero to maximum brightness. It SHALL honor the reverse-temperature toggle and never send an unmapped DP for an optional mode or brightness control.

#### Scenario: Call Home Assistant's light turn-on action
- **WHEN** a user requests `color_temp_kelvin: 6500` with the default non-reversed limits
- **THEN** a color-temperature DP value of `1000` is sent

#### Scenario: Reverse the temperature axis
- **WHEN** the reverse toggle is enabled
- **THEN** the temperature conversion flips the raw warm/cool axis in both the write and the report

### Requirement: Decode and write Tuya color representations

The light SHALL choose the RGB-prefixed color format when its cached color string is longer than 12 characters; otherwise use the three four-hex-digit HSV fields. The RGB-prefixed format uses RGB bytes, a four-digit hue, saturation scaled to `0–255`, and the raw brightness. The short format uses saturation times ten. A zero-saturation HS request with a brightness DP SHALL write white mode instead.

#### Scenario: Decode a short color report
- **WHEN** the color DP reports `007803e801f4` in color mode
- **THEN** it yields hue `120`, saturation `100%`, and raw brightness `500`

### Requirement: Scene and music commands

The light SHALL publish the configured scene/effect names as a list. It SHALL select the RGBW 255 scene table for scene DP IDs below `20`, RGB 1000 when the ID is at least `20` and brightness is not mapped, and RGBW 1000 otherwise. A scene value beginning with `scene` SHALL be written directly to the mode DP; other known scenes SHALL set mode `scene` and write the scene data separately.

#### Scenario: Select a stored scenario
- **WHEN** `Scenario 1` is requested using the RGBW 255 table
- **THEN** `scene_1` is sent to the mode DP

#### Scenario: Recognize custom scene data
- **WHEN** a `scene` mode report contains unknown scene data
- **THEN** the current effect is `Custom`

#### Scenario: Use dedicated music mode
- **WHEN** music mode is enabled and a `Music` effect request does not match an entry in the selected scene table
- **THEN** `music` is written to the mode DP
