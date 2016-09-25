"""
Support for Netatmo thermostat.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/thermostat.netatmo/
"""
import logging
# import socket

from datetime import timedelta
# from urllib.error import HTTPError
import requests
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.components.climate import (STATE_HEAT, STATE_IDLE, ClimateDevice)
from homeassistant.util import Throttle
from homeassistant.loader import get_component

DEPENDENCIES = ['netatmo']

REQUIREMENTS = [
    'https://github.com/jabesq/netatmo-api-python/archive/'
    'v0.5.0.zip#lnetatmo==0.5.0']

_LOGGER = logging.getLogger(__name__)

CONF_STATION = 'station'
ATTR_MODULE = 'module'

CONF_SECRET_KEY = 'secret_key'
# DOMAIN = "netatmo"

# Return cached results if last scan was less then this time ago
# NetAtmo Data is uploaded to server every 10mn
# so this time should not be under
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the NetAtmo Thermostat."""
    import lnetatmo

    netatmo = get_component('netatmo')
    device = config.get(CONF_STATION, None)
    data = NetAtmoData(netatmo.NETATMO_AUTH)

    for module_name in data.get_module_names():
        if ATTR_MODULE in config:
            if module_name not in config[ATTR_MODULE]:
                continue
    add_devices([NetatmoThermostat(data, module_name)])

class NetatmoThermostat(ClimateDevice):
    """Representation a Netatmo thermostat."""

    def __init__(self, data, module_name):
        """Initialize the sensor."""
        super(NetatmoThermostat, self).__init__()
        self._data = data
        self._state = None
        self._module_name = module_name
        self._target_temperature = None
        self._current_temperature = None
        self._current_operation = STATE_IDLE
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._module_name

    @property
    def state(self):
        """Return the state of the device."""
        return self._data.thermostatdata.temp

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._data.thermostatdata.temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.is_away_mode_on:
            temp = self._data.thermostatdata.setpoint_temp
        else:
            temp = self._data.thermostatdata.setpoint_temp
        return temp

    @property
    def current_operation(self):
        """Return the current state of the thermostat."""
        state = self._data.thermostatdata.relay_cmd
        if state == 0:
            return STATE_IDLE
        elif state == 100:
            return STATE_HEAT

    @property
    def is_away_mode_on(self):
        """Return true if away mode is on."""
        # return self._away
        return 'away' in self._data.thermostatdata.setpoint_mode

    def turn_away_mode_on(self):
        """Turn away on."""
        # self._away = True
        mode = "away"
        temp = None
        self._data.thermostatdata.setthermpoint(mode, temp)
        self.update_ha_state()

    def turn_away_mode_off(self):
        """Turn away off."""
        # self._away = False
        mode = "program"
        temp = None
        self._data.thermostatdata.setthermpoint(mode, temp)
        self.update_ha_state()


    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        mode ="manual"
        self._data.thermostatdata.setthermpoint(mode, temperature)
        self.update_ha_state()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from NetAtmo API and updates the states."""
        # import tnetatmo
        # # self.auth = auth
        # self.data = tnetatmo.Thermos(authorization)
        self._data.update()

class NetAtmoData(object):
    """Get the latest data from NetAtmo."""

    def __init__(self, auth, device=None):
        """Initialize the data object."""
        self.auth = auth
        self.thermostatdata = None
        self.module_names = []
        self.device = device
        self.update()

    def get_module_names(self):
        """Return all module available on the API as a list."""
        self.update()
        # return self.thermostatdata.default_module
        if not self.device:
            for device in self.thermostatdata.modules.keys():
                for module in self.thermostatdata.modules[device].values():
                    self.module_names.append(module['module_name'])
        else:
            for module in self.thermostatdata.modules[self.device].values():
                self.module_names.append[module['module_name']]
        return self.module_names


    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Call the NetAtmo API to update the data."""
        import lnetatmo
        self.update()
        self.thermostatdata = lnetatmo.ThermostatData(self.auth)
