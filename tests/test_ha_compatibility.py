"""Exercise LocalTuya against installed Home Assistant APIs without a Tuya device."""

from importlib import import_module
from pathlib import Path
from shutil import copytree, ignore_patterns
from tempfile import TemporaryDirectory
from types import MappingProxyType
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, patch

from homeassistant import bootstrap, config_entries, loader
from homeassistant.components.light import ATTR_COLOR_TEMP_KELVIN, ColorMode
from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory

from custom_components.localtuya import config_flow
from custom_components.localtuya.climate import LocaltuyaClimate
from custom_components.localtuya.const import PLATFORMS
from custom_components.localtuya.light import LocaltuyaLight
from custom_components.localtuya.vacuum import LocaltuyaVacuum

DOMAIN = "localtuya"
DEVICE = {
    "device_id": "test_device",
    "friendly_name": "Test device",
    "host": "192.0.2.10",
    "local_key": "0000000000000000",
    "protocol_version": "3.3",
    "enable_debug": False,
}


def make_entity(cls, **settings):
    """Construct a configured entity with recorded LAN writes."""
    device = Mock(set_dp=AsyncMock(), set_dps=AsyncMock())
    config = {**DEVICE, "entities": [{"id": 1, "friendly_name": "Test", **settings}]}
    return cls(device, config, 1), device


class PlatformTests(IsolatedAsyncioTestCase):
    async def test_light_kelvin_round_trip_and_limits(self):
        for reverse, warm_dp, cool_dp in ((False, 0, 1000), (True, 1000, 0)):
            with self.subTest(reverse=reverse):
                entity, device = make_entity(
                    LocaltuyaLight, color_temp=2, color_temp_reverse=reverse
                )
                for kelvin, raw in ((2700, warm_dp), (6500, cool_dp)):
                    entity._status = {"1": True, "2": raw}
                    entity.status_updated()
                    self.assertEqual(entity.color_temp_kelvin, kelvin)
                    await entity.async_turn_on(**{ATTR_COLOR_TEMP_KELVIN: kelvin})
                    device.set_dps.assert_awaited_with({2: raw})
                self.assertEqual(entity.color_mode, ColorMode.COLOR_TEMP)

    async def test_light_uses_hs_for_unknown_color_mode(self):
        entity, _ = make_entity(
            LocaltuyaLight, color_temp=2, color=3, color_mode=4, scene=5
        )
        entity._status = {"1": True, "2": 0, "3": "007803e801f4", "4": "unknown"}
        entity.status_updated()
        self.assertIn(entity.color_mode, entity.supported_color_modes)
        self.assertIn("Scenario 1", entity.effect_list)

    async def test_climate_device_native_units_and_scaling(self):
        entity, device = make_entity(
            LocaltuyaClimate,
            temperature_unit="fahrenheit",
            target_temperature_dp=2,
            current_temperature_dp=3,
            precision=0.5,
            target_precision=0.5,
        )
        entity._status = {"1": True, "2": 144, "3": 140}
        entity.status_updated()
        self.assertEqual(entity.native_temperature_unit, "°F")
        self.assertEqual(entity.native_current_temperature, 70)
        self.assertEqual(entity.native_target_temperature, 72)
        await entity.async_set_temperature(temperature=73.5)
        device.set_dp.assert_awaited_once_with(147, 2)

    async def test_vacuum_activity_and_optional_commands(self):
        entity, device = make_entity(
            LocaltuyaVacuum,
            idle_status_value="standby",
            docked_status_value="charging",
            returning_status_value="docking",
            paused_state="paused",
            mode_dp=2,
            return_mode="chargego",
            stop_status="standby",
            battery_dp=3,
        )
        entity._status = {"1": "charging", "3": 80}
        entity.status_updated()
        self.assertEqual(entity.activity, VacuumActivity.DOCKED)
        self.assertEqual(entity.state, "docked")
        self.assertEqual(entity.extra_state_attributes["battery_level"], 80)
        self.assertIn(VacuumEntityFeature.RETURN_HOME, entity.supported_features)
        await entity.async_return_to_base()
        device.set_dp.assert_awaited_once_with("chargego", 2)


class SchemaTests(TestCase):
    def test_all_platforms_import_and_build_forms(self):
        dp_labels = ["1 (value: True)", "2 (value: 500)"]
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                mod = import_module(f"custom_components.localtuya.{platform}")
                self.assertTrue(callable(mod.async_setup_entry))
                schema = config_flow.platform_schema(platform, dp_labels)
                self.assertIn("id", schema.schema)
                self.assertEqual(
                    "entity_section" in schema.schema,
                    platform not in ("sensor", "binary_sensor"),
                )

    def test_form_defaults_do_not_leak_between_devices(self):
        first = config_flow.schema_defaults(config_flow.DEVICE_SCHEMA, host="192.0.2.10")
        second = config_flow.schema_defaults(config_flow.DEVICE_SCHEMA, host="192.0.2.20")
        def host_default(schema):
            return next(
                marker.default() for marker in schema.schema if marker.schema == "host"
            )

        self.assertEqual(host_default(first), "192.0.2.10")
        self.assertEqual(host_default(second), "192.0.2.20")


class EntryTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        directory = self.enterContext(TemporaryDirectory())
        integration_dir = Path(__file__).resolve().parents[1] / "custom_components"
        copytree(
            integration_dir,
            Path(directory) / "custom_components",
            ignore=ignore_patterns("__pycache__"),
        )
        self.hass = HomeAssistant(directory)
        loader.async_setup(self.hass)
        self.hass.config.skip_pip = True
        self.hass.config_entries = config_entries.ConfigEntries(self.hass, {})
        self.addAsyncCleanup(self.hass.async_stop, force=True)
        await bootstrap.async_load_base_functionality(self.hass)
        self.enterContext(
            patch("custom_components.localtuya.TuyaDiscovery.start", new_callable=AsyncMock)
        )
        self.enterContext(patch("custom_components.localtuya.TuyaDevice.async_connect"))

    async def test_v1_migrates_and_light_handles_core_service_call(self):
        entry = config_entries.ConfigEntry(
            data={
                **DEVICE,
                "entities": [
                    {"id": 1, "platform": "light", "friendly_name": "Lamp", "color_temp": 2}
                ],
            },
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=1,
            options={},
            source=config_entries.SOURCE_USER,
            subentries_data=None,
            title="Old device entry",
            unique_id=DEVICE["device_id"],
            version=1,
        )
        await self.hass.config_entries.async_add(entry)
        await self.hass.async_block_till_done()
        self.assertEqual(entry.version, 2)
        self.assertTrue(entry.data["no_cloud"])
        self.assertEqual(entry.state, config_entries.ConfigEntryState.LOADED)
        registry = er.async_get(self.hass)
        entity_id = registry.async_get_entity_id("light", DOMAIN, "local_test_device_1")
        device = self.hass.data[DOMAIN]["tuya_devices"][DEVICE["device_id"]]
        device.status_updated({"1": True, "2": 0})
        await self.hass.async_block_till_done()
        self.assertEqual(self.hass.states.get(entity_id).attributes[ATTR_COLOR_TEMP_KELVIN], 2700)
        with patch.object(device, "set_dps", AsyncMock()) as write:
            await self.hass.services.async_call(
                "light",
                "turn_on",
                {"entity_id": entity_id, ATTR_COLOR_TEMP_KELVIN: 6500},
                blocking=True,
            )
            write.assert_awaited_once_with({2: 1000})

    async def test_lan_only_setup_options_reload_and_registry_identity(self):
        manager = self.hass.config_entries
        result = await manager.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await manager.flow.async_configure(result["flow_id"], {"no_cloud": False})
        self.assertEqual(result["errors"]["base"], "authentication_failed")
        result = await manager.flow.async_configure(result["flow_id"], {"no_cloud": True})
        self.assertEqual(result["type"], FlowResultType.CREATE_ENTRY)
        entry = result["result"]
        self.assertEqual(entry.data["region"], "eu")
        self.assertEqual(entry.data["devices"], {})

        result = await manager.options.async_init(entry.entry_id)
        flow_id = result["flow_id"]
        await manager.options.async_configure(flow_id, {"action": "add_device"})
        await manager.options.async_configure(flow_id, {"selected_device": "..."})
        labels = ["1 (value: True)", "2 (value: False)"]
        with patch.object(config_flow, "validate_input", AsyncMock(return_value=labels)):
            await manager.options.async_configure(flow_id, DEVICE)
        await manager.options.async_configure(flow_id, {"platform_to_add": "switch"})
        await manager.options.async_configure(
            flow_id,
            {
                "friendly_name": "Relay",
                "id": labels[0],
                "restore_on_reconnect": False,
                "is_passive_entity": False,
            },
        )
        await manager.options.async_configure(
            flow_id, {"platform_to_add": "binary_sensor", "no_additional_entities": False}
        )
        result = await manager.options.async_configure(
            flow_id, {"id": labels[1], "friendly_name": "Contact"}
        )
        self.assertEqual(result["type"], FlowResultType.CREATE_ENTRY)
        await self.hass.async_block_till_done()
        registry = er.async_get(self.hass)
        switch_id = registry.async_get_entity_id("switch", DOMAIN, "local_test_device_1")
        self.assertIsNotNone(switch_id)
        self.assertIsNone(registry.async_get(switch_id).entity_category)
        registry.async_update_entity(
            switch_id, new_entity_id="switch.my_relay", name="Custom relay"
        )
        sensor_id = registry.async_get_entity_id(
            "binary_sensor", DOMAIN, "local_test_device_2"
        )
        self.assertIsNotNone(sensor_id)
        self.assertIsNone(registry.async_get(sensor_id).entity_category)

        result = await manager.options.async_init(entry.entry_id)
        flow_id = result["flow_id"]
        await manager.options.async_configure(flow_id, {"action": "edit_device"})
        await manager.options.async_configure(
            flow_id, {"selected_device": DEVICE["device_id"]}
        )
        edit = {key: value for key, value in DEVICE.items() if key != "device_id"}
        await manager.options.async_configure(flow_id, {**edit, "entities": ["1: Relay"]})
        result = await manager.options.async_configure(
            flow_id, {"friendly_name": "Updated relay", "entity_section": "config"}
        )
        self.assertEqual(result["type"], FlowResultType.CREATE_ENTRY)
        await self.hass.async_block_till_done()
        updated = registry.async_get("switch.my_relay")
        self.assertEqual(updated.name, "Custom relay")
        self.assertEqual(updated.entity_category, EntityCategory.CONFIG)
        self.assertEqual(updated.unique_id, "local_test_device_1")
        self.assertIsNone(
            registry.async_get_entity_id("binary_sensor", DOMAIN, "local_test_device_2")
        )

        result = await manager.options.async_init(entry.entry_id)
        flow_id = result["flow_id"]
        await manager.options.async_configure(flow_id, {"action": "edit_device"})
        await manager.options.async_configure(
            flow_id, {"selected_device": DEVICE["device_id"]}
        )
        result = await manager.options.async_configure(
            flow_id, {**edit, "entities": ["1: Updated relay"]}
        )
        section = next(
            marker
            for marker in result["data_schema"].schema
            if marker.schema == "entity_section"
        )
        self.assertEqual(section.default(), "config")
        result = await manager.options.async_configure(
            flow_id, {"friendly_name": "Updated relay", "entity_section": "control"}
        )
        self.assertEqual(result["type"], FlowResultType.CREATE_ENTRY)
        await self.hass.async_block_till_done()
        self.assertIsNone(registry.async_get("switch.my_relay").entity_category)

        result = await manager.options.async_init(entry.entry_id)
        flow_id = result["flow_id"]
        await manager.options.async_configure(flow_id, {"action": "add_device"})
        await manager.options.async_configure(flow_id, {"selected_device": "..."})
        with patch.object(config_flow, "validate_input", AsyncMock()) as validate:
            result = await manager.options.async_configure(flow_id, DEVICE)
        validate.assert_not_awaited()
        self.assertEqual(result["type"], FlowResultType.ABORT)
        self.assertEqual(result["reason"], "already_configured")
        self.assertTrue(await manager.async_unload(entry.entry_id))
