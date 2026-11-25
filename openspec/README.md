# LocalTuya OpenSpec baseline

This is a source-derived description of the Home Assistant integration in this checkout (manifest version `5.2.3`; config-entry version `2`). It documents current behavior, not a proposed rewrite or a claim that every device model has been tested. Known gaps are listed separately from the requirements so they do not become contracts by accident.

## Capability index

| Area | Specs |
| --- | --- |
| Home Assistant integration | [Lifecycle, services, and migration](specs/integration-lifecycle/spec.md) · [Account, device, and entity configuration](specs/configuration/spec.md) · [Device runtime and entity state](specs/device-runtime/spec.md) |
| Connectivity | [UDP discovery](specs/lan-discovery/spec.md) · [TCP protocol 3.1–3.4](specs/lan-protocol/spec.md) · [Optional Tuya cloud metadata](specs/cloud-metadata/spec.md) |
| Troubleshooting | [Diagnostics and logging](specs/diagnostics/spec.md) · [Known gaps](known-gaps.md) |
| Basic entity platforms | [Binary sensor](specs/binary-sensor/spec.md) · [Sensor](specs/sensor/spec.md) · [Switch](specs/switch/spec.md) · [Number](specs/number/spec.md) · [Select](specs/select/spec.md) |
| Device controllers | [Fan](specs/fan/spec.md) · [Cover](specs/cover/spec.md) · [Vacuum](specs/vacuum/spec.md) · [Light](specs/light/spec.md) · [Climate](specs/climate/spec.md) |

## Architecture and code map

```text
Home Assistant config/options flow ─── config entry ─── integration setup
          │                                ▲                    │
          ├── LAN probe                    │                    ├── TuyaDevice (per ID)
          └── optional cloud inventory    │                    │       ↕ TCP / PyTuya
                     │                     │                    │   Tuya device
                     └─ name/model/key     │                    │       ↑ UDP broadcast
                                           │                    └── discovery callback
                                           └── host/product/key updates

Home Assistant entity ── command ──> TuyaDevice ──> TCP
Home Assistant entity <── dispatcher/cache <────── TCP reply or push
```

| Component | Implementation |
| --- | --- |
| Bootstrap, discovery reconciliation, migration, services, registry removal | [`__init__.py`](../custom_components/localtuya/__init__.py), [`manifest.json`](../custom_components/localtuya/manifest.json), [`services.yaml`](../custom_components/localtuya/services.yaml) |
| UI, schemas, validation, persistence, shared key names | [`config_flow.py`](../custom_components/localtuya/config_flow.py), [`const.py`](../custom_components/localtuya/const.py), and each platform's `flow_schema()` |
| Platform forwarding target, connection wrapper, entity dispatcher and restoration | [`common.py`](../custom_components/localtuya/common.py) |
| Network transports | [`discovery.py`](../custom_components/localtuya/discovery.py), [`pytuya/__init__.py`](../custom_components/localtuya/pytuya/__init__.py), [`cloud_api.py`](../custom_components/localtuya/cloud_api.py) |
| Troubleshooting | [`diagnostics.py`](../custom_components/localtuya/diagnostics.py), protocol and integration loggers, [`README.md`](../README.md) |
| Localization | [`translations/en.json`](../custom_components/localtuya/translations/en.json), [`it.json`](../custom_components/localtuya/translations/it.json), [`pt-BR.json`](../custom_components/localtuya/translations/pt-BR.json), and the older [`strings.json`](../custom_components/localtuya/strings.json) template |
| Distribution and checks | [`hacs.json`](../hacs.json), [`info.md`](../info.md), [HACS/Hassfest workflow](../.github/workflows/validate.yml), [tox workflow](../.github/workflows/tox.yaml), [`tox.ini`](../tox.ini), [`requirements_test.txt`](../requirements_test.txt), [`pyproject.toml`](../pyproject.toml), [`setup.cfg`](../setup.cfg), [`pylint.rc`](../pylint.rc), [Dependabot config](../.dependabot/config.yml), [issue template](../.github/ISSUE_TEMPLATE/bug_report.md) |

The installation unit is `custom_components/localtuya/`, distributed through HACS or copied into Home Assistant manually. HACS declares Home Assistant `2024.1.0` as its minimum; this is package metadata, not a tested compatibility matrix. The manifest declares no additional dependencies or pip requirements; the integration code imports Home Assistant, Voluptuous, Requests, and Cryptography. `img/` contains documentation and branding assets. `tuyadebug.tgz` is a separate debugging bundle containing TinyTuya, a separate LocalTuya/PyTuya snapshot, scripts, and compiled cache files. The integration does not import it, and it is not run by CI; it is not a source of requirements for the active component.

## Data boundaries

| Boundary | Shape and ownership |
| --- | --- |
| Config entry | `region`, `client_id`, `client_secret`, `user_id`, `username`, `no_cloud`, `devices`, and optional `updated_at` (epoch milliseconds as a string). Main device/account changes write `ConfigEntry.data`, not the options result. |
| `devices[device_id]` | Device `device_id`, `friendly_name`, `host`, `local_key`, `protocol_version`, `enable_debug`; optional `scan_interval`, `manual_dps_strings`, `reset_dpids`, `model`, and `product_key`; saved `dps_strings` and `entities` array. |
| Entity config | `id` (integer primary DP), `platform`, `friendly_name`, and platform-specific values or auxiliary integer DP bindings. Discovery labels are preserved separately from stored IDs. |
| Runtime | `hass.data["localtuya"]` holds `tuya_devices`, `cloud_data`, optional `discovery`, and the entry-keyed unload-listener record. Discovery uses `gwId` and cloud uses `id`; config and runtime join on the Tuya device ID rather than the Home Assistant registry UUID. |
| Device status | DPS maps keyed by string IDs with device-specific JSON values. Protocol and wrapper each maintain a merged cache; entities consume copies via Home Assistant dispatch. A reported value is not a command acknowledgement. |
| Sensitive data | Cloud credentials and local keys live in entry data. Diagnostic exports and debug logs are not guaranteed to redact them. Use synthetic data when reproducing issues and review artifacts before sharing. |

## Use and verification

With [OpenSpec](https://openspec.dev/docs/installation) available on `PATH`:

```text
openspec list --specs
openspec validate --specs --strict
```

Project-scoped OpenCode skills are in [`.agents/skills/`](../.agents/skills/). For future changes, use `/openspec-propose`, make the spec deltas under `openspec/changes/`, and archive when the implementation and verification are complete. Put agreed behavior in the relevant capability rather than duplicating it in a new project document.

OpenSpec validation checks Markdown structure, not the Python implementation. The repository has no active behavior test suite: the default tox test command is a placeholder. For runtime changes, use integration tests or mocks for entry migration, flow failures, cloud opt-out, LAN dispatch and reconnect, protocol fixtures per version, and input/output checks per affected platform. Verify real-device interoperability separately where the behavior depends on device firmware, DP layout, or LAN conditions.
