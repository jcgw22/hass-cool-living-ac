"""Constants for the TCL · Cool Living · Comfee AC (IR) integration."""

from __future__ import annotations

DOMAIN = "tcl112ac_ir"
CONF_INFRARED_ENTITY_ID = "infrared_entity_id"

MIN_TEMP_C: int = 16
MAX_TEMP_C: int = 30

# Preset modes
PRESET_SLEEP: str = "sleep"
PRESET_ECO: str = "eco"
