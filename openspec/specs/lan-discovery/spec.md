# LAN discovery

## Purpose

Listen for Tuya broadcasts and reconcile configured device addresses and product keys. Sources: [`discovery.py`](../../../custom_components/localtuya/discovery.py) and [`__init__.py`](../../../custom_components/localtuya/__init__.py).

## Requirements

### Requirement: Broadcast listeners and cache

Discovery SHALL listen on IPv4 UDP ports `6666` and `6667` with port reuse. It SHALL remove the 20-byte prefix and eight-byte trailer, try the Tuya UDP AES decryption, fall back to plaintext decoding when decryption raises, and parse the result as JSON. It SHALL cache the first decoded record per `gwId` and call the registered callback for each decoded broadcast, including repeats.

#### Scenario: Repeated announcement
- **WHEN** the same ID broadcasts again with a different IP
- **THEN** the cached first record remains unchanged and the callback receives the new announcement

### Requirement: Discovery lifetime and address reconciliation

Integration discovery SHALL run until Home Assistant stops; inability to start it is logged and does not by itself stop integration setup. Standalone discovery SHALL listen for six seconds and close its listeners in `finally`. Reconciliation SHALL ignore unconfigured IDs. A changed `ip` or `productKey` SHALL update the entry and trigger reload; otherwise an announcement for a configured disconnected device SHALL request reconnection.

#### Scenario: Device changes IP after DHCP renewal
- **WHEN** a configured ID broadcasts a different address
- **THEN** LocalTuya saves the new `host`, refreshes `updated_at`, and notifies Home Assistant of the entry update

#### Scenario: Device not yet configured
- **WHEN** a broadcast does not match any configured device
- **THEN** it can appear in the add flow but does not create a runtime connection by itself
