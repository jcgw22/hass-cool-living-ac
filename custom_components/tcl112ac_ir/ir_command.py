"""IR command wrapper for Cool Living AC.

Converts a 14-byte protocol frame into the signed-µs timing list
required by infrared_protocols.commands.Command.

Timing constants derived from Broadlink RM4 Pro captures.
Carrier: 38 kHz  (1 tick ≈ 26.3 µs)
"""

from __future__ import annotations

from infrared_protocols.commands import Command

# Timing in microseconds (verified against captured codes)
_PREAMBLE_MARK_US: int = 3077   # 117 ticks × 26.3 µs
_PREAMBLE_SPACE_US: int = 1526  # 58 ticks  × 26.3 µs
_BIT_MARK_US: int = 421         # 16 ticks  × 26.3 µs
_SPACE_ONE_US: int = 1184       # 45 ticks  × 26.3 µs
_SPACE_ZERO_US: int = 395       # 15 ticks  × 26.3 µs

_MODULATION: int = 38000        # 38 kHz carrier


class CoolLivingACCommand(Command):
    """IR command for Cool Living AC (TCL112AC protocol, 112-bit, LSB-first)."""

    def __init__(self, frame: list[int]) -> None:
        """Initialise with a 14-byte frame from protocol.encode()."""
        super().__init__(modulation=_MODULATION)
        self._frame = frame

    def get_raw_timings(self) -> list[int]:
        """Return signed µs timing list.

        Positive values = mark (carrier on).
        Negative values = space (carrier off).
        """
        timings: list[int] = [_PREAMBLE_MARK_US, -_PREAMBLE_SPACE_US]

        for byte_val in self._frame:
            for bit in range(8):  # LSB-first
                timings.append(_BIT_MARK_US)
                if (byte_val >> bit) & 1:
                    timings.append(-_SPACE_ONE_US)
                else:
                    timings.append(-_SPACE_ZERO_US)

        timings.append(_BIT_MARK_US)  # trailing mark (end of frame)
        return timings
