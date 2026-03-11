"""Constants for Smart TRV Thermostat."""
from __future__ import annotations

DOMAIN = "smart_trv_thermostat"
PLATFORMS = ["climate", "sensor"]

CONF_NAME = "name"
CONF_TRV_ENTITY = "trv_entity"
CONF_SENSOR_ENTITY = "sensor_entity"
CONF_HUMIDITY_ENTITY = "humidity_entity"
CONF_WINDOW_ENTITY = "window_entity"
CONF_BOILER_ENTITY = "boiler_entity"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TARGET_TEMP = "target_temp"
CONF_HEAT_DELTA = "heat_delta"
CONF_STOP_DELTA = "stop_delta"
CONF_SENSOR_OFFSET = "sensor_offset"
CONF_MIN_HEATING_TIME = "min_heating_time"
CONF_MIN_IDLE_TIME = "min_idle_time"
CONF_OPEN_VALVE_TEMP = "open_valve_temp"
CONF_CLOSE_VALVE_TEMP = "close_valve_temp"
CONF_WINDOW_OPEN_DELAY = "window_open_delay"
CONF_WINDOW_CLOSE_DELAY = "window_close_delay"
CONF_REACTION_SPEED = "reaction_speed"
CONF_PRECISION = "precision"
CONF_ENABLE_BOILER_COORD = "enable_boiler_coord"
CONF_BOILER_MODE = "boiler_mode"
CONF_ENABLE_RUNTIME_STATS = "enable_runtime_stats"

DEFAULT_MIN_TEMP = 16.0
DEFAULT_MAX_TEMP = 25.0
DEFAULT_TARGET_TEMP = 21.0
DEFAULT_HEAT_DELTA = 0.3
DEFAULT_STOP_DELTA = 0.2
DEFAULT_SENSOR_OFFSET = 0.0
DEFAULT_MIN_HEATING_TIME = 300
DEFAULT_MIN_IDLE_TIME = 300
DEFAULT_OPEN_VALVE_TEMP = 30.0
DEFAULT_CLOSE_VALVE_TEMP = 5.0
DEFAULT_WINDOW_OPEN_DELAY = 60
DEFAULT_WINDOW_CLOSE_DELAY = 300
DEFAULT_REACTION_SPEED = "normal"
DEFAULT_PRECISION = 0.1
DEFAULT_ENABLE_BOILER_COORD = False
DEFAULT_BOILER_MODE = "multi_room_coordinator"
DEFAULT_ENABLE_RUNTIME_STATS = False

REACTION_PRESETS: dict[str, tuple[float, float]] = {
    "slow": (0.5, 0.1),
    "normal": (DEFAULT_HEAT_DELTA, DEFAULT_STOP_DELTA),
    "fast": (0.2, 0.2),
}

ATTR_CURRENT_SENSOR_TEMPERATURE = "sensor_temperature"
ATTR_EFFECTIVE_TEMPERATURE = "effective_temperature"
ATTR_CURRENT_HUMIDITY = "humidity"
ATTR_HEAT_REQUEST = "heat_request"
ATTR_LAST_DECISION = "last_decision"
ATTR_LAST_CHANGE = "last_change"
ATTR_WINDOW_OPEN = "window_open"
ATTR_WINDOW_SINCE = "window_since"
ATTR_TRV_TARGET = "trv_target_temperature"
ATTR_CYCLE_LOCK_UNTIL = "cycle_lock_until"
ATTR_BOILER_COORDINATED = "boiler_coordinated"
ATTR_HEATING_SECONDS = "heating_seconds"
ATTR_IDLE_SECONDS = "idle_seconds"

SERVICE_REEVALUATE_ALL = "reevaluate_all"
