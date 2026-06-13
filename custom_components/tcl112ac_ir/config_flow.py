"""Config flow for Cool Living AC integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import infrared
from homeassistant.components.infrared import DOMAIN as INFRARED_DOMAIN
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import CONF_INFRARED_ENTITY_ID, DOMAIN


class CoolLivingACConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cool Living AC."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the user step — select an infrared emitter entity."""
        errors: dict[str, str] = {}

        if not infrared.async_get_emitters(self.hass):
            return self.async_abort(reason="no_emitters")

        if user_input is not None:
            entity_id = user_input[CONF_INFRARED_ENTITY_ID]
            await self.async_set_unique_id(f"tcl112ac_ir_{entity_id}")
            self._abort_if_unique_id_configured()

            ent_reg = er.async_get(self.hass)
            entry = ent_reg.async_get(entity_id)
            entity_name = (
                entry.name or entry.original_name or entity_id
                if entry
                else entity_id
            )
            return self.async_create_entry(
                title=f"TCL · Cool Living · Comfee AC ({entity_name})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INFRARED_ENTITY_ID): EntitySelector(
                        EntitySelectorConfig(
                            domain=INFRARED_DOMAIN,
                            device_class="emitter",
                        )
                    ),
                }
            ),
            errors=errors,
        )
