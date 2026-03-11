"""Sensor platform for Smart TRV Thermostat runtime stats."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ATTR_HEATING_SECONDS,
    ATTR_IDLE_SECONDS,
    CONF_ENABLE_RUNTIME_STATS,
    CONF_NAME,
    DOMAIN,
)


@dataclass
class RuntimeSensorDescription:
    key: str
    name_suffix: str
    attribute: str


SENSORS = [
    RuntimeSensorDescription("heating", "Heating time", ATTR_HEATING_SECONDS),
    RuntimeSensorDescription("idle", "Idle time", ATTR_IDLE_SECONDS),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    cfg = {**entry.data, **entry.options}
    if not cfg.get(CONF_ENABLE_RUNTIME_STATS, False):
        return
    async_add_entities([SmartTrvRuntimeSensor(hass, entry, desc) for desc in SENSORS])


class SmartTrvRuntimeSensor(SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, description: RuntimeSensorDescription) -> None:
        self.hass = hass
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = f"{entry.title} {description.name_suffix}"
        self._attr_native_value = 0
        self._climate_entity_id = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        climate = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("climate")
        if climate is not None:
            self._climate_entity_id = climate.entity_id
            self._refresh_from_climate()
            self.async_on_remove(
                async_track_state_change_event(self.hass, [self._climate_entity_id], self._handle_climate_change)
            )

    @callback
    def _handle_climate_change(self, event) -> None:
        self._refresh_from_state(event.data.get("new_state"))
        self.async_write_ha_state()

    @callback
    def _refresh_from_climate(self) -> None:
        if self._climate_entity_id:
            self._refresh_from_state(self.hass.states.get(self._climate_entity_id))

    @callback
    def _refresh_from_state(self, state) -> None:
        if state is None:
            return
        self._attr_native_value = int(state.attributes.get(self.entity_description.attribute, 0) or 0)
