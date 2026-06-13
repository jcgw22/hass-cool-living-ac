"""Climate entity for Cool Living AC."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PRESET_NONE,
    SWING_OFF,
    SWING_ON,
)
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_INFRARED_ENTITY_ID, DOMAIN, MAX_TEMP_C, MIN_TEMP_C, PRESET_ECO, PRESET_SLEEP
from .ir_command import CoolLivingACCommand
from .protocol import encode

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1

_MODE_TO_PROTOCOL: dict[HVACMode, str] = {
    HVACMode.COOL:     "cool",
    HVACMode.HEAT:     "heat",
    HVACMode.DRY:      "dry",
    HVACMode.FAN_ONLY: "fan_only",
}

_FAN_TO_PROTOCOL: dict[str, str] = {
    FAN_AUTO:   "auto",
    FAN_LOW:    "low",
    FAN_MEDIUM: "medium",
    FAN_HIGH:   "high",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up climate entity from a config entry."""
    async_add_entities([CoolLivingACClimate(entry)])


class CoolLivingACClimate(InfraredEmitterConsumerEntity, RestoreEntity, ClimateEntity):
    """Climate entity for Cool Living AC via the infrared platform.

    Sends full-state TCL112AC frames (14 bytes, LSB-first, 38 kHz)
    through whichever infrared emitter is selected during setup.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = True
    _attr_should_poll = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    _attr_min_temp = float(MIN_TEMP_C)
    _attr_max_temp = float(MAX_TEMP_C)
    _attr_target_temperature_step = 0.5

    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_swing_modes = [SWING_OFF, SWING_ON]
    _attr_preset_modes = [PRESET_NONE, PRESET_ECO, PRESET_SLEEP]

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialise the climate entity."""
        self._infrared_emitter_entity_id: str = entry.data[CONF_INFRARED_ENTITY_ID]
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="AC (TCL112)",
            manufacturer="TCL / Cool Living / Comfee",
            model="TCL112AC (IR)",
        )

        # Default assumed state
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_target_temperature = 24.0
        self._attr_fan_mode = FAN_AUTO
        self._attr_swing_mode = SWING_OFF
        self._attr_preset_mode = PRESET_NONE

    async def async_added_to_hass(self) -> None:
        """Restore last known state on startup and register emitter tracking."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if last_state.state in [m.value for m in self._attr_hvac_modes]:
            self._attr_hvac_mode = HVACMode(last_state.state)
        attrs = last_state.attributes
        if (temp := attrs.get("temperature")) is not None:
            self._attr_target_temperature = float(temp)
        if (fan := attrs.get("fan_mode")) is not None:
            self._attr_fan_mode = fan
        if (swing := attrs.get("swing_mode")) is not None:
            self._attr_swing_mode = swing
        if (preset := attrs.get("preset_mode")) is not None:
            self._attr_preset_mode = preset

    async def _send_ir(self, *, power: bool = True) -> None:
        """Encode current state and send via the infrared platform."""
        is_sleep = self._attr_preset_mode == PRESET_SLEEP
        mode = "sleep" if is_sleep else _MODE_TO_PROTOCOL.get(
            self._attr_hvac_mode, "cool"
        )
        fan = _FAN_TO_PROTOCOL.get(self._attr_fan_mode, "auto")
        swing_on = self._attr_swing_mode == SWING_ON

        _LOGGER.debug(
            "Sending IR: emitter=%s mode=%s temp=%s fan=%s swing=%s power=%s",
            self._infrared_emitter_entity_id,
            mode, self._attr_target_temperature, fan, swing_on, power,
        )

        frame = encode(
            mode=mode,
            temp_c=self._attr_target_temperature,
            fan=fan,
            swing_v="auto" if swing_on else "middle",
            swing_h=False,
            power=power,
            eco=(self._attr_preset_mode == PRESET_ECO),
        )
        _LOGGER.debug("IR frame: %s", [f"0x{b:02X}" for b in frame])
        await self._send_command(CoolLivingACCommand(frame))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self._send_ir(power=False)
            self._attr_hvac_mode = HVACMode.OFF
            self.async_write_ha_state()
            return

        was_off = self._attr_hvac_mode == HVACMode.OFF
        self._attr_hvac_mode = hvac_mode
        if was_off:
            self._attr_preset_mode = PRESET_NONE
        await self._send_ir(power=True)
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        if (temp := kwargs.get("temperature")) is not None:
            self._attr_target_temperature = float(temp)
            if self._attr_hvac_mode != HVACMode.OFF:
                await self._send_ir()
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan speed."""
        self._attr_fan_mode = fan_mode
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._send_ir()
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set vertical swing."""
        self._attr_swing_mode = swing_mode
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._send_ir()
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset (none / sleep)."""
        self._attr_preset_mode = preset_mode
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._send_ir()
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn on (restore last active mode)."""
        if self._attr_hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = HVACMode.COOL
        await self._send_ir(power=True)
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn off."""
        await self._send_ir(power=False)
        self._attr_hvac_mode = HVACMode.OFF
        self.async_write_ha_state()
