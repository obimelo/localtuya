# Diagnostics and logging

## Purpose

Expose troubleshooting information and document the limits of current credential handling. Sources: [`diagnostics.py`](../../../custom_components/localtuya/diagnostics.py), [`pytuya/__init__.py`](../../../custom_components/localtuya/pytuya/__init__.py), and [`config_flow.py`](../../../custom_components/localtuya/config_flow.py).

## Requirements

### Requirement: Entry-level diagnostics

The entry diagnostic SHALL return the entry data and `cloud_devices`, with client ID, client secret, user ID and local keys abbreviated to the first three and last three characters separated by `...`. This is partial masking; it is not safe to treat the export as anonymized.

#### Scenario: Export entry diagnostics
- **WHEN** a diagnostics export is requested for an entry with configured devices
- **THEN** the nested configured device records are deep-copied before masking
- **AND** other configuration data, such as names and addresses, is still present

### Requirement: Device-level diagnostics

The device diagnostic SHALL return `device_config` and, for a matching cached cloud record, `device_cloud_info`. This checkout does not apply independent masking on the device diagnostic path.

#### Scenario: Export diagnostics for a LAN-only device
- **WHEN** no matching cloud record exists
- **THEN** the result contains `device_config` without `device_cloud_info`
- **AND** the stored local key can be present in the result

### Requirement: Contextual protocol logging

The logging adapter SHALL prefix messages with a shortened device ID. Debug logging through the protocol and dispatcher SHALL require the per-device debug flag as well as Home Assistant's logging configuration.

#### Scenario: Debug a connection
- **WHEN** the user enables device debugging and sets the relevant logger level to debug
- **THEN** protocol debug output may include payloads or session data and must be reviewed before sharing
