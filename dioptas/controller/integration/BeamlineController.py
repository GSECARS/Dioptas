# SPDX-License-Identifier: MIT

from ...widgets.integration import IntegrationWidget
from ...widgets.CalibrationWidget import CalibrationWidget
from .EpicsController import EpicsController
from ...model.BeamlineConfig import BeamlineConfig


class BeamlineController:
    """
    Manages the beamline configuration tab in the integration control panel.
    Applies saved EPICS motor PVs, detector pixel size, and safety condition PVs
    on startup and whenever the user saves a new configuration.
    """

    def __init__(
        self,
        integration_widget: IntegrationWidget,
        calibration_widget: CalibrationWidget,
        epics_controller: EpicsController,
        beamline_config: BeamlineConfig,
    ):
        """
        :param integration_widget: Reference to the IntegrationWidget
        :param calibration_widget: Reference to the CalibrationWidget
        :param epics_controller: Reference to the EpicsController
        :param beamline_config: Reference to the BeamlineConfig model

        :type integration_widget: IntegrationWidget
        :type calibration_widget: CalibrationWidget
        :type epics_controller: EpicsController
        :type beamline_config: BeamlineConfig
        """
        self.widget = integration_widget.integration_control_widget.beamline_widget
        self.calibration_widget = calibration_widget
        self.epics_controller = epics_controller
        self.beamline_config = beamline_config

        self._populate_widget()
        self._apply_config()
        self._connect_signals()

    def _connect_signals(self):
        self.widget.preset_cb.currentTextChanged.connect(self._on_preset_changed)
        self.widget.save_btn.clicked.connect(self._save_config)

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

        for i, cond in enumerate(config.condition_pvs[:3]):
            self.widget.cond_pv_txts[i].setText(cond['pv'])
            self.widget.cond_limit_sbs[i].setValue(cond['limit'])

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
        config.condition_pvs = [
            {'pv': self.widget.cond_pv_txts[i].text(),
             'limit': self.widget.cond_limit_sbs[i].value()}
            for i in range(3)
        ]
        config.save()
        self._apply_config()
