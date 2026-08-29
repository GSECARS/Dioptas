# SPDX-License-Identifier: MIT

import json
from pathlib import Path
from typing import Any


class BeamlineConfig:
    CONFIG_PATH = Path.home() / '.Dioptas' / 'gsecars_config.json'

    PRESETS = {
        '13IDD': {
            'sample_position_x': '13IDD:m98',
            'sample_position_y': '13IDD:m97',
            'sample_position_z': '13IDD:m99',
            'pixel_size': 75,
            'condition_pvs': [
                {'pv': '13IDD:m103', 'limit': -175},
                {'pv': '13IDD:m102', 'limit': -175},
                {'pv': '13IDD:m67',  'limit': -130},
            ],
        },
        '13BMD': {
            'sample_position_x': '13BMD:m89',
            'sample_position_y': '13BMD:m90',
            'sample_position_z': '13BMD:m91',
            'pixel_size': 172,
            'condition_pvs': [
                {'pv': '13BMD:m68', 'limit': -50},
                {'pv': '13BMD:m65', 'limit': -50},
                {'pv': '13BMD:m43', 'limit': -10},
            ],
        },
    }

    def __init__(self):
        self._apply_preset_values('13IDD')
        self.beamline = '13IDD'
        self.load()

    def _apply_preset_values(self, name: str) -> None:
        preset = self.PRESETS[name]
        self.sample_position_x: str = preset['sample_position_x']
        self.sample_position_y: str = preset['sample_position_y']
        self.sample_position_z: str = preset['sample_position_z']
        self.pixel_size: int = preset['pixel_size']
        self.condition_pvs: list[dict[str, Any]] = [dict(p) for p in preset['condition_pvs']]

    def apply_preset(self, name: str) -> None:
        if name in self.PRESETS:
            self.beamline = name
            self._apply_preset_values(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            'beamline': self.beamline,
            'sample_position_x': self.sample_position_x,
            'sample_position_y': self.sample_position_y,
            'sample_position_z': self.sample_position_z,
            'pixel_size': self.pixel_size,
            'condition_pvs': self.condition_pvs,
        }

    def from_dict(self, d: dict[str, Any]) -> None:
        self.beamline = d.get('beamline', self.beamline)
        self.sample_position_x = d.get('sample_position_x', self.sample_position_x)
        self.sample_position_y = d.get('sample_position_y', self.sample_position_y)
        self.sample_position_z = d.get('sample_position_z', self.sample_position_z)
        self.pixel_size = d.get('pixel_size', self.pixel_size)
        self.condition_pvs = d.get('condition_pvs', self.condition_pvs)

    def save(self) -> None:
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_PATH, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def load(self) -> None:
        if self.CONFIG_PATH.exists():
            try:
                with open(self.CONFIG_PATH) as f:
                    self.from_dict(json.load(f))
            except (json.JSONDecodeError, KeyError, OSError):
                pass

    @property
    def epics_config(self) -> dict[str, str]:
        return {
            'sample_position_x': self.sample_position_x,
            'sample_position_y': self.sample_position_y,
            'sample_position_z': self.sample_position_z,
        }
