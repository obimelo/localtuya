# Device runtime and entity state

## Purpose

Manage one configured device's LAN connection, push updates, refresh, and state restoration. Sources: [`common.py`](../../../custom_components/localtuya/common.py) and [`__init__.py`](../../../custom_components/localtuya/__init__.py).

## Requirements

### Requirement: Start and recover the device connection

A device wrapper SHALL use the configured host, device ID, key, protocol version, and debug flag. It SHALL guard against a second concurrent connection attempt and seed the protocol's DP request set with the primary and configured platform DP IDs. After getting initial status it SHALL start heartbeat and publish the state. A 60-second integration timer SHALL attempt to reconnect disconnected devices.

#### Scenario: Initial status fails with reset IDs configured
- **WHEN** the initial query raises and reset IDs are present
- **THEN** the wrapper requests a reset and retries status before starting the heartbeat
- **AND** this retry requires a nonempty result

#### Scenario: Initial status fails without reset IDs
- **WHEN** the initial query raises and no reset IDs are configured
- **THEN** the interface is closed rather than treating the device as initialized

### Requirement: Update availability and state on push

The wrapper SHALL merge incoming status into its DP cache and dispatch that cache on the per-device `localtuya_<device_id>` signal. Entities SHALL use the string form of the primary DP ID as their availability criterion, not the truthiness of its value. Home Assistant entity polling SHALL be disabled. When entity data changes, the entity SHALL schedule a Home Assistant state update.

#### Scenario: A switch reports false
- **WHEN** a device status contains the switch DP with value `false`
- **THEN** the switch is available and off, not unavailable

#### Scenario: Partial status or a late-added entity
- **WHEN** a push reports only some DPs, or an entity signals it was added after the wrapper subscribed
- **THEN** the wrapper publishes the merged cache rather than discarding unrelated DPs

#### Scenario: The LAN session disconnects
- **WHEN** the protocol calls the wrapper's disconnect callback
- **THEN** it dispatches an unavailable update, clears the active interface, and removes the optional refresh timer

### Requirement: Optional refresh and local writes

A positive configured scan interval in seconds SHALL schedule `update_dps` on the active protocol interface. It is a request for device refresh rather than a replacement for push state. The wrapper SHALL forward single or grouped writes only when an interface is present and log transport failures.

#### Scenario: No refresh configured
- **WHEN** the scan interval is absent, zero, or negative
- **THEN** the wrapper does not schedule timed refreshes

### Requirement: Entity identity

An entity SHALL use `local_<device_id>_<dp_id>` as its unique ID and register under `(localtuya, local_<device_id>)`. Device metadata SHALL include the configured name, Tuya manufacturer, model with device ID (fallback model `Tuya generic`), and the configured protocol as software version.

#### Scenario: Two DPs identify separate entities on the same device
- **WHEN** a device has entities on DP 1 and DP 2
- **THEN** both share a device identifier but have distinct entity unique IDs

### Requirement: Reconnect initialization

For platforms using common restoration, an entity SHALL be eligible if restore-on-reconnect is enabled or if it is passive and its primary DP is missing. Restoration SHALL use current raw state first, then saved `raw_state`, then the configured or platform default only for passive entities.

#### Scenario: Passive entity has never reported its DP
- **WHEN** a connection succeeds and no current or stored state exists for a passive switch, number, or select
- **THEN** the configured default is written if present, otherwise `false`, the number minimum, or the first raw select option respectively

#### Scenario: Active entity has no saved state
- **WHEN** restoration is enabled for a non-passive entity but neither current nor stored state is available
- **THEN** no default write is issued

#### Scenario: Read-only sensor reconnects
- **WHEN** a sensor or binary sensor reconnects
- **THEN** it does not write a restoration value
