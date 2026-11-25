# Integration lifecycle

## Purpose

Load and manage LocalTuya as a Home Assistant config-entry integration. Source: [`__init__.py`](../../../custom_components/localtuya/__init__.py), [`manifest.json`](../../../custom_components/localtuya/manifest.json), and [`services.yaml`](../../../custom_components/localtuya/services.yaml).

## Requirements

### Requirement: Config-entry startup and reload

LocalTuya SHALL expose the `localtuya` domain as a `local_push` integration with a config flow. On entry setup it SHALL initialize the optional cloud client, instantiate one runtime wrapper per configured device, forward setup for the union of configured platforms, and schedule device connections after forwarding. Entry updates SHALL trigger entry reload.

#### Scenario: Several devices share a platform
- **WHEN** an entry has two devices with switches and one with a sensor
- **THEN** setup creates the wrappers and forwards `switch` and `sensor` once each before scheduling device connections

#### Scenario: Entry data is updated
- **WHEN** an options change or discovery update notifies the entry listener
- **THEN** Home Assistant reloads that entry

### Requirement: Legacy entry migration

Version 1 entries SHALL be consolidated under the first entry. The first becomes version 2 with title `localtuya`, region `eu`, cloud disabled, blank client ID, client secret and user ID, and the old device data under `devices[device_id]`. Subsequent legacy entries SHALL contribute their device data and be removed. New YAML imports are not supported even though a schema remains; they SHALL log the unsupported-configuration message rather than create entries.

#### Scenario: Upgrade multiple version 1 entries
- **WHEN** the first legacy entry is migrated and the others are merged
- **THEN** the surviving entry preserves each device's settings and entities and does not enable cloud access by default

### Requirement: Unload and device removal

Entry unload SHALL request unload of the configured platforms, unsubscribe the update listener, and close connected device wrappers. The runtime device map is cleared if all platform unloads succeed. Device removal SHALL remove matching entity registry entries, close the configured device if present, and remove its config from the entry so it is not recreated on reload.

#### Scenario: Remove one configured device
- **WHEN** Home Assistant invokes device removal
- **THEN** matching registry entities are removed and the device configuration is dropped while the other configurations are retained

#### Scenario: Device configuration is already gone
- **WHEN** removal is called for an identifier not in the entry's device map
- **THEN** it finalizes after matching registry cleanup rather than attempting to close the missing configuration

### Requirement: Home Assistant services

The integration SHALL provide admin-only `localtuya.reload`, which requests a reload of all LocalTuya entries, and `localtuya.set_dp`, which accepts a string `device_id`, integer `dp`, and required `value` of any schema type. `set_dp` SHALL delegate to the connected runtime wrapper without requiring an entity for the DP. A service return does not confirm a device changed state; the wrapper logs write failures.

#### Scenario: Raw write to an unbound DP
- **WHEN** a known connected device is addressed with a valid integer DP and value
- **THEN** the write is delegated even if that DP is not the primary DP of an entity

#### Scenario: Service targets an unavailable device
- **WHEN** `set_dp` names an unknown device or a known disconnected device
- **THEN** it raises `HomeAssistantError` with `unknown device id` or `not connected to device`, respectively
