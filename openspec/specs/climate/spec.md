# Climate

## Purpose

Map heating, thermostat, and air conditioning datapoints onto Home Assistant climate controls. Source: [`climate.py`](../../../custom_components/localtuya/climate.py).

## Requirements

### Requirement: Report and set configured temperature values

The climate entity SHALL report device-native Celsius by default or Fahrenheit when configured, using Core 2026.11 native temperature properties where available. It SHALL multiply current and target readings by their respective precision and divide an outgoing target by target precision, rounding to an integer. Minimum and maximum SHALL come from configured bound DPs as-is or the configured constants.

#### Scenario: Control a half-degree thermostat
- **WHEN** target precision is `0.5` and the user sets `21.5`
- **THEN** the target DP is set to `43`
- **AND** a report of `43` decodes as `21.5`

#### Scenario: Select or load temperature precision
- **WHEN** an entity is configured through the form
- **THEN** it offers `1`, `0.5`, and `0.1` for current precision, target precision, and target step (default `1` each)
- **AND** if those fields are absent in storage, runtime instead falls back to current precision `0.1`, matching target precision, and step `0.5`

### Requirement: Power and HVAC mode mapping

The primary DP SHALL receive boolean on/off commands. With a mode DP, the entity SHALL expose the modes in the [configured mapping](#hvac-mode-mapping-reference) plus off. Inbound off state overrides the mode DP; an unmatched mode while on falls back to auto.

#### Scenario: Off thermostat changes to heat
- **WHEN** the primary power DP and mode DP differ and the thermostat is off
- **THEN** power is turned on, the implementation waits `0.1` seconds, and then sends the mapped heat token

#### Scenario: Set HVAC to off
- **WHEN** off is selected
- **THEN** the entity sends `false` to the primary power DP rather than a mapped mode command

### Requirement: HVAC action and heating inference

The entity SHALL decode heating/idle from the selected action mapping: boolean `true/false`, `open/close`, `heating/no_heating`, `Heat/Warming`, or `heating/warming`. In heat mode, the optional heuristic SHALL compare the current temperature to the target less one current precision step.

#### Scenario: Infer heating action in heat mode
- **WHEN** heuristic action is enabled and the current temperature is more than one current precision step below target
- **THEN** the action reports heating
- **AND** at exactly one step below it preserves the action, while above that threshold it reports idle

### Requirement: Eco and other presets

The entity SHALL map away/home/none to `Holiday/Program/Manual` or `holiday/smart/hold`. An exact eco DP match (default `ECO`) SHALL take precedence; selecting eco writes that value to its own DP. An unmatched report SHALL fall back to none.

#### Scenario: Eco overrides a preset
- **WHEN** the preset DP maps to home but the eco DP matches its eco token
- **THEN** the entity reports eco

### Requirement: Fan and swing controls

Fan SHALL map auto/low/medium/high/top to `auto/low/middle/high/strong`; swing SHALL map on/off to booleans. Unrecognized reports SHALL fall back to auto and off respectively. Unmapped commands are logged rather than sent.

#### Scenario: Report HVAC capabilities
- **WHEN** the entity has target and maximum temperature DPs, an eco DP, a fan DP with mapping, and a swing DP
- **THEN** it advertises target temperature, target temperature range, preset, fan, and swing in addition to on/off

## HVAC mode mapping reference

| Set | Home Assistant modes to device values |
| --- | --- |
| `manual/auto`, `Manual/Auto`, `MANUAL/AUTO` | heat and auto to the corresponding case-sensitive values |
| `Manual/Program` | heat → `Manual`, auto → `Program` |
| `m/p` | heat → `m`, auto → `p` |
| `True/False` | heat → boolean `true` |
| `Auto/Cold/Dry/Wind/Hot` | auto → `auto`, cool → `cold`, dry → `wet`, fan-only → `wind`, heat → `hot` |
| `Cold/Dehumidify/Hot` | cool → `cold`, dry → `dehumidify`, heat → `hot` |
| `1/0` | heat → string `1`, auto → string `0` |
