# Cover

## Purpose

Control cover motion with no position feedback, a native position DP, or estimated travel time. Source: [`cover.py`](../../../custom_components/localtuya/cover.py).

## Requirements

### Requirement: Movement command mapping

The cover SHALL write the configured open/close/stop tokens to its primary DP. Supported sets are `on_off_stop` (default), `open_close_stop`, `fz_zz_stop`, and `1_2_3` (string tokens). An uppercase reported motion state SHALL cause subsequent commands to be uppercased. Open, close and stop are always exposed; set position is exposed for `position` and `timed` modes but not `none`.

#### Scenario: Access a cover in none mode
- **WHEN** positioning is `none`
- **THEN** position is not reported, `is_closed` is false, and the motion commands remain available

### Requirement: Native position feedback and target writes

An optional current-position DP SHALL supply the reported position when used. In `position` mode, a configured target DP SHALL receive the integer target if within `0–100`. With `position_inverted` enabled (default false), both conversions SHALL use `100 - position`.

#### Scenario: Inverted native cover
- **WHEN** the reported native value is `30` and the user requests `70%` open
- **THEN** the reported Home Assistant position is `70%` and a target value of `30` is sent

### Requirement: Timed positioning

Timed positioning SHALL use a configured travel span (default `25` seconds, range `1–300`). It SHALL estimate movement on transitions using elapsed time divided by the span, sign according to direction, and clamp to `0–100`. It SHALL recover `current_position` from Home Assistant state when available. A target request schedules stop after the fraction of the span needed; open and close also schedule a full-travel stop after span plus three seconds.

#### Scenario: Move from 20 to 60 percent
- **WHEN** a timed cover with a 25-second span is asked to move from `20` to `60`
- **THEN** it sends open and schedules the target stop after ten seconds in addition to the full-travel timeout
