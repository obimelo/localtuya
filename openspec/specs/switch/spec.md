# Switch

## Purpose

Control a boolean datapoint and expose optional electrical measurements. Source: [`switch.py`](../../../custom_components/localtuya/switch.py).

## Requirements

### Requirement: Boolean writes and reported switch state

The switch SHALL expose the reported primary DP as its state and write `true` or `false` on Home Assistant on or off commands. It SHALL offer required restore-on-reconnect and passive flags and an optional initialization value (string in the form). Its built-in passive default is `false`.

#### Scenario: Turn a device off
- **WHEN** an off command is sent
- **THEN** the integration writes `false` to the primary DP
- **AND** the display state is driven by the device report rather than by assigning the commanded state

### Requirement: Optional electrical attributes

The switch SHALL publish configured `current` unchanged and divide configured `current_consumption` and `voltage` by ten. Unconfigured measurements SHALL be omitted. It SHALL include the current raw state or the last raw state in `raw_state` when available.

#### Scenario: Supply all three optional measurements
- **WHEN** configured DPs report current `110`, consumption `253`, and voltage `2302`
- **THEN** the attributes are `110`, `25.3`, and `230.2`, respectively
