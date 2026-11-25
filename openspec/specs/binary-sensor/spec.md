# Binary sensor

## Purpose

Expose a read-only, two-state interpretation of a Tuya datapoint. Source: [`binary_sensor.py`](../../../custom_components/localtuya/binary_sensor.py).

## Requirements

### Requirement: Translate configured state patterns

The binary sensor SHALL accept on/off string patterns (defaults `True` and `False`) and an optional Home Assistant binary-sensor device class. It SHALL initialize off and compare the stringified DP to the patterns case-insensitively, checking the on pattern first. It SHALL not write to the device on reconnect.

#### Scenario: Match state or preserve the previous state
- **WHEN** the received value matches an on or off pattern regardless of case
- **THEN** the corresponding state is reported
- **AND** an unmatched value logs a warning and preserves the previous boolean state
