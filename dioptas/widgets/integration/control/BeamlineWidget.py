# SPDX-License-Identifier: MIT

from qtpy import QtWidgets

from ...CustomWidgets import LabelAlignRight, VerticalSpacerItem


class BeamlineWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._create_widgets()
        self._create_layout()
        self._style_widgets()
        self._set_tooltips()

    def _create_widgets(self):
        self.preset_cb = QtWidgets.QComboBox()
        self.preset_cb.addItems(['13IDD', '13BMD', 'Custom'])

        self.hor_pv_txt = QtWidgets.QLineEdit()
        self.ver_pv_txt = QtWidgets.QLineEdit()
        self.focus_pv_txt = QtWidgets.QLineEdit()

        self.pixel_size_sb = QtWidgets.QSpinBox()

        self.cond_pv_txts = [QtWidgets.QLineEdit() for _ in range(3)]
        self.cond_limit_sbs = [QtWidgets.QSpinBox() for _ in range(3)]

        self.save_btn = QtWidgets.QPushButton('Save Config')

    def _create_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        preset_row = QtWidgets.QHBoxLayout()
        preset_row.addWidget(LabelAlignRight('Preset:'))
        preset_row.addWidget(self.preset_cb)
        layout.addLayout(preset_row)

        motors_gb = QtWidgets.QGroupBox('Stage Motors')
        motors_grid = QtWidgets.QGridLayout()
        motors_grid.setContentsMargins(5, 8, 5, 5)
        motors_grid.setSpacing(5)
        motors_grid.addWidget(LabelAlignRight('Hor (X):'), 0, 0)
        motors_grid.addWidget(self.hor_pv_txt, 0, 1)
        motors_grid.addWidget(LabelAlignRight('Ver (Y):'), 1, 0)
        motors_grid.addWidget(self.ver_pv_txt, 1, 1)
        motors_grid.addWidget(LabelAlignRight('Focus (Z):'), 2, 0)
        motors_grid.addWidget(self.focus_pv_txt, 2, 1)
        motors_gb.setLayout(motors_grid)
        layout.addWidget(motors_gb)

        detector_gb = QtWidgets.QGroupBox('Detector')
        detector_row = QtWidgets.QHBoxLayout()
        detector_row.setContentsMargins(5, 8, 5, 5)
        detector_row.addWidget(LabelAlignRight('Pixel size:'))
        detector_row.addWidget(self.pixel_size_sb)
        detector_row.addStretch()
        detector_gb.setLayout(detector_row)
        layout.addWidget(detector_gb)

        cond_gb = QtWidgets.QGroupBox('Safety Condition PVs')
        cond_grid = QtWidgets.QGridLayout()
        cond_grid.setContentsMargins(5, 8, 5, 5)
        cond_grid.setSpacing(5)
        for i in range(3):
            cond_grid.addWidget(LabelAlignRight(f'PV {i + 1}:'), i, 0)
            cond_grid.addWidget(self.cond_pv_txts[i], i, 1)
            cond_grid.addWidget(LabelAlignRight('<='), i, 2)
            cond_grid.addWidget(self.cond_limit_sbs[i], i, 3)
        cond_gb.setLayout(cond_grid)
        layout.addWidget(cond_gb)

        layout.addWidget(self.save_btn)
        layout.addSpacerItem(VerticalSpacerItem())
        self.setLayout(layout)

    def _style_widgets(self):
        self.pixel_size_sb.setRange(1, 10000)
        self.pixel_size_sb.setSuffix(' um')
        for sb in self.cond_limit_sbs:
            sb.setRange(-100000, 100000)

    def _set_tooltips(self):
        self.preset_cb.setToolTip('Select a beamline preset to auto-fill all fields')
        self.pixel_size_sb.setToolTip('Default detector pixel size applied to new calibrations')
        for sb in self.cond_limit_sbs:
            sb.setToolTip('Motor must be at or below this value for stage rotation to be allowed')
        self.save_btn.setToolTip('Save configuration to ~/.Dioptas/gsecars_config.json')
