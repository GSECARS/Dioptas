# SPDX-License-Identifier: MIT

# imports for type hinting in PyCharm -- DO NOT DELETE
from ...widgets.BeamlineWidget import BeamlineWidget
from ...widgets.CalibrationWidget import CalibrationWidget
from .EpicsController import EpicsController
from ...model.BeamlineConfig import BeamlineConfig


class BeamlineController:
    """
    Manages the beamline configuration floating window.
    Applies saved EPICS motor PVs, detector pixel size, and safety condition PVs
    on startup and whenever the user saves a new configuration.
    """

    def __init__(
        self,
        beamline_widget: BeamlineWidget,
        calibration_widget: CalibrationWidget,
        epics_controller: EpicsController,
        beamline_config: BeamlineConfig,
    ):
        """
        :param beamline_widget: Reference to the BeamlineWidget floating window
        :param calibration_widget: Reference to the CalibrationWidget
        :param epics_controller: Reference to the EpicsController
        :param beamline_config: Reference to the BeamlineConfig model

        :type beamline_widget: BeamlineWidget
        :type calibration_widget: CalibrationWidget
        :type epics_controller: EpicsController
        :type beamline_config: BeamlineConfig
        """
        self.widget = beamline_widget
        self.calibration_widget = calibration_widget
        self.epics_controller = epics_controller
        self.beamline_config = beamline_config

        self._populate_widget()
        self._apply_config()
        self._connect_signals()

    def _connect_signals(self):
        self.widget.preset_cb.currentTextChanged.connect(self._on_preset_changed)
        self.widget.save_btn.clicked.connect(self._save_config)
        self.widget.connect_epics_btn.clicked.connect(self.epics_controller.update_current_motor_position)

    def _on_preset_changed(self, name: str):
        if name != 'Custom':
            self.beamline_config.apply_preset(name)
            self._populate_widget()

    def _populate_widget(self):
        config = self.beamline_config
        self.widget.preset_cb.blockSignals(True)
        if config.beamline in config.PRESETS:
            self.widget.preset_cb.setCurrentText(config.beamline)
        else:
            self.widget.preset_cb.setCurrentText('Custom')
        self.widget.preset_cb.blockSignals(False)

        self.widget.hor_pv_txt.setText(config.sample_position_x)
        self.widget.ver_pv_txt.setText(config.sample_position_y)
        self.widget.focus_pv_txt.setText(config.sample_position_z)
        self.widget.pixel_size_sb.setValue(config.pixel_size)

        self.widget.clear_condition_rows()
        for cond in config.condition_pvs:
            self.widget.add_condition_row(cond['pv'], cond['limit'])

    def _apply_config(self):
        self.epics_controller.load_config(self.beamline_config)
        size_m = self.beamline_config.pixel_size * 1e-6
        self.calibration_widget.set_pixel_size(size_m, size_m)

    def _save_config(self):
        config = self.beamline_config
        config.beamline = self.widget.preset_cb.currentText()
        config.sample_position_x = self.widget.hor_pv_txt.text()
        config.sample_position_y = self.widget.ver_pv_txt.text()
        config.sample_position_z = self.widget.focus_pv_txt.text()
        config.pixel_size = self.widget.pixel_size_sb.value()
        config.condition_pvs = self.widget.condition_rows
        config.save()
        self._apply_config()
