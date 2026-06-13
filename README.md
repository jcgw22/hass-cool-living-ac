# TCL · Cool Living · Comfee AC (IR) — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2026.4%2B-blue.svg)](https://www.home-assistant.io)
[![Version](https://img.shields.io/github/v/release/jcgw22/hass-cool-living-ac)](https://github.com/jcgw22/hass-cool-living-ac/releases)

Control any **TCL, Cool Living, or Comfee air conditioner** (and other TCL112AC-compatible units) from Home Assistant using any infrared emitter (e.g. an [ESPHome IR blaster](https://esphome.io/components/remote_transmitter.html)).

The integration sends full 14-byte TCL112AC frames over the Home Assistant `infrared` platform — no Wi-Fi dongle or cloud account required.

---

## Supported devices

Any AC unit that uses the **TCL112AC / Mitsubishi-112 Chinese OEM variant** IR protocol (14-byte frame, 38 kHz carrier, LSB-first, header `0x23 0xCB 0x26 0x01`). This protocol is shared across many OEM brands.

### Confirmed compatible

| Brand | Models / Series | Notes |
|-------|----------------|-------|
| **Cool Living** | All `CL-*` portables and window units (e.g. CL-10AEW, CL-12AEW, CL-WPS08XC1, CL-WPS10XC1, CL-WPS12XC1) | Primary target of this integration |
| **TCL** | Split and portable AC units using the TCL112AC remote | Protocol is named after this brand |
| **Comfee** (Midea OEM) | CF series portable ACs | Same 14-byte frame reported by users |
| **Olimpia Splendid** | Unico / Bi2 series (some variants) | OEM frame matches; verify with your remote |

### Likely compatible (same protocol, not yet confirmed)

These brands are known to ship units with TCL112AC-compatible remotes in some markets. They may work out of the box but have not been independently verified with this integration:

- **Beko** — portable AC units sold in Europe
- **Arçelik** — rebranded Beko units
- **Midea** — select portable / window models (non-Comfee line)
- **Sharp** — some OEM Chinese-market portables
- **Haier** — select portable models using the 14-byte TCL frame
- **Carrier** — Chinese-market OEM units with TCL112-compatible remotes
- **AUX** — portable and split units sold under the AUX or rebadged label
- **Hisense** — some portable models (verify header bytes match)

### How to check if your unit is compatible

Point the original remote at an IR receiver and capture a raw signal. If the decoded frame is 14 bytes with the header `23 CB 26 01`, your unit will work with this integration. Tools like [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266) or an ESPHome `remote_receiver` component can do this capture.

If your unit responds to the IR remote but is not listed, open an issue and share the model number so it can be added here.

---

## Features

| Feature | Supported |
|---------|-----------|
| HVAC modes | Cool, Heat, Dry, Fan Only, Off |
| Target temperature | 16 °C – 30 °C (0.5 °C steps) |
| Fan speeds | Auto, Low, Medium, High |
| Vertical swing | On / Off |
| Presets | None, Eco, Sleep |
| State restore on restart | Yes |
| Local control (no cloud) | Yes |

---

## Requirements

- Home Assistant **2026.4.0** or newer
- The built-in **`infrared`** integration enabled
- An **infrared emitter** entity — for example:
  - An [ESPHome IR blaster](https://esphome.io/components/remote_transmitter.html) added via the ESPHome integration
  - Any other emitter that exposes an entity on the `infrared` platform

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → ⋮ menu → **Custom repositories**.
2. Add `https://github.com/jcgw22/hass-cool-living-ac` as an **Integration**.
3. Search for **TCL Cool Living Comfee AC** and click **Download**.
4. Restart Home Assistant.

### Manual

1. Copy the `custom_components/tcl112ac_ir/` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **TCL Cool Living Comfee AC**.
3. Select the infrared emitter entity that is pointed at your unit.
4. A new **Climate** device will appear.

Each additional Cool Living unit needs its own emitter entity and its own integration entry.

---

## How it works

Every state change (mode, temperature, fan speed, swing, preset) immediately encodes a fresh full-state IR frame and fires it through the selected emitter. Because infrared is one-way there is no feedback from the unit; state is **assumed** and persisted across Home Assistant restarts via `RestoreEntity`.

---

## Contributing

Pull requests are welcome. Please open an issue first if you are adding support for a new device variant or protocol change.

---

## License

AGPL
