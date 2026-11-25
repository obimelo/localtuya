# Configuration

## Purpose

Configure accounts, devices, and datapoint (DP) bindings through Home Assistant. Source: [`config_flow.py`](../../../custom_components/localtuya/config_flow.py), [`const.py`](../../../custom_components/localtuya/const.py), and [`translations/en.json`](../../../custom_components/localtuya/translations/en.json).

## Requirements

### Requirement: Account setup and reconfiguration

The config flow SHALL accept region `eu`, `us`, `cn`, or `in` (default `eu`), client ID, client secret, user ID, account label (default `localtuya`), and a `no_cloud` toggle (default false). Initial creation SHALL use the account label for the title, pass the user ID to Home Assistant as the flow unique ID, and start with an empty device map. The options menu SHALL offer Add device, Edit device, and Reconfigure Cloud API account.

#### Scenario: Skip cloud setup
- **WHEN** `no_cloud` is selected at creation or reconfiguration
- **THEN** client ID, client secret and user ID are stored as empty strings without testing cloud credentials
- **AND** a reconfiguration preserves the device map

#### Scenario: Submit cloud credentials
- **WHEN** cloud is enabled and credentials are submitted
- **THEN** the flow tests token acquisition and device listing in order
- **AND** an unsuccessful result keeps the form open with `authentication_failed` or `device_list_failed` and the returned message

#### Scenario: Reconfigure cloud successfully
- **WHEN** both cloud calls succeed while reconfiguring
- **THEN** account fields are saved and missing model fields are populated from matching cloud product names, without replacing models already present

### Requirement: Add-device selection and validation

Adding a device SHALL use the running discovery cache when available or fall back to a short discovery run. The chooser SHALL omit discovered IDs already in the current entry and offer `...` for manual entry. Device settings SHALL include friendly name, host, ID, local key, version `3.1`–`3.4` (default `3.3`), debug flag (default false), optional integer scan interval, and optional comma-separated manual and reset DPs.

#### Scenario: Choose a discovered device
- **WHEN** a user selects a broadcast device
- **THEN** the form pre-fills host, ID and advertised version
- **AND** matching cloud data supplies preferred name and local key if available, and the selected device's product name is used for its model

#### Scenario: Live DP probe and manual fallback
- **WHEN** a new device form is submitted
- **THEN** a temporary LAN connection runs DP detection, optionally retries after sending configured reset IDs on probe failure, and is closed in `finally`
- **AND** when the manual DP field is present, missing manual IDs and configured reset IDs are included with a setup placeholder of `-1`

#### Scenario: Add fails validation
- **WHEN** validation reports refused/reset connection, an uncaught `ValueError`, no usable DPs, or another exception
- **THEN** the form reports `cannot_connect`, `invalid_auth`, `empty_dps`, or `unknown` respectively

#### Scenario: Fallback discovery fails to bind
- **WHEN** fallback discovery reports `EADDRINUSE`
- **THEN** the selection form shows `address_in_use`
- **AND** other discovery failures are surfaced as `discovery_failed`

### Requirement: Entity binding and persistence

The flow SHALL support `binary_sensor`, `climate`, `cover`, `fan`, `light`, `number`, `select`, `sensor`, `switch`, and `vacuum`. A new entity SHALL have a name, an unused primary DP, a platform, and the options provided by the platform schema. Discovered options SHALL be shown as `<dp> (value: <value>)`; selected labels SHALL be stored as integer DP IDs, distinct from displayed values.

#### Scenario: Configure additional entities
- **WHEN** the first entity has been configured and unused DPs remain
- **THEN** the user can finish (the default) or choose another platform and unused primary DP

#### Scenario: No unused DPs remain
- **WHEN** the last available primary DP has been bound
- **THEN** the add flow saves without asking for another platform

### Requirement: Edit existing device and entity settings

Editing SHALL select from devices in the current entry, preserve the device ID, and use saved DP labels (or `1`–`255` with `?` values if absent). A different cached cloud key SHALL be offered as the default. The normal edit path SHALL retain only selected entities and preserve their primary IDs and platforms; it removes matching registry entries before saving so retained entities are recreated.

#### Scenario: Edit two retained entities
- **WHEN** two existing entities are selected for normal edit
- **THEN** the flow requests their settings one at a time, with the existing values filled in
- **AND** the resulting device config is saved only after both forms are complete

#### Scenario: Open an edit form with a new cached key
- **WHEN** the cloud cache has a different local key
- **THEN** it is offered as the default and is not saved merely by opening the form

#### Scenario: No entity selected for normal edit
- **WHEN** a user submits the edit form with no selected entities and Add Entities disabled
- **THEN** the flow aborts with `no_entities`

#### Scenario: Append an entity without removing the previous ones
- **WHEN** Add Entities is enabled and an unused saved DP is configured
- **THEN** the new binding is saved alongside existing bindings, without a new LAN validation
