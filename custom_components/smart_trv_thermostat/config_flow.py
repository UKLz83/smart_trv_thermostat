"""Config flow for Smart TRV Thermostat."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_BOILER_ENTITY,
    CONF_BOILER_MODE,
    CONF_CLOSE_VALVE_TEMP,
    CONF_ENABLE_BOILER_COORD,
    CONF_ENABLE_RUNTIME_STATS,
    CONF_HEAT_DELTA,
    CONF_HUMIDITY_ENTITY,
    CONF_MAX_TEMP,
    CONF_MIN_HEATING_TIME,
    CONF_MIN_IDLE_TIME,
    CONF_MIN_TEMP,
    CONF_OPEN_VALVE_TEMP,
    CONF_PRECISION,
    CONF_REACTION_SPEED,
    CONF_SENSOR_ENTITY,
    CONF_SENSOR_OFFSET,
    CONF_STOP_DELTA,
    CONF_TARGET_TEMP,
    CONF_TRV_ENTITY,
    CONF_WINDOW_CLOSE_DELAY,
    CONF_WINDOW_ENTITY,
    CONF_WINDOW_OPEN_DELAY,
    DEFAULT_BOILER_MODE,
    DEFAULT_CLOSE_VALVE_TEMP,
    DEFAULT_ENABLE_BOILER_COORD,
    DEFAULT_ENABLE_RUNTIME_STATS,
    DEFAULT_HEAT_DELTA,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_HEATING_TIME,
    DEFAULT_MIN_IDLE_TIME,
    DEFAULT_MIN_TEMP,
    DEFAULT_OPEN_VALVE_TEMP,
    DEFAULT_PRECISION,
    DEFAULT_REACTION_SPEED,
    DEFAULT_SENSOR_OFFSET,
    DEFAULT_STOP_DELTA,
    DEFAULT_TARGET_TEMP,
    DEFAULT_WINDOW_CLOSE_DELAY,
    DEFAULT_WINDOW_OPEN_DELAY,
    DOMAIN,
)

REACTION_OPTIONS = ["slow", "normal", "fast"]
BOILER_MODE_OPTIONS = ["independent", "master_thermostat", "multi_room_coordinator"]
TEMP_SOURCE_DOMAINS = ["sensor", "input_number", "number", "weather"]
HUMIDITY_SOURCE_DOMAINS = ["sensor", "input_number", "number", "weather"]


def _build_schema(current: dict[str, Any] | None = None) -> vol.Schema:
    current = current or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=current.get(CONF_NAME, "")): selector.TextSelector(),
            vol.Required(
                CONF_TRV_ENTITY,
                default=current.get(CONF_TRV_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="climate")),
            vol.Required(
                CONF_SENSOR_ENTITY,
                default=current.get(CONF_SENSOR_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain=TEMP_SOURCE_DOMAINS)),
            vol.Optional(
                CONF_HUMIDITY_ENTITY,
                default=current.get(CONF_HUMIDITY_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain=HUMIDITY_SOURCE_DOMAINS)),
            vol.Optional(
                CONF_WINDOW_ENTITY,
                default=current.get(CONF_WINDOW_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
            vol.Optional(
                CONF_BOILER_ENTITY,
                default=current.get(CONF_BOILER_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain=["switch", "climate", "input_boolean"])),
            vol.Optional(
                CONF_ENABLE_BOILER_COORD,
                default=current.get(CONF_ENABLE_BOILER_COORD, DEFAULT_ENABLE_BOILER_COORD),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_BOILER_MODE,
                default=current.get(CONF_BOILER_MODE, DEFAULT_BOILER_MODE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=BOILER_MODE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional(
                CONF_ENABLE_RUNTIME_STATS,
                default=current.get(CONF_ENABLE_RUNTIME_STATS, DEFAULT_ENABLE_RUNTIME_STATS),
            ): selector.BooleanSelector(),
            vol.Optional(CONF_MIN_TEMP, default=current.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)): vol.Coerce(float),
            vol.Optional(CONF_MAX_TEMP, default=current.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)): vol.Coerce(float),
            vol.Optional(CONF_TARGET_TEMP, default=current.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)): vol.Coerce(float),
            vol.Optional(CONF_HEAT_DELTA, default=current.get(CONF_HEAT_DELTA, DEFAULT_HEAT_DELTA)): vol.Coerce(float),
            vol.Optional(CONF_STOP_DELTA, default=current.get(CONF_STOP_DELTA, DEFAULT_STOP_DELTA)): vol.Coerce(float),
            vol.Optional(CONF_SENSOR_OFFSET, default=current.get(CONF_SENSOR_OFFSET, DEFAULT_SENSOR_OFFSET)): vol.Coerce(float),
            vol.Optional(CONF_MIN_HEATING_TIME, default=current.get(CONF_MIN_HEATING_TIME, DEFAULT_MIN_HEATING_TIME)): vol.Coerce(int),
            vol.Optional(CONF_MIN_IDLE_TIME, default=current.get(CONF_MIN_IDLE_TIME, DEFAULT_MIN_IDLE_TIME)): vol.Coerce(int),
            vol.Optional(CONF_OPEN_VALVE_TEMP, default=current.get(CONF_OPEN_VALVE_TEMP, DEFAULT_OPEN_VALVE_TEMP)): vol.Coerce(float),
            vol.Optional(CONF_CLOSE_VALVE_TEMP, default=current.get(CONF_CLOSE_VALVE_TEMP, DEFAULT_CLOSE_VALVE_TEMP)): vol.Coerce(float),
            vol.Optional(CONF_WINDOW_OPEN_DELAY, default=current.get(CONF_WINDOW_OPEN_DELAY, DEFAULT_WINDOW_OPEN_DELAY)): vol.Coerce(int),
            vol.Optional(CONF_WINDOW_CLOSE_DELAY, default=current.get(CONF_WINDOW_CLOSE_DELAY, DEFAULT_WINDOW_CLOSE_DELAY)): vol.Coerce(int),
            vol.Optional(
                CONF_REACTION_SPEED,
                default=current.get(CONF_REACTION_SPEED, DEFAULT_REACTION_SPEED),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=REACTION_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional(CONF_PRECISION, default=current.get(CONF_PRECISION, DEFAULT_PRECISION)): vol.Coerce(float),
        }
    )


class SmartTrvConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart TRV Thermostat."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_TRV_ENTITY]}::{user_input[CONF_SENSOR_ENTITY]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=_build_schema(), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return SmartTrvOptionsFlowHandler(config_entry)


class SmartTrvOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_build_schema(current))
