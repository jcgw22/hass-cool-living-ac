"""Cool Living AC IR protocol encoder.

Protocol: TCL112AC / Mitsubishi-112 Chinese OEM variant.
14-byte full-state frame, 38 kHz carrier, LSB-first.

Frame layout:
  B0-B5  : Fixed header [0x23, 0xCB, 0x26, 0x01, 0x00, CTRL]
  B6     : Mode
  B7     : Temperature  (31 - floor(T_celsius))
  B8     : (SwingV[5:3] | Fan[2:0])
  B9-B11 : Zeroes
  B12    : bit5=HalfDegree (0.5°C), bit3=SwingH
  B13    : Checksum = sum(B0..B12) mod 256

Reference: ir_Tcl.h / ir_Tcl.cpp in crankyoldgit/IRremoteESP8266
           isTcl=0 variant (Mitsubishi-112 sub-type, same protocol).
"""

from __future__ import annotations

# Byte 5 control flags
_CTRL_POWER_ON: int = 0x24   # Power=1 (bit5), Light=1 (bit2)
_CTRL_POWER_OFF: int = 0x04  # Power=0, Light=1

# Byte 6 — mode
_MODE: dict[str, int] = {
    "cool":     0x03,
    "heat":     0x01,
    "dry":      0x02,
    "fan_only": 0x07,
    "sleep":    0x07,  # same mode byte as fan_only; differentiated by fan speed
}

# Byte 8 — fan speed (bits 2:0)
_FAN: dict[str, int] = {
    "auto":   0x00,
    "night":  0x01,  # min/quiet — used internally for sleep preset
    "low":    0x02,
    "medium": 0x03,
    "high":   0x05,
}

# Byte 8 — vertical swing (bits 5:3)
_SWING_V: dict[str, int] = {
    "off":     0x00,
    "highest": 0x01,
    "high":    0x02,
    "middle":  0x03,
    "low":     0x04,
    "lowest":  0x05,
    "auto":    0x07,
}

_TEMP_MAX: int = 31


def encode(
    mode: str,
    temp_c: float = 24.0,
    fan: str = "auto",
    swing_v: str = "middle",
    swing_h: bool = False,
    power: bool = True,
    eco: bool = False,
) -> list[int]:
    """Encode AC state into a 14-byte IR frame.

    Args:
        mode:    Operating mode — "cool", "heat", "dry", "fan_only", "sleep".
        temp_c:  Target temperature in Celsius (16–30, 0.5° steps supported).
        fan:     Fan speed — "auto", "low", "medium", "high".
                 Overridden to "night" automatically when mode="sleep".
        swing_v: Vertical swing position — "off", "highest", "high", "middle",
                 "low", "lowest", "auto".
        swing_h: Horizontal swing on/off.
        power:   True = power on, False = power off frame.
        eco:     True = economy/eco mode (byte 5 bit 7).

    Returns:
        14-byte list ready to encode as IR pulses.
    """
    temp_c = max(16.0, min(30.0, temp_c))
    temp_int = int(temp_c)           # integer part
    half_degree = (temp_c % 1) >= 0.5

    ctrl = _CTRL_POWER_ON if power else _CTRL_POWER_OFF
    if eco and power:
        ctrl |= 0x80  # bit 7 = Econo
    mode_byte = _MODE.get(mode, _MODE["cool"])

    fan_key = "night" if mode == "sleep" else fan
    fan_val = _FAN.get(fan_key, _FAN["auto"])
    swing_v_val = _SWING_V.get(swing_v, _SWING_V["middle"])
    byte8 = (swing_v_val << 3) | fan_val

    byte12 = 0x00
    if half_degree:
        byte12 |= 0x20  # bit 5 = HalfDegree
    if swing_h:
        byte12 |= 0x08  # bit 3 = SwingH

    frame: list[int] = [
        0x23, 0xCB, 0x26, 0x01, 0x00, ctrl,  # B0-B5
        mode_byte,                             # B6
        _TEMP_MAX - temp_int,                  # B7  (integer part only)
        byte8,                                 # B8
        0x00, 0x00, 0x00,                      # B9-B11
        byte12,                                # B12
    ]
    frame.append(sum(frame) & 0xFF)            # B13 checksum
    return frame
