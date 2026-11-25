# Sensor

## Purpose

Expose read-only telemetry from an arbitrary datapoint. Source: [`sensor.py`](../../../custom_components/localtuya/sensor.py).

## Requirements

### Requirement: Publish raw or scaled sensor values

The sensor SHALL accept an optional unit, Home Assistant sensor device class, and scale factor between `-1000000` and `1000000`. Its initial state is unknown. If scaling is set and the value is numeric, it SHALL multiply by the factor and round to two decimals. It SHALL not write a restoration value.

#### Scenario: Convert raw voltage
- **WHEN** DP `1` reports `2314` with scaling `0.1`
- **THEN** the sensor reports `231.4` in its configured unit

#### Scenario: Textual sensor value
- **WHEN** a DP reports a non-numeric string
- **THEN** the sensor reports the string unchanged even when scaling is configured
