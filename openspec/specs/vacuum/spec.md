# Vacuum

## Purpose

Translate a vacuum status datapoint and map Home Assistant commands to configured control DPs. Source: [`vacuum.py`](../../../custom_components/localtuya/vacuum.py).

## Requirements

### Requirement: Report activity and telemetry

The vacuum SHALL compare the string form of the primary status DP to comma-separated idle and docked values (defaults `standby,sleep` and `charging,chargecompleted`), then the configured returning and paused values (defaults `docking` and `paused`); other values mean cleaning. A configured fault value other than numeric zero SHALL override the mapped activity with error.

#### Scenario: Fault overrides docking
- **WHEN** a vacuum reports `charging` with a fault DP of `1`
- **THEN** it reports error and includes the fault value

### Requirement: Expose optional vacuum telemetry

Configured DPs SHALL provide battery and cleaning telemetry (`clean_time`, `clean_area`, `clean_record`, and `fault`). Cleaning modes default to `smart,wall_follow,spiral,single`; fan speeds default to `low,normal,high`. The reported mode and fan speed use their configured DPs.

#### Scenario: Publish a cleaning cycle's metadata
- **WHEN** clean time and area DPs are configured and report values
- **THEN** the entity exposes them in `clean_time` and `clean_area`

### Requirement: Send configured cleaning commands

Start and pause SHALL write `true` and `false` to the required `powergo_dp`. Return-to-base and stop SHALL write their configured tokens (defaults `chargego` and `standby`) to the mode DP. Locate SHALL write an empty string to its configured DP, fan speed SHALL write the requested token, and `set_mode` SHALL forward `params["mode"]` to the mode DP. Spot cleaning is not implemented.

#### Scenario: Return the vacuum to its dock
- **WHEN** return-to-base is invoked on a vacuum with a mode DP and the default return token
- **THEN** the mode DP receives `chargego`

#### Scenario: Advertise optional vacuum controls
- **WHEN** a vacuum has mappings for fan speed, battery and locate
- **THEN** those features are added to the base start, pause, stop, status and state feature set
- **AND** return-home is enabled based on the return token, not a check for the mode DP
