# Optional Tuya cloud metadata

## Purpose

Fetch the linked user's device inventory and local credentials without putting normal control on the cloud path. Sources: [`cloud_api.py`](../../../custom_components/localtuya/cloud_api.py), [`config_flow.py`](../../../custom_components/localtuya/config_flow.py), and [`common.py`](../../../custom_components/localtuya/common.py).

## Requirements

### Requirement: Signed regional metadata requests

The client SHALL use `https://openapi.tuya<region>.com`, GET `/v1.0/token?grant_type=1` to obtain an access token, then GET `/v1.0/users/<user_id>/devices` for inventory. Requests SHALL run via Home Assistant's executor and include client ID, access token, millisecond timestamp, sign method and uppercase HMAC-SHA256 signature. The signature input includes client ID, current token, timestamp, method, body SHA256, declared signed headers, and request path with query.

#### Scenario: Inventory request succeeds
- **WHEN** the cloud returns a successful device list
- **THEN** the prior inventory is replaced with records indexed by their Tuya `id`
- **AND** matching records can supply device names, product names, and local keys

#### Scenario: Cloud rejects credentials at startup
- **WHEN** token acquisition returns a failure result
- **THEN** startup logs the failure and skips the inventory request, but still proceeds with LAN device setup

### Requirement: Cloud is optional for normal control

An entry with cloud disabled (including a missing `no_cloud` flag at runtime) SHALL skip the startup token and inventory requests. An entry with cloud enabled SHALL attempt both at setup, subject to token success. Local data-plane writes and pushes SHALL use the LAN session rather than cloud control endpoints.

#### Scenario: LAN-only installation
- **WHEN** a configured device has a working local key and the entry has cloud disabled
- **THEN** the device can be connected to and controlled without cloud account setup

### Requirement: Refresh a stored local key from inventory

When the runtime key-recovery routine runs, it SHALL request a fresh list using the current client. If a matching record exists it SHALL save its `local_key` into the device configuration and update `updated_at`, so the entry listener can reload with that key. The implemented exception path into recovery only handles `UnicodeDecodeError` and `JSONDecodeError` that escape the inner status handling.

#### Scenario: Matching replacement key is returned
- **WHEN** recovery fetches a device record for the configured ID
- **THEN** the record's key replaces the stored key; a missing device record leaves the key unchanged
