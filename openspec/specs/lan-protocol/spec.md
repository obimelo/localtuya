# Tuya LAN protocol

## Purpose

Transport local status and control over TCP. Source: [`pytuya/__init__.py`](../../../custom_components/localtuya/pytuya/__init__.py). Protocol behavior is implementation-derived, not a guarantee for every Tuya model.

## Requirements

### Requirement: Connect and exchange Tuya frames

The transport SHALL default to TCP port `6668`, wait up to five seconds for the connection-ready future after transport creation, and use five-second response waits. It SHALL parse and encode the [frame format](#frame-and-version-reference), using sequence numbers starting at 1 and incrementing on transmission.

#### Scenario: Invalid frame header
- **WHEN** the prefix is invalid or the declared length exceeds 1000 bytes
- **THEN** the parser raises a decode error

#### Scenario: Reply and pushed status arrive together
- **WHEN** complete frames arrive in one TCP callback
- **THEN** the dispatcher consumes them in order, delivers a matching reply to its waiter, and handles an unmatched `STATUS` as a push unless a reset waiter is active

#### Scenario: Exceptional response sequencing
- **WHEN** heartbeat, refresh/reset or session-key replies do not match a normal waiter
- **THEN** the dispatcher can route them to the dedicated heartbeat, reset or negotiation waiter

#### Scenario: Empty acknowledgement
- **WHEN** heartbeat or control is answered by an empty payload
- **THEN** it is treated as an acknowledgement without a JSON response

### Requirement: Version-specific encapsulation and commands

The transport SHALL use the [version-specific command and payload encoding](#frame-and-version-reference). Query, update, heartbeat and session negotiation commands in the header exclusion list omit the 3.x payload header.

#### Scenario: Device requires the alternative query
- **WHEN** a decoded response contains `data unvalid` and changes the device type
- **THEN** the command is retried with the new type's command and payload policy

#### Scenario: First 3.4 exchange
- **WHEN** the active key is still the configured key
- **THEN** the protocol attempts session negotiation before sending the ordinary command
- **AND** successful negotiation derives the active key from both nonces and updates the dispatcher key

#### Scenario: DPS is nested in a 3.4 reply
- **WHEN** decoded JSON has `data.dps` but no top-level `dps`
- **THEN** it normalizes the nested map for status processing

### Requirement: Data points and device liveness

The protocol SHALL merge queried and pushed DPS into its cache. Single writes SHALL stringify the DP ID and use the same control path as multi-DP writes. DP probing SHALL clear the cache, then request DP 1 and batches `2–10`, `11–20`, `21–30` and `100–110`, stopping after the first query if the device remains `type_0a`.

#### Scenario: Request a timed refresh
- **WHEN** `update_dps()` runs on 3.2, 3.3, or 3.4 without explicit IDs
- **THEN** it probes when the cache is empty, selects cached IDs intersecting `18`, `19`, and `20` when possible, and writes `UPDATEDPS` without awaiting a reply
- **AND** the default payload uses `[18, 19, 20]` when no list is derived on a fresh template

#### Scenario: Request a reset
- **WHEN** `reset(ids)` is called on 3.3
- **THEN** it switches to `type_0a` and exchanges `UPDATEDPS` with those IDs
- **AND** other versions return without transmitting a reset

### Requirement: Heartbeat and connection closure

Heartbeat SHALL run immediately on start, wait ten seconds between successful calls, and close the transport on failure. Explicit close SHALL cancel heartbeat and unblock pending response waiters.

#### Scenario: Heartbeat wait times out
- **WHEN** a heartbeat does not get a reply in five seconds
- **THEN** the heartbeat loop closes the transport rather than sending another heartbeat

## Frame and version reference

Frames use a big-endian header with prefix `0x000055AA`, sequence, command, and length. The receive path extracts a return code, payload, and CRC32 (3.1–3.3) or HMAC-SHA256 (3.4) trailer with suffix `0x0000AA55`. Integrity mismatches are logged but the decoder can still return the frame.

| Version | Payload and command behavior |
| --- | --- |
| 3.1 | Default query `0x0A`; control `0x07` uses `3.1`, a truncated MD5 hex digest and Base64 AES-ECB ciphertext; other outgoing commands are not encrypted |
| 3.2 | AES-ECB binary payloads with the version header outside ciphertext where applicable; starts as `type_0d`, querying with `0x0D` and null-valued requested IDs |
| 3.3 | Same general AES/header placement, starts as `type_0a`; may switch to `type_0d` |
| 3.4 | AES-ECB encrypts the header along with the payload where applicable; ordinary queries use `0x10`, control uses `0x0D` with `protocol: 5` and nested `data.dps` |
