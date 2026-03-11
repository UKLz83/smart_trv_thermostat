"""Climate platform for Smart TRV Thermostat."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACAction, HVACMode
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_OPEN, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import State

from .const import (
    ATTR_BOILER_COORDINATED,
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_SENSOR_TEMPERATURE,
    ATTR_CYCLE_LOCK_UNTIL,
    ATTR_EFFECTIVE_TEMPERATURE,
    ATTR_HEAT_REQUEST,
    ATTR_HEATING_SECONDS,
    ATTR_IDLE_SECONDS,
    ATTR_LAST_CHANGE,
    ATTR_LAST_DECISION,
    ATTR_TRV_TARGET,
    ATTR_WINDOW_OPEN,
    ATTR_WINDOW_SINCE,
    CONF_BOILER_ENTITY,
    CONF_BOILER_MODE,
    CONF_CLOSE_VALVE_TEMP,
    CONF_ENABLE_BOILER_COORD,
    CONF_HEAT_DELTA,
    CONF_HUMIDITY_ENTITY,
    CONF_MAX_TEMP,
    CONF_MIN_HEATING_TIME,
    CONF_MIN_IDLE_TIME,
    CONF_MIN_TEMP,
    CONF_NAME,
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
    DEFAULT_CLOSE_VALVE_TEMP,
    DEFAULT_HEAT_DELTA,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_HEATING_TIME,
    DEFAULT_MIN_IDLE_TIME,
    DEFAULT_MIN_TEMP,
    DEFAULT_OPEN_VALVE_TEMP,
    DEFAULT_PRECISION,
    DEFAULT_SENSOR_OFFSET,
    DEFAULT_STOP_DELTA,
    DEFAULT_TARGET_TEMP,
    DEFAULT_WINDOW_CLOSE_DELAY,
    DEFAULT_WINDOW_OPEN_DELAY,
    DOMAIN,
    REACTION_PRESETS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entity = SmartTrvClimate(hass, entry)
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})["climate"] = entity
    async_add_entities([entity])


@dataclass
class RuntimeState:
    heat_request: bool = False
    hvac_mode: HVACMode = HVACMode.HEAT
    hvac_action: HVACAction = HVACAction.IDLE
    last_decision: str = "startup"
    last_change: datetime | None = None
    window_since_open: datetime | None = None
    window_since_closed: datetime | None = None
    heating_seconds: int = 0
    idle_seconds: int = 0


class SmartTrvClimate(ClimateEntity, RestoreEntity):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = 1  # TARGET_TEMPERATURE
    _attr_temperature_unit = "°C"
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        cfg = {**entry.data, **entry.options}

        self._attr_unique_id = entry.entry_id
        self._attr_name = cfg[CONF_NAME]

        self._trv_entity = cfg[CONF_TRV_ENTITY]
        self._sensor_entity = cfg[CONF_SENSOR_ENTITY]
        self._humidity_entity = cfg.get(CONF_HUMIDITY_ENTITY)
        self._window_entity = cfg.get(CONF_WINDOW_ENTITY)
        self._boiler_entity = cfg.get(CONF_BOILER_ENTITY)
        self._enable_boiler_coord = cfg.get(CONF_ENABLE_BOILER_COORD, False)
        self._boiler_mode = cfg.get(CONF_BOILER_MODE)
        self._enable_runtime_stats = cfg.get('enable_runtime_stats', False)

        self._min_temp = float(cfg.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP))
        self._max_temp = float(cfg.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP))
        self._target_temperature = float(cfg.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP))
        self._sensor_offset = float(cfg.get(CONF_SENSOR_OFFSET, DEFAULT_SENSOR_OFFSET))
        self._heat_delta = float(cfg.get(CONF_HEAT_DELTA, DEFAULT_HEAT_DELTA))
        self._stop_delta = float(cfg.get(CONF_STOP_DELTA, DEFAULT_STOP_DELTA))
        self._min_heating_time = int(cfg.get(CONF_MIN_HEATING_TIME, DEFAULT_MIN_HEATING_TIME))
        self._min_idle_time = int(cfg.get(CONF_MIN_IDLE_TIME, DEFAULT_MIN_IDLE_TIME))
        self._open_valve_temp = float(cfg.get(CONF_OPEN_VALVE_TEMP, DEFAULT_OPEN_VALVE_TEMP))
        self._close_valve_temp = float(cfg.get(CONF_CLOSE_VALVE_TEMP, DEFAULT_CLOSE_VALVE_TEMP))
        self._window_open_delay = int(cfg.get(CONF_WINDOW_OPEN_DELAY, cfg.get('window_delay', DEFAULT_WINDOW_OPEN_DELAY)))
        self._window_close_delay = int(cfg.get(CONF_WINDOW_CLOSE_DELAY, DEFAULT_WINDOW_CLOSE_DELAY))
        self._precision = float(cfg.get(CONF_PRECISION, DEFAULT_PRECISION))
        self._reaction_speed = cfg.get(CONF_REACTION_SPEED)
        if self._reaction_speed in REACTION_PRESETS:
            self._heat_delta, self._stop_delta = REACTION_PRESETS[self._reaction_speed]

        self._runtime = RuntimeState()
        self._sensor_temperature: float | None = None
        self._effective_temperature: float | None = None
        self._humidity: float | None = None
        self._trv_target_temperature: float | None = None
        self._cycle_lock_until: datetime | None = None
        self._unsubs: list[Any] = []

    @property
    def precision(self) -> float:
        return self._precision

    @property
    def min_temp(self) -> float:
        return self._min_temp

    @property
    def max_temp(self) -> float:
        return self._max_temp

    @property
    def target_temperature(self) -> float | None:
        return self._target_temperature

    @property
    def current_temperature(self) -> float | None:
        return self._effective_temperature

    @property
    def current_humidity(self) -> float | None:
        return self._humidity

    @property
    def hvac_mode(self) -> HVACMode:
        return self._runtime.hvac_mode

    @property
    def hvac_action(self) -> HVACAction:
        return self._runtime.hvac_action

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_CURRENT_SENSOR_TEMPERATURE: self._sensor_temperature,
            ATTR_EFFECTIVE_TEMPERATURE: self._effective_temperature,
            ATTR_CURRENT_HUMIDITY: self._humidity,
            ATTR_HEAT_REQUEST: self._runtime.heat_request,
            ATTR_LAST_DECISION: self._runtime.last_decision,
            ATTR_LAST_CHANGE: self._runtime.last_change.isoformat() if self._runtime.last_change else None,
            ATTR_WINDOW_OPEN: self._is_window_open(),
            ATTR_WINDOW_SINCE: self._runtime.window_since_open.isoformat() if self._runtime.window_since_open else None,
            ATTR_TRV_TARGET: self._trv_target_temperature,
            ATTR_CYCLE_LOCK_UNTIL: self._cycle_lock_until.isoformat() if self._cycle_lock_until else None,
            ATTR_BOILER_COORDINATED: bool(self._enable_boiler_coord and self._boiler_entity),
            ATTR_HEATING_SECONDS: self._runtime.heating_seconds,
            ATTR_IDLE_SECONDS: self._runtime.idle_seconds,
            "trv_entity": self._trv_entity,
            "sensor_entity": self._sensor_entity,
            "humidity_entity": self._humidity_entity,
            "window_entity": self._window_entity,
            "boiler_entity": self._boiler_entity,
            "heat_delta": self._heat_delta,
            "stop_delta": self._stop_delta,
            "sensor_offset": self._sensor_offset,
            "min_heating_time_s": self._min_heating_time,
            "min_idle_time_s": self._min_idle_time,
            "window_open_delay_s": self._window_open_delay,
            "window_close_delay_s": self._window_close_delay,
            "runtime_stats_enabled": self._enable_runtime_stats,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state == HVACMode.OFF:
                self._runtime.hvac_mode = HVACMode.OFF
                self._runtime.hvac_action = HVACAction.OFF
            if last_state.attributes.get("temperature") is not None:
                self._target_temperature = float(last_state.attributes["temperature"])
            self._runtime.heating_seconds = int(last_state.attributes.get(ATTR_HEATING_SECONDS, 0) or 0)
            self._runtime.idle_seconds = int(last_state.attributes.get(ATTR_IDLE_SECONDS, 0) or 0)

        self._update_cached_state()

        self._unsubs.append(
            async_track_state_change_event(
                self.hass,
                [e for e in [self._sensor_entity, self._humidity_entity, self._trv_entity, self._window_entity] if e],
                self._async_handle_dependency_change,
            )
        )
        self._unsubs.append(async_track_time_interval(self.hass, self._async_periodic_check, timedelta(minutes=1)))
        await self._async_control(force=True)

    async def async_will_remove_from_hass(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    @callback
    def _update_cached_state(self) -> None:
        sensor_state = self.hass.states.get(self._sensor_entity)
        self._sensor_temperature = _entity_temperature(sensor_state)
        self._effective_temperature = (
            round(self._sensor_temperature + self._sensor_offset, 2)
            if self._sensor_temperature is not None
            else None
        )
        humidity_state = self.hass.states.get(self._humidity_entity) if self._humidity_entity else None
        self._humidity = _entity_humidity(humidity_state)
        trv_state = self.hass.states.get(self._trv_entity)
        if trv_state is not None:
            trv_temp = trv_state.attributes.get("temperature")
            try:
                self._trv_target_temperature = float(trv_temp) if trv_temp is not None else None
            except (TypeError, ValueError):
                self._trv_target_temperature = None

        if self._window_entity:
            if self._is_window_open():
                if self._runtime.window_since_open is None:
                    self._runtime.window_since_open = dt_util.utcnow()
                self._runtime.window_since_closed = None
            else:
                if self._runtime.window_since_closed is None:
                    self._runtime.window_since_closed = dt_util.utcnow()
                self._runtime.window_since_open = None

    async def _async_handle_dependency_change(self, event) -> None:
        self._update_cached_state()
        await self._async_control()
        self.async_write_ha_state()

    async def _async_periodic_check(self, now: datetime) -> None:
        self._accumulate_runtime(now)
        self._update_cached_state()
        await self._async_control()
        self.async_write_ha_state()

    def _accumulate_runtime(self, now: datetime) -> None:
        if self._runtime.last_change is None:
            self._runtime.last_change = now
            return
        elapsed = int((now - self._runtime.last_change).total_seconds())
        if elapsed <= 0:
            return
        if self._runtime.heat_request:
            self._runtime.heating_seconds += elapsed
        else:
            self._runtime.idle_seconds += elapsed
        self._runtime.last_change = now

    def _is_window_open(self) -> bool:
        if not self._window_entity:
            return False
        state = self.hass.states.get(self._window_entity)
        return state is not None and state.state in {STATE_ON, STATE_OPEN}

    def _window_open_delay_elapsed(self) -> bool:
        return bool(
            self._runtime.window_since_open
            and (dt_util.utcnow() - self._runtime.window_since_open).total_seconds() >= self._window_open_delay
        )

    def _window_close_delay_elapsed(self) -> bool:
        if not self._window_entity or self._runtime.window_since_closed is None:
            return True
        return (dt_util.utcnow() - self._runtime.window_since_closed).total_seconds() >= self._window_close_delay

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temp := kwargs.get("temperature")) is None:
            return
        self._target_temperature = max(self._min_temp, min(self._max_temp, float(temp)))
        await self._async_control(force=True)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self._runtime.hvac_mode = hvac_mode
        if hvac_mode == HVACMode.OFF:
            self._runtime.hvac_action = HVACAction.OFF
            await self._async_apply_heat_request(False, "hvac_off", force=True)
        else:
            await self._async_control(force=True)
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def _async_control(self, force: bool = False) -> None:
        if self._runtime.hvac_mode == HVACMode.OFF:
            await self._async_apply_heat_request(False, "off_mode", force=force)
            return

        if self._effective_temperature is None:
            self._runtime.last_decision = "sensor_unavailable"
            return

        if self._is_window_open() and self._window_open_delay_elapsed():
            await self._async_apply_heat_request(False, "window_open", force=force)
            return

        if self._window_entity and (not self._is_window_open()) and not self._window_close_delay_elapsed():
            await self._async_apply_heat_request(False, "window_close_delay", force=force)
            return

        now = dt_util.utcnow()
        if not force and self._cycle_lock_until and now < self._cycle_lock_until:
            self._runtime.last_decision = "cycle_lock"
            return

        if not self._runtime.heat_request:
            should_heat = self._effective_temperature <= (self._target_temperature - self._heat_delta)
            await self._async_apply_heat_request(should_heat, "below_start_delta" if should_heat else "idle_band", force=force)
        else:
            should_stop = self._effective_temperature >= (self._target_temperature + self._stop_delta)
            await self._async_apply_heat_request(not should_stop, "above_stop_delta" if should_stop else "continue_heating", force=force)

    async def _async_apply_heat_request(self, new_state: bool, reason: str, force: bool = False) -> None:
        now = dt_util.utcnow()
        changed = new_state != self._runtime.heat_request

        if changed and not force and self._runtime.last_change:
            elapsed = (now - self._runtime.last_change).total_seconds()
            if self._runtime.heat_request and elapsed < self._min_heating_time:
                self._cycle_lock_until = self._runtime.last_change + timedelta(seconds=self._min_heating_time)
                self._runtime.last_decision = f"min_heating_time_active:{reason}"
                self._runtime.hvac_action = HVACAction.HEATING
                return
            if not self._runtime.heat_request and elapsed < self._min_idle_time:
                self._cycle_lock_until = self._runtime.last_change + timedelta(seconds=self._min_idle_time)
                self._runtime.last_decision = f"min_idle_time_active:{reason}"
                self._runtime.hvac_action = HVACAction.IDLE
                return

        self._runtime.last_decision = reason
        if changed or force:
            self._runtime.heat_request = new_state
            self._runtime.last_change = now
            self._cycle_lock_until = None
            await self._async_push_to_trv(new_state)
            await self._async_coordinate_boiler()

        self._runtime.hvac_action = HVACAction.HEATING if self._runtime.heat_request else HVACAction.IDLE

    async def _async_push_to_trv(self, heat_request: bool) -> None:
        target = self._open_valve_temp if heat_request else self._close_valve_temp
        service_data = {ATTR_ENTITY_ID: self._trv_entity, "temperature": target}
        await self.hass.services.async_call("climate", "set_temperature", service_data, blocking=True)
        self._trv_target_temperature = target

    async def _async_coordinate_boiler(self) -> None:
        if not (self._enable_boiler_coord and self._boiler_entity):
            return

        any_request = False
        for state in self.hass.states.async_all("climate"):
            if state.entity_id == self.entity_id:
                attrs = self.extra_state_attributes
            else:
                attrs = state.attributes
            if attrs.get(ATTR_HEAT_REQUEST):
                any_request = True
                break

        domain = self._boiler_entity.split(".", 1)[0]
        if domain in {"switch", "input_boolean"}:
            await self.hass.services.async_call(
                domain,
                "turn_on" if any_request else "turn_off",
                {ATTR_ENTITY_ID: self._boiler_entity},
                blocking=True,
            )
        elif domain == "climate":
            await self.hass.services.async_call(
                domain,
                "set_hvac_mode",
                {ATTR_ENTITY_ID: self._boiler_entity, "hvac_mode": HVACMode.HEAT if any_request else HVACMode.OFF},
                blocking=True,
            )


def _entity_temperature(state: State | None) -> float | None:
    if state is None:
        return None
    if state.entity_id.startswith("weather."):
        value = state.attributes.get("temperature")
    else:
        value = state.state
    return _to_float(value)


def _entity_humidity(state: State | None) -> float | None:
    if state is None:
        return None
    if state.entity_id.startswith("weather."):
        value = state.attributes.get("humidity")
    else:
        value = state.attributes.get("humidity")
        if value is None:
            value = state.state
    return _to_float(value)


def _to_float(value: Any) -> float | None:
    if value in {None, STATE_UNKNOWN, STATE_UNAVAILABLE}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
