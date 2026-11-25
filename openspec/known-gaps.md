# Known implementation gaps

These are observations from static review, not compatibility promises or verified hardware reproductions. No fixes are part of the baseline.

| Area | Source observation |
| --- | --- |
| Diagnostic masking | Entry diagnostics partially mask credentials and configured local keys. The cloud inventory is inserted by reference, so masking it also replaces its live cached keys. Device diagnostics do not mask keys; protocol debug logging can expose session material. |
| Entry isolation | Loaded devices and platforms are tracked per entry for unload, but the cloud client is still domain-global. The flow does not implement a blanket one-entry guard; the migration shape should not be interpreted as multi-account isolation. |
| Registry diagnostics | Device diagnostics still derive the ID from the first identifier's final underscore-delimited segment, which can misidentify a device whose ID contains underscores. |
| Discovery and networking | The cache keeps the first record even after IP changes; later announcements still reach the reconciliation callback. Malformed decoded JSON/missing fields do not get an explicit per-datagram recovery path. Restart behavior and `reuse_port=True` depend on the Home Assistant host. |
| TCP stream handling | The dispatcher collects a short header across callbacks but calls the unpacker as soon as it has a receive header, even if the remainder of the frame has not arrived. The unpacker can raise on partial payloads; do not assume arbitrary fragmentation is handled cleanly. |
| LAN integrity and handshake | Frame suffix/CRC/HMAC mismatches are logged rather than uniformly rejected. The 3.4 negotiation has a fixed local nonce, logs a nonce-HMAC mismatch without stopping there, and the ordinary exchange does not check the negotiation's boolean result. This is device interoperability code, not a secure-channel guarantee. |
| Payload templates | `_generate_payload()` mutates shared dictionaries rather than copying them; optional fields and timestamp representation can carry over between calls. The whitespace removal also strips spaces inside JSON string values. |
| Initial connection and recovery | Normal status handling accepts an empty cached dictionary but the reset retry does not. A retry error outside the two decode exceptions is not caught by the outer recovery path, and the task flag is not cleared in a `finally`. |
| Cloud key recovery | Most status decode failures become PyTuya `DecodeError` or an error payload, and the first status exception may be handled without reaching the cloud recovery block. Recovery does not reauthorize an expired token, validate the returned key, or explicitly check `no_cloud`. Do not assume automatic recovery after every re-pair. |
| Cloud errors | The client has no explicit request timeout or token refresh. Non-OK HTTP handling refers to `resp.status` rather than Requests' `status_code`; some transport exceptions are only handled on the token path and can escape setup or flow. |
| Device edit and DP selection | Edits reuse cached DP labels and do not revalidate changed LAN credentials. New bindings use the filtered list of unused primary DPs for the entire form, including auxiliary selectors. |
| Partial/mismatched DP data | Configured optional DPs are not guaranteed to be present in every initial status. Switch measurement division, climate temperature multiplication, cover string/position math and light conversion assume compatible values once called. |
| Light mode selection | `color_mode_set` can be read from stored data but is not exposed by `flow_schema()`. |
| Climate range and swing | `TARGET_TEMPERATURE_RANGE` is advertised when a maximum DP is configured, but `async_set_temperature()` handles a single temperature only. Swing constants/mapping work from stored data but their fields are not exposed in the current flow schema. |
| Cover timing | Timed target commands create a target-stop task and a full-span-stop task; these are not coordinated or canceled when later motion supersedes them. Position estimates use reported state transitions rather than a continuous clock update. |
| Vacuum commands | Spot cleaning is a no-op. |
| UI strings | The three locale files have the active UI step names, while `strings.json` still contains legacy step names. Not every translated error, abort, or field maps to an active code path. |
| CI and compatibility | The compatibility workflow runs tests against pinned official Core images. Legacy `tox.ini` and its test dependency pins do not drive that workflow. HACS/Hassfest metadata validation and physical-device verification are separate. |
