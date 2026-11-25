# Fan

## Purpose

Provide power and optional speed, oscillation, and direction controls. Source: [`fan.py`](../../../custom_components/localtuya/fan.py).

## Requirements

### Requirement: Power and optional control features

The fan SHALL always advertise on and off and use boolean writes to the primary DP. Configuring the relevant DP SHALL enable speed, oscillation, or direction separately. Oscillation SHALL write the requested boolean and direction SHALL write the configured forward/reverse token (`forward`/`reverse` by default). Reports SHALL map direction tokens back to Home Assistant direction values.

#### Scenario: Change direction
- **WHEN** reverse is requested with a configured direction DP and reverse token `rev`
- **THEN** that DP receives `rev`

### Requirement: Percentage conversion for two speed representations

Speed SHALL use either a comma-separated ordered list with more than one item or an inclusive integer range (default `1–9`). The ordered list defaults to `disabled`. Numeric speed writes SHALL round up the Home Assistant ranged value, and both modes SHALL cast the result to the configured `str` (default) or `int`. Inbound values SHALL be converted back to a percentage with Home Assistant's corresponding helper. The reported speed count uses the integer range even in list mode.

#### Scenario: Set speed while the fan is off
- **WHEN** a nonzero percentage is requested while the device reports off
- **THEN** an on command is sent before the speed write

#### Scenario: Set zero percent
- **WHEN** the percentage is zero
- **THEN** the fan is turned off without writing a speed value
