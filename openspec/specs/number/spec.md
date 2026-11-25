# Number

## Purpose

Read and set a numeric datapoint with Home Assistant number metadata. Source: [`number.py`](../../../custom_components/localtuya/number.py).

## Requirements

### Requirement: Native number values and configuration

The number SHALL publish the primary DP directly, initially unknown, and write submitted values without additional conversion, clamping, or step rounding. Minimum and maximum settings SHALL accept floats from `-1000000` to `1000000`, and step from `0` to `1000000`. Defaults are `0`, `100000`, and `1.0`. The form SHALL offer restore-on-reconnect and passive flags and a default-value string, which is parsed as a float when provided.

#### Scenario: Set a number from Home Assistant
- **WHEN** Home Assistant submits `2.5`
- **THEN** the integration writes numeric `2.5` to the primary DP

#### Scenario: Initialize a passive number without a saved value
- **WHEN** the common restoration rules require initialization and no explicit default is configured
- **THEN** the number uses its configured minimum
