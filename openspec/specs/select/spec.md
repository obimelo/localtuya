# Select

## Purpose

Expose a device enumeration with optional user-facing labels. Source: [`select.py`](../../../custom_components/localtuya/select.py).

## Requirements

### Requirement: Map choices to raw values by position

The select SHALL split raw values and optional friendly labels on `;`, use raw values for all labels if none are supplied, and fill missing friendly labels with raw values at the same position. The form SHALL offer restore-on-reconnect, passive mode, and an optional initialization value. Its built-in initialization value is the first raw option.

#### Scenario: Partially label an enumeration
- **WHEN** raw values are `eco;turbo` and the friendly value string is `Economy`
- **THEN** the choices are `Economy` and `turbo`
- **AND** selecting `Economy` writes `eco`

#### Scenario: Device reports an unmapped value
- **WHEN** the received DP is not null but does not match a configured raw option
- **THEN** the entity reports the received value rather than inventing a label
