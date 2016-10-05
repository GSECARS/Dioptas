# -*- coding: utf-8 -*-

from ..utility import QtTest
from mock import MagicMock, patch

from ...model.DioptasModel import DioptasModel
from ...widgets.integration import IntegrationWidget
from ...controller.integration.EpicsController import EpicsController

from qtpy import QtWidgets

# mocking the functions which will block the unittest for some reason...
QtWidgets.QApplication.processEvents = MagicMock()
QtWidgets.QProgressDialog.setValue = MagicMock()


class TestEpicsController(QtTest):

    def setUp(self):
        self.integration_widget = IntegrationWidget()
        self.move_widget = self.integration_widget.move_widget
        self.setup_widget = self.integration_widget.move_widget.motors_setup_widget
        self.model = DioptasModel()
        self.epics_controller = EpicsController(self.integration_widget, self.model)

    @patch('epics.caget', return_value=12.03)
    def test_update_motor_position(self, caget):
        self.epics_controller.update_current_motor_position()

        self.assertEqual(self.move_widget.hor_lbl.text(), '12.03')
        self.assertEqual(self.move_widget.ver_lbl.text(), '12.03')
        self.assertEqual(self.move_widget.focus_lbl.text(), '12.03')
        self.assertEqual(self.move_widget.omega_lbl.text(), '12.03')

    def test_update_image_position(self):
        self.epics_controller.update_image_position()

        self.assertEqual(self.move_widget.img_hor_lbl.text(), '')
        self.assertEqual(self.move_widget.img_ver_lbl.text(), '')
        self.assertEqual(self.move_widget.img_focus_lbl.text(), '')
        self.assertEqual(self.move_widget.img_omega_lbl.text(), '')

        self.model.img_model.motors_info['Horizontal'] = 0.1
        self.model.img_model.motors_info['Vertical'] = 0.2
        self.model.img_model.motors_info['Focus'] = 0.3
        self.model.img_model.motors_info['Omega'] = 0.4

        self.epics_controller.update_image_position()
        self.assertEqual(str(self.move_widget.img_hor_lbl.text()), '0.100')
        self.assertEqual(str(self.move_widget.img_ver_lbl.text()), '0.200')
        self.assertEqual(str(self.move_widget.img_focus_lbl.text()), '0.300')
        self.assertEqual(str(self.move_widget.img_omega_lbl.text()), '0.400')

    @patch('epics.caput')
    @patch('epics.caget', return_value=0.0)
    def test_move_stage(self, caget, caput):
        self.model.img_model.motors_info['Horizontal'] = 0.1
        self.model.img_model.motors_info['Vertical'] = 0.02
        self.model.img_model.motors_info['Focus'] = 0.05
        self.model.img_model.motors_info['Omega'] = 90

        self.epics_controller.update_image_position()

        self.move_widget.move_hor_cb.setChecked(True)
        self.move_widget.move_ver_cb.setChecked(True)
        self.move_widget.move_focus_cb.setChecked(True)

        self.epics_controller.move_stage()

        caput.assert_any_call('13IDD:m81.VAL', 0.1)
        caput.assert_any_call('13IDD:m83.VAL', 0.02)
        caput.assert_any_call('13IDD:m82.VAL', 0.05)


if __name__ == '__main__':
    unittest.main()
