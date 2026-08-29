# SPDX-License-Identifier: MIT

from qtpy import QtWidgets, QtCore

from .CustomWidgets import LabelAlignRight, VerticalSpacerItem


class BeamlineWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Beamline Configuration")

        self._condition_rows: list = []

        self._create_widgets()
        self._create_layout()
        self._style_widgets()
        self._set_tooltips()

        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_MacAlwaysShowToolWindow)

    def _create_widgets(self):
        self.preset_cb = QtWidgets.QComboBox()
        self.preset_cb.addItems(['13IDD', '13BMD', 'Custom'])

        self.hor_pv_txt = QtWidgets.QLineEdit()
        self.ver_pv_txt = QtWidgets.QLineEdit()
        self.focus_pv_txt = QtWidgets.QLineEdit()

        self.pixel_size_sb = QtWidgets.QSpinBox()

        self.add_cond_btn = QtWidgets.QPushButton('+ Add condition')
        self.add_cond_btn.clicked.connect(lambda: self.add_condition_row())

        self.save_btn = QtWidgets.QPushButton('Save Config')
        self.connect_epics_btn = QtWidgets.QPushButton('Connect EPICS')

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
        cond_outer = QtWidgets.QVBoxLayout()
        cond_outer.setContentsMargins(5, 8, 5, 5)
        cond_outer.setSpacing(4)

        self._cond_scroll = QtWidgets.QScrollArea()
        self._cond_scroll.setWidgetResizable(True)
        self._cond_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        cond_container = QtWidgets.QWidget()
        self._cond_rows_layout = QtWidgets.QVBoxLayout(cond_container)
        self._cond_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._cond_rows_layout.setSpacing(3)
        self._cond_rows_layout.setAlignment(QtCore.Qt.AlignTop)
        self._cond_scroll.setWidget(cond_container)

        cond_outer.addWidget(self._cond_scroll)
        cond_outer.addWidget(self.add_cond_btn)
        cond_gb.setLayout(cond_outer)
        layout.addWidget(cond_gb)

        action_row = QtWidgets.QHBoxLayout()
        action_row.addWidget(self.save_btn)
        action_row.addWidget(self.connect_epics_btn)
        layout.addLayout(action_row)
        layout.addSpacerItem(VerticalSpacerItem())
        self.setLayout(layout)

    def _style_widgets(self):
        self.pixel_size_sb.setRange(1, 10000)
        self.pixel_size_sb.setSuffix(' um')
        self._cond_scroll.setFixedHeight(120)

    def _set_tooltips(self):
        self.preset_cb.setToolTip('Select a beamline preset to auto-fill all fields')
        self.pixel_size_sb.setToolTip('Default detector pixel size applied to new calibrations')
        self.add_cond_btn.setToolTip('Add a safety condition PV row')
        self.save_btn.setToolTip('Save configuration to ~/.Dioptas/gsecars_config.json')

    def add_condition_row(self, pv: str = '', limit: int = 0):
        """Append a condition row to the list."""
        row = QtWidgets.QWidget()
        row_layout = QtWidgets.QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        pv_txt = QtWidgets.QLineEdit(pv)
        limit_sb = QtWidgets.QSpinBox()
        limit_sb.setRange(-100000, 100000)
        limit_sb.setValue(limit)
        remove_btn = QtWidgets.QPushButton('×')
        remove_btn.setFixedWidth(22)
        remove_btn.setFixedHeight(22)

        row_layout.addWidget(pv_txt)
        row_layout.addWidget(LabelAlignRight('≤'))
        row_layout.addWidget(limit_sb)
        row_layout.addWidget(remove_btn)

        entry = {'widget': row, 'pv_txt': pv_txt, 'limit_sb': limit_sb}
        self._condition_rows.append(entry)
        self._cond_rows_layout.addWidget(row)

        remove_btn.clicked.connect(lambda: self._remove_condition_row(entry))

    def _remove_condition_row(self, entry: dict):
        if entry in self._condition_rows:
            self._condition_rows.remove(entry)
            entry['widget'].deleteLater()

    def clear_condition_rows(self):
        """Remove all condition rows."""
        for entry in list(self._condition_rows):
            self._remove_condition_row(entry)

    @property
    def condition_rows(self) -> list:
        """Return current condition rows as a list of {'pv', 'limit'} dicts."""
        return [
            {'pv': e['pv_txt'].text(), 'limit': e['limit_sb'].value()}
            for e in self._condition_rows
        ]

    def raise_widget(self):
        self.show()
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.activateWindow()
        self.raise_()
