# Nixwrap

Unified Python SDK for Rocket League: save file data extraction, Stats API WebSocket client, tracker.gg stats, process detection, keyboard/controller input, and a reusable GUI/overlay toolkit.

```bash
# Local install (dev):
pip install ./nixwrap/
# or editable:
pip install -e ./nixwrap/

# With optional extras:
pip install "./nixwrap/[tracker]"   # tracker.gg anti-bot
pip install "./nixwrap/[gui]"       # overlay / GUI
pip install "./nixwrap/[input]"     # keyboard + controller
pip install "./nixwrap/[all]"       # everything

```

## Modules

| Module | Purpose | Requires |
|--------|---------|----------|
| `nixwrap.save_file` | Decrypt + extract data from `.save` files | `pycryptodome` |
| `nixwrap.process` | Detect running RL (Steam vs Epic) | `psutil` |
| `nixwrap.stats` | Live Stats API WebSocket events | - |
| `nixwrap.tracker` | tracker.gg player rank/stats | `curl-cffi` (optional) |
| `nixwrap.input` | Keyboard, Xbox, DualSense hotkey detection | `dualsense-controller`, `keyboard` (optional) |
| `nixwrap.gui` | Overlay/GUI toolkit | `PySide6` (optional) |
| `nixwrap.utils` | Constants and helpers | - |

---

## Quick Start

### 1. Save File Data Extraction

```python
from nixwrap.save_file import load, find_save_file

# Auto-find the active save file
path = find_save_file()
save = load(path)

# Camera
print(save.camera.fov)           # 110.0
print(save.camera.stiffness)     # 0.55

# Controls (keyboard + gamepad)
print(save.controls.jump)                    # "SpaceBar"
print(save.gamepad_bindings.boost)           # "XboxTypeS_RightShoulder"

# Raw bindings for custom inspection
for b in save.gamepad_bindings.raw_bindings:
    print(f"  {b['Action']} -> {b['Key']}")

# Stats
print(save.stats.wins)           # 1234
print(save.xp.level)             # 27
print(save.xp.total_xp)          # 348223

# Skill data per playlist
for pid, skill in save.skills.items():
    print(f"Playlist {pid}: matches={skill.matches_played}, tier={skill.tier}")

# Inventory
for item in save.inventory:
    print(f"Product {item.product_id} (series {item.series_id})")

# Settings
print(save.video.res_width, save.video.res_height)
print(save.gameplay.controller_deadzone)
print(save.sound.master_volume)

# Quick chats, loadout sets, season, achievements, etc.
print(len(save.quick_chats), "quick chat bindings")
print(len(save.loadout_sets), "loadout presets")
```

### 2. Process Detection

```python
from nixwrap.process import find_rocket_league, is_rocket_league_focused

rl = find_rocket_league()
if rl:
    print(f"PID: {rl.pid}")
    print(f"Platform: {rl.platform.value}")      # steam or epic
    print(f"Root dir: {rl.root_dir}")
    print(f"Save path: {rl.save_data_path}")

if is_rocket_league_focused():
    print("RL window has focus")
```

### 3. Input Detection (Keyboard + Controller)

```python
from nixwrap.input import (
    is_hotkey_pressed, is_key_pressed,
    get_xinput_state, XINPUT_A,
    setup_dualsense, start_dualsense_monitor,
    get_button_display,
)

# Keyboard
if is_key_pressed("tab"):
    print("Tab is held")

# XInput (Xbox / DS4 via DS4Windows)
state = get_xinput_state()
if state and state.is_pressed(XINPUT_A):
    print("A button pressed")

# DualSense (PS5)
controller = setup_dualsense()       # auto-finds bundled hidapi.dll
start_dualsense_monitor()            # background auto-reconnect

# Unified hotkey check (InGameRank-compatible config format)
config = {"is_controller": True, "controller_type": "xinput",
          "controller_button": XINPUT_A}
if is_hotkey_pressed(config):
    print("Hotkey held!")

# Button display names
print(get_button_display("xinput", XINPUT_A))           # "A"
print(get_button_display("dualsense", 0))               # "Cross"
```

### 4. Stats API (Live Events)

```python
from nixwrap.stats import StatsClient

client = StatsClient()

# Callback mode
client.on("GoalScored", lambda evt: print(f"GOAL! {evt.scorer.name}"))
client.on("StatfeedEvent", lambda evt: print(f"{evt.main_target.name}: {evt.stat_type}"))
client.on_event(lambda evt: print(f"[{evt.event_type}]"))

with client:
    import time
    time.sleep(300)  # listen for 5 minutes
```

**Async mode:**

```python
import asyncio
from nixwrap.stats import StatsClient

async def main():
    client = StatsClient()
    client.start()
    async for event in client.events():
        print(event.event_type)
        if event.event_type == "GoalScored":
            print(f"  {event.scorer.name} scored!")

asyncio.run(main())
```

### 5. Tracker API (Player Ranks)

```python
from nixwrap.tracker import TrackerClient

client = TrackerClient()  # random browser fingerprint per request
stats = client.fetch("Steam|123456789|0", "PlayerName")

if stats.error:
    print(f"Error: {stats.error}")
else:
    print(f"Last updated: {stats.last_updated}")
    print(f"Lifetime: {stats.lifetime.wins} wins, {stats.lifetime.goals} goals")
    for pid, rank in stats.ranks.items():
        print(f"  {rank.playlist_name}: {rank.tier_name} {rank.division_name} "
              f"({rank.mmr} MMR, #{rank.rank_percentile}%)")
        if rank.win_streak:
            direction = "^" if rank.win_streak_type == "win" else "v"
            print(f"    Streak: {direction}{rank.win_streak}")
```

Results are cached for 5 minutes (tracker.gg update interval).

### 6. GUI / Overlay

```python
from PySide6.QtWidgets import QApplication
from nixwrap.gui import (
    create_overlay, WindowConfig, WindowType,
    Painter, Color, THEME_DARK, FadeAnimation,
)

class MyOverlay:
    def __init__(self):
        self.win = create_overlay(600, 200, corner_radius=12, opacity=0.95)
        self.win._paint = self._paint
        self.win.snap_to_bottom_center(margin=20)

    def _paint(self, painter_q):
        p = Painter(painter_q)
        p.fill_rect(0, 0, 600, 200,
                     THEME_DARK.background.with_alpha(216), radius=12)
        p.stroke_rect(0, 0, 599, 199,
                       THEME_DARK.divider, width=1, radius=12)
        p.draw_text("Hello Rocket League!", 20, 40,
                     color=THEME_DARK.text_primary)

app = QApplication([])
overlay = MyOverlay()
app.exec()
```

---

## Optional Dependencies

| Extra | Packages | What you get |
|-------|----------|-------------|
| `[tracker]` | `curl-cffi` | Browser impersonation for tracker.gg anti-bot |
| `[gui]` | `PySide6` | Overlay windows, painter, colors, fonts, animations |
| `[input]` | `dualsense-controller`, `keyboard`, bundled `hidapi.dll` | Xbox (XInput), PS5 DualSense, keyboard hotkey detection |
| `[all]` | all of the above | Everything |

---

## Requirements

- **Python** >= 3.10
- **pycryptodome** >= 3.18 (save file AES)
- **psutil** >= 5.9 (process detection)


---

## Acknowledgements

- [RocketRP](https://github.com/Drogebot/RocketRP): AES key and binary format research
- [tracker.gg](https://tracker.gg/): player stats API
- Rocket League Stats API: [Psyonix/Epic](https://www.rocketleague.com/en/developer/stats-api)
