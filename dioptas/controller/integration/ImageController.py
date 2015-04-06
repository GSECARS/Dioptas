# -*- coding: utf8 -*-
# Dioptas - GUI program for fast processing of 2D X-ray data
# Copyright (C) 2014  Clemens Prescher (clemens.prescher@gmail.com)
# GSECARS, University of Chicago
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Clemens Prescher'
import os

from PyQt4 import QtGui, QtCore
import numpy as np
from PIL import Image

from model.Helper.ImgCorrection import CbnCorrection, ObliqueAngleDetectorAbsorptionCorrection


# imports for type hinting in PyCharm -- DO NOT DELETE
from widgets.IntegrationWidget import IntegrationWidget
from model.ImgModel import ImgModel
from model.SpectrumModel import SpectrumModel
from model.MaskModel import MaskModel
from model.CalibrationModel import CalibrationModel


class ImageController(object):
    """
    The IntegrationImageController manages the Image actions in the Integration Window. It connects the file actions, as
    well as interaction with the image_view.
    """

    def __init__(self, working_dir, widget, img_model, mask_model, spectrum_model,
                 calibration_data):
        """
        :param working_dir: dictionary of working directories
        :param widget: Reference to IntegrationView
        :param img_model: Reference to ImgModel object
        :param mask_model: Reference to MaskModel object
        :param spectrum_model: Reference to SpectrumModel object
        :param calibration_data: Reference to CalibrationModel object

        :type widget: IntegrationWidget
        :type img_model: ImgModel
        :type mask_model: MaskModel
        :type spectrum_model: SpectrumModel
        :type calibration_data: CalibrationModel
        """
        self.working_dir = working_dir
        self.widget = widget
        self.img_model = img_model
        self.mask_model = mask_model
        self.spectrum_model = spectrum_model
        self.calibration_model = calibration_data

        self._auto_scale = True
        self.img_mode = 'Image'
        self.img_docked = True
        self.use_mask = False
        self.roi_active = False

        self.autoprocess_timer = QtCore.QTimer(self.widget)

        self.widget.show()
        self.initialize()
        self.img_model.subscribe(self.update_img)
        self.create_signals()
        self.create_mouse_behavior()

    def initialize(self):
        self.update_img(True)
        self.plot_mask()
        self.widget.img_view.auto_range()

    def plot_img(self, auto_scale=None):
        """
        Plots the current image loaded in self.img_data.
        :param auto_scale:
            Determines if intensities should be auto-scaled. If value is None it will use the parameter saved in the
            Object (self._auto_scale)
        """
        if auto_scale is None:
            auto_scale = self._auto_scale

        self.widget.img_view.plot_image(self.img_model.get_img(),
                                        False)

        if auto_scale:
            self.widget.img_view.auto_range()

    def plot_cake(self, auto_scale=None):
        """
        Plots the cake saved in the calibration data
        :param auto_scale:
            Determines if the intensity should be auto-scaled. If value is None it will use the parameter saved in the
            object (self._auto_scale)
        """
        if auto_scale is None:
            auto_scale = self._auto_scale
        self.widget.img_view.plot_image(self.calibration_model.cake_img)
        if auto_scale:
            self.widget.img_view.auto_range()

    def plot_mask(self):
        """
        Plots the mask data.
        """
        if self.use_mask and \
                        self.img_mode == 'Image':
            self.widget.img_view.plot_mask(self.mask_model.get_img())
        else:
            self.widget.img_view.plot_mask(
                np.zeros(self.mask_model.get_img().shape))

    def change_mask_colormap(self):
        """
        Changes the colormap of the mask according to the transparency option selection in the GUI. Resulting Mask will
        be either transparent or solid.
        """
        if self.widget.mask_transparent_cb.isChecked():
            self.widget.img_view.set_color([255, 0, 0, 100])
        else:
            self.widget.img_view.set_color([255, 0, 0, 255])

    def change_img_levels_mode(self):
        """
        Sets the img intensity scaling mode according to the option selection in the GUI.
        """
        self.widget.img_view.img_histogram_LUT.percentageLevel = self.widget.img_levels_percentage_rb.isChecked()
        self.widget.img_view.img_histogram_LUT.old_hist_x_range = self.widget.img_view.img_histogram_LUT.hist_x_range
        if self.widget.img_levels_autoscale_rb.isChecked():
            self._auto_scale = True
        else:
            self._auto_scale = False

    def create_signals(self):
        """
        Creates all the connections of the GUI elements.
        """
        self.connect_click_function(self.widget.next_img_btn, self.load_next_img)
        self.connect_click_function(self.widget.prev_img_btn, self.load_previous_img)
        self.connect_click_function(self.widget.load_img_btn, self.load_file)
        self.widget.img_filename_txt.editingFinished.connect(self.filename_txt_changed)
        self.widget.img_directory_txt.editingFinished.connect(self.directory_txt_changed)
        self.connect_click_function(self.widget.img_directory_btn, self.img_directory_btn_click)

        self.connect_click_function(self.widget.img_browse_by_name_rb, self.set_iteration_mode_number)
        self.connect_click_function(self.widget.img_browse_by_time_rb, self.set_iteration_mode_time)
        self.connect_click_function(self.widget.mask_transparent_cb, self.change_mask_colormap)
        self.connect_click_function(self.widget.img_levels_autoscale_rb, self.change_img_levels_mode)
        self.connect_click_function(self.widget.img_levels_absolute_rb, self.change_img_levels_mode)
        self.connect_click_function(self.widget.img_levels_percentage_rb, self.change_img_levels_mode)

        self.connect_click_function(self.widget.img_roi_btn, self.change_roi_mode)
        self.connect_click_function(self.widget.img_mask_btn, self.change_mask_mode)
        self.connect_click_function(self.widget.img_mode_btn, self.change_view_mode)
        self.connect_click_function(self.widget.img_autoscale_btn, self.widget.img_view.auto_range)
        self.connect_click_function(self.widget.img_dock_btn, self.img_dock_btn_clicked)

        self.connect_click_function(self.widget.qa_img_save_img_btn, self.save_img)

        self.connect_click_function(self.widget.img_load_calibration_btn, self.load_calibration)

        self.connect_click_function(self.widget.cbn_groupbox, self.cbn_groupbox_changed)
        self.widget.cbn_diamond_thickness_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_seat_thickness_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_inner_seat_radius_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_outer_seat_radius_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_cell_tilt_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_tilt_rotation_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_center_offset_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_center_offset_angle_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_anvil_al_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.widget.cbn_seat_al_txt.editingFinished.connect(self.cbn_groupbox_changed)
        self.connect_click_function(self.widget.cbn_plot_correction_btn, self.cbn_plot_correction_btn_clicked)

        self.connect_click_function(self.widget.oiadac_groupbox, self.oiadac_groupbox_changed)
        self.widget.oiadac_thickness_txt.editingFinished.connect(self.oiadac_groupbox_changed)
        self.widget.oiadac_abs_length_txt.editingFinished.connect(self.oiadac_groupbox_changed)
        self.connect_click_function(self.widget.oiadac_plot_btn, self.oiadac_plot_btn_clicked)

        self.create_auto_process_signal()

    def connect_click_function(self, emitter, function):
        """
        Small helper function for the button-click connection.
        """
        self.widget.connect(emitter, QtCore.SIGNAL('clicked()'), function)

    def create_mouse_behavior(self):
        """
        Creates the signal connections of mouse interactions
        """
        self.widget.img_view.mouse_left_clicked.connect(self.img_mouse_click)
        self.widget.img_view.mouse_moved.connect(self.show_img_mouse_position)

    def load_file(self, filenames=None):
        if filenames is None:
            filenames = list(QtGui.QFileDialog.getOpenFileNames(
                self.widget, "Load image data file(s)",
                self.working_dir['image']))

        else:
            if isinstance(filenames, str):
                filenames = [filenames]

        if filenames is not None and len(filenames) is not 0:
            self.working_dir['image'] = os.path.dirname(str(filenames[0]))
            if len(filenames) == 1:
                self.img_model.load(str(filenames[0]))
            else:
                self._load_multiple_files(filenames)
            self._check_absorption_correction_shape()

    def _load_multiple_files(self, filenames):
        if not self.calibration_model.is_calibrated:
            self.widget.show_error_msg("Can not integrate multiple images without calibration.")
            return

        working_directory = self._get_spectrum_working_directory()
        if working_directory is '':
            return  # abort file processing if no directory was selected

        progress_dialog = self.widget.get_progress_dialog("Integrating multiple files.", "Abort Integration",
                                                          len(filenames))
        self._set_up_multiple_file_integration()

        for ind in range(len(filenames)):
            filename = str(filenames[ind])
            base_filename = os.path.basename(filename)

            progress_dialog.setValue(ind)
            progress_dialog.setLabelText("Integrating: " + base_filename)

            self.img_model.load(filename)

            x, y = self.integrate_spectrum()
            self._save_spectrum(base_filename, working_directory, x, y)

            QtGui.QApplication.processEvents()
            if progress_dialog.wasCanceled():
                break

        self._tear_down_multiple_file_integration()
        progress_dialog.close()

    def _check_absorption_correction_shape(self):
        if self.img_model.has_corrections() is None and self.widget.cbn_groupbox.isChecked():
            self.widget.cbn_groupbox.setChecked(False)
            self.widget.oiadac_groupbox.setChecked(False)
            QtGui.QMessageBox.critical(self.widget,
                                       'ERROR',
                                       'Due to a change in image dimensions the corrections have been removed')

    def _get_spectrum_working_directory(self):
        if self.widget.spec_autocreate_cb.isChecked():
            working_directory = self.working_dir['spectrum']
        else:
            # if there is no working directory selected A file dialog opens up to choose a directory...
            working_directory = str(QtGui.QFileDialog.getExistingDirectory(
                self.widget, "Please choose the output directory for the integrated spectra.",
                self.working_dir['spectrum']))
        return working_directory

    def _set_up_multiple_file_integration(self):
        self.img_model.turn_off_notification()
        self.spectrum_model.blockSignals(True)
        if self.widget.autoprocess_cb.isChecked():
            self._stop_auto_process()

    def _tear_down_multiple_file_integration(self):
        self.img_model.turn_on_notification()
        self.spectrum_model.blockSignals(False)
        if self.widget.autoprocess_cb.isChecked():
            self._start_auto_process()
        self.img_model.notify()

    def _save_spectrum(self, base_filename, working_directory, x, y):
        file_endings = self._get_spectrum_file_endings()
        for file_ending in file_endings:
            filename = os.path.join(working_directory, os.path.splitext(base_filename)[0] + file_ending)
            print filename
            self.spectrum_model.set_spectrum(x, y, filename, unit=self.get_integration_unit())
            if file_ending == '.xy':
                self.spectrum_model.save_spectrum(filename, header=self._create_spectrum_header())
            else:
                self.spectrum_model.save_spectrum(filename)

    def _create_spectrum_header(self):
        header = self.calibration_model.create_file_header()
        header = header.replace('\r\n', '\n')
        header += '\n#\n# ' + self.spectrum_model.unit + '\t I'
        return header

    def _get_spectrum_file_endings(self):
        res = []
        if self.widget.spectrum_header_xy_cb.isChecked():
            res.append('.xy')
        if self.widget.spectrum_header_chi_cb.isChecked():
            res.append('.chi')
        if self.widget.spectrum_header_dat_cb.isChecked():
            res.append('.dat')
        return res

    def get_integration_unit(self):
        if self.widget.spec_tth_btn.isChecked():
            return '2th_deg'
        elif self.widget.spec_q_btn.isChecked():
            return 'q_A^-1'
        elif self.widget.spec_d_btn.isChecked():
            return 'd_A'

    def integrate_spectrum(self):
        if self.widget.img_mask_btn.isChecked():
            mask = self.mask_model.get_mask()
        else:
            mask = None

        if self.widget.img_roi_btn.isChecked():
            roi_mask = self.widget.img_view.roi.getRoiMask(self.img_model.img_data.shape)
        else:
            roi_mask = None

        if roi_mask is None and mask is None:
            mask = None
        elif roi_mask is None and mask is not None:
            mask = mask
        elif roi_mask is not None and mask is None:
            mask = roi_mask
        elif roi_mask is not None and mask is not None:
            mask = np.logical_or(mask, roi_mask)

        if self.widget.spec_tth_btn.isChecked():
            integration_unit = '2th_deg'
        elif self.widget.spec_q_btn.isChecked():
            integration_unit = 'q_A^-1'
        elif self.widget.spec_d_btn.isChecked():
            integration_unit = 'd_A'
        else:
            # in case something weird happened
            print('No correct integration unit selected')
            return

        if not self.widget.automatic_binning_cb.isChecked():
            num_points = int(str(self.widget.bin_count_txt.text()))
        else:
            num_points = None
        return self.calibration_model.integrate_1d(mask=mask, unit=integration_unit, num_points=num_points)

    def change_mask_mode(self):
        self.use_mask = not self.use_mask
        self.plot_mask()
        auto_scale_save = self._auto_scale
        self._auto_scale = False
        self.img_model.notify()
        self._auto_scale = auto_scale_save

    def load_next_img(self):
        step = int(str(self.widget.image_browse_step_txt.text()))
        self.img_model.load_next_file(step=step)

    def load_previous_img(self):
        step = int(str(self.widget.image_browse_step_txt.text()))
        self.img_model.load_previous_file(step=step)

    def filename_txt_changed(self):
        current_filename = os.path.basename(self.img_model.filename)
        current_directory = str(self.widget.img_directory_txt.text())
        new_filename = str(self.widget.img_filename_txt.text())
        if os.path.exists(os.path.join(current_directory, new_filename)):
            try:
                self.load_file(os.path.join(current_directory, new_filename))
            except TypeError:
                self.widget.img_filename_txt.setText(current_filename)
        else:
            self.widget.img_filename_txt.setText(current_filename)

    def directory_txt_changed(self):
        new_directory = str(self.widget.img_directory_txt.text())
        if os.path.exists(new_directory) and new_directory != self.working_dir['image']:
            if self.widget.autoprocess_cb.isChecked():
                self._files_now = dict([(f, None) for f in os.listdir(self.working_dir['image'])])
            self.working_dir['image'] = os.path.abspath(new_directory)
            old_filename = str(self.widget.img_filename_txt.text())
            self.widget.img_filename_txt.setText(old_filename + '*')
        else:
            self.widget.img_directory_txt.setText(self.working_dir['image'])

    def img_directory_btn_click(self):
        directory = str(QtGui.QFileDialog.getExistingDirectory(
            self.widget,
            "Please choose the image working directory.",
            self.working_dir['image']))
        if directory is not '':
            if self.widget.autoprocess_cb.isChecked():
                self._files_now = dict([(f, None) for f in os.listdir(self.working_dir['image'])])
            self.working_dir['image'] = directory
            self.widget.img_directory_txt.setText(directory)

    def update_img(self, reset_img_levels=None):
        self.widget.img_filename_txt.setText(os.path.basename(self.img_model.filename))
        self.widget.img_directory_txt.setText(os.path.dirname(self.img_model.filename))
        self.widget.cbn_plot_correction_btn.setText('Plot')
        self.widget.oiadac_plot_btn.setText('Plot')

        if self.img_mode == 'Cake' and \
                self.calibration_model.is_calibrated:
            if self.use_mask:
                mask = self.mask_model.get_img()
            else:
                mask = np.zeros(self.img_model._img_data.shape)

            if self.roi_active:
                roi_mask = np.ones(self.img_model._img_data.shape)
                x1, x2, y1, y2 = self.widget.img_view.roi.getIndexLimits(self.img_model._img_data.shape)
                roi_mask[x1:x2, y1:y2] = 0
            else:
                roi_mask = np.zeros(self.img_model._img_data.shape)

            if self.use_mask or self.roi_active:
                mask = np.logical_or(mask, roi_mask)
            else:
                mask = None

            self.calibration_model.integrate_2d(mask)
            self.plot_cake()
            self.widget.img_view.plot_mask(
                np.zeros(self.mask_model.get_img().shape))
            self.widget.img_view.activate_vertical_line()
            self.widget.img_view.img_view_box.setAspectLocked(False)
        elif self.img_mode == 'Image':
            self.plot_mask()
            self.plot_img(reset_img_levels)
            self.widget.img_view.deactivate_vertical_line()
            self.widget.img_view.img_view_box.setAspectLocked(True)

    def change_roi_mode(self):
        self.roi_active = not self.roi_active
        if self.img_mode == 'Image':
            if self.roi_active:
                self.widget.img_view.activate_roi()
            else:
                self.widget.img_view.deactivate_roi()

        auto_scale_save = self._auto_scale
        self._auto_scale = False
        self.img_model.notify()
        self._auto_scale = auto_scale_save

    def change_view_mode(self):
        self.img_mode = self.widget.img_mode_btn.text()
        if not self.calibration_model.is_calibrated:
            return
        else:
            self.update_img()
            if self.img_mode == 'Cake':
                self.widget.img_view.deactivate_circle_scatter()
                self.widget.img_view.deactivate_roi()
                self._update_cake_line_pos()
                self.widget.img_mode_btn.setText('Image')
            elif self.img_mode == 'Image':
                self.widget.img_view.activate_circle_scatter()
                if self.roi_active:
                    self.widget.img_view.activate_roi()
                self._update_image_scatter_pos()
                self.widget.img_mode_btn.setText('Cake')

    def img_dock_btn_clicked(self):
        self.img_docked = not self.img_docked
        self.widget.dock_img(self.img_docked)

    def _update_cake_line_pos(self):
        cur_tth = self.get_current_spectrum_tth()
        if cur_tth < np.min(self.calibration_model.cake_tth):
            new_pos = np.min(self.calibration_model.cake_tth)
        else:
            upper_ind = np.where(self.calibration_model.cake_tth > cur_tth)
            lower_ind = np.where(self.calibration_model.cake_tth < cur_tth)

            spacing = self.calibration_model.cake_tth[upper_ind[0][0]] - \
                      self.calibration_model.cake_tth[lower_ind[-1][-1]]
            new_pos = lower_ind[-1][-1] + \
                      (cur_tth -
                       self.calibration_model.cake_tth[lower_ind[-1][-1]]) / spacing
        self.widget.img_view.vertical_line.setValue(new_pos)

    def _update_image_scatter_pos(self):
        cur_tth = self.get_current_spectrum_tth()
        self.widget.img_view.set_circle_scatter_tth(
            self.calibration_model.get_two_theta_array(), cur_tth / 180 * np.pi)

    def get_current_spectrum_tth(self):
        cur_pos = self.widget.spectrum_view.pos_line.getPos()[0]
        if self.widget.spec_q_btn.isChecked():
            cur_tth = self.convert_x_value(cur_pos, 'q_A^-1', '2th_deg')
        elif self.widget.spec_tth_btn.isChecked():
            cur_tth = cur_pos
        elif self.widget.spec_d_btn.isChecked():
            cur_tth = self.convert_x_value(cur_pos, 'd_A', '2th_deg')
        else:
            cur_tth = None
        return cur_tth

    def show_img_mouse_position(self, x, y):
        img_shape = self.img_model.get_img().shape
        if x > 0 and y > 0 and x < img_shape[1] - 1 and y < img_shape[0] - 1:
            x_pos_string = 'X:  %4d' % x
            y_pos_string = 'Y:  %4d' % y
            self.widget.mouse_x_lbl.setText(x_pos_string)
            self.widget.mouse_y_lbl.setText(y_pos_string)

            self.widget.img_widget_mouse_x_lbl.setText(x_pos_string)
            self.widget.img_widget_mouse_y_lbl.setText(y_pos_string)

            int_string = 'I:   %5d' % self.widget.img_view.img_data[
                np.floor(y), np.floor(x)]

            self.widget.mouse_int_lbl.setText(int_string)
            self.widget.img_widget_mouse_int_lbl.setText(int_string)

            if self.calibration_model.is_calibrated:
                x_temp = x
                x = np.array([y])
                y = np.array([x_temp])
                if self.img_mode == 'Cake':
                    tth = self.calibration_model.get_two_theta_cake(y)
                    azi = self.calibration_model.get_azi_cake(x)
                    q_value = self.convert_x_value(tth, '2th_deg', 'q_A^-1')

                else:
                    tth = self.calibration_model.get_two_theta_img(x, y)
                    tth = tth / np.pi * 180.0
                    q_value = self.convert_x_value(tth, '2th_deg', 'q_A^-1')
                    azi = self.calibration_model.get_azi_img(x, y) / np.pi * 180

                azi = azi + 360 if azi < 0 else azi
                d = self.convert_x_value(tth, '2th_deg', 'd_A')
                tth_str = u"2θ:%9.3f  " % tth
                self.widget.mouse_tth_lbl.setText(unicode(tth_str))
                self.widget.mouse_d_lbl.setText('d:%9.3f  ' % d)
                self.widget.mouse_q_lbl.setText('Q:%9.3f  ' % q_value)
                self.widget.mouse_azi_lbl.setText('X:%9.3f  ' % azi)
                self.widget.img_widget_mouse_tth_lbl.setText(unicode(tth_str))
                self.widget.img_widget_mouse_d_lbl.setText('d:%9.3f  ' % d)
                self.widget.img_widget_mouse_q_lbl.setText('Q:%9.3f  ' % q_value)
                self.widget.img_widget_mouse_azi_lbl.setText('X:%9.3f  ' % azi)
            else:
                self.widget.mouse_tth_lbl.setText(u'2θ: -')
                self.widget.mouse_d_lbl.setText('d: -')
                self.widget.mouse_q_lbl.setText('Q: -')
                self.widget.mouse_azi_lbl.setText('X: -')
                self.widget.img_widget_mouse_tth_lbl.setText(u'2θ: -')
                self.widget.img_widget_mouse_d_lbl.setText('d: -')
                self.widget.img_widget_mouse_q_lbl.setText('Q: -')
                self.widget.img_widget_mouse_azi_lbl.setText('X: -')

    def img_mouse_click(self, x, y):
        # update click position
        try:
            x_pos_string = 'X:  %4d' % y
            y_pos_string = 'Y:  %4d' % x
            int_string = 'I:   %5d' % self.widget.img_view.img_data[
                np.floor(x), np.floor(y)]

            self.widget.click_x_lbl.setText(x_pos_string)
            self.widget.click_y_lbl.setText(y_pos_string)
            self.widget.click_int_lbl.setText(int_string)

            self.widget.img_widget_click_x_lbl.setText(x_pos_string)
            self.widget.img_widget_click_y_lbl.setText(y_pos_string)
            self.widget.img_widget_click_int_lbl.setText(int_string)
        except IndexError:
            self.widget.click_int_lbl.setText('I: ')

        if self.calibration_model.is_calibrated:
            if self.img_mode == 'Cake':  # cake mode
                cake_shape = self.calibration_model.cake_img.shape
                if x < 0 or y < 0 or x > (cake_shape[0] - 1) or y > (cake_shape[1] - 1):
                    return
                y = np.array([y])
                tth = self.calibration_model.get_two_theta_cake(y) / 180 * np.pi
            elif self.img_mode == 'Image':  # image mode
                img_shape = self.img_model.get_img().shape
                if x < 0 or y < 0 or x > img_shape[0] - 1 or y > img_shape[1] - 1:
                    return
                tth = self.calibration_model.get_two_theta_img(x, y)
                self.widget.img_view.set_circle_scatter_tth(
                    self.calibration_model.get_two_theta_array(), tth)
            else:  # in the case of whatever
                tth = 0

            # calculate right unit
            if self.widget.spec_q_btn.isChecked():
                pos = 4 * np.pi * \
                      np.sin(tth / 2) / \
                      self.calibration_model.wavelength / 1e10
            elif self.widget.spec_tth_btn.isChecked():
                pos = tth / np.pi * 180
            elif self.widget.spec_d_btn.isChecked():
                pos = self.calibration_model.wavelength / \
                      (2 * np.sin(tth / 2)) * 1e10
            else:
                pos = 0
            self.widget.spectrum_view.set_pos_line(pos)
        self.widget.click_tth_lbl.setText(self.widget.mouse_tth_lbl.text())
        self.widget.click_d_lbl.setText(self.widget.mouse_d_lbl.text())
        self.widget.click_q_lbl.setText(self.widget.mouse_q_lbl.text())
        self.widget.click_azi_lbl.setText(self.widget.mouse_azi_lbl.text())
        self.widget.img_widget_click_tth_lbl.setText(self.widget.mouse_tth_lbl.text())
        self.widget.img_widget_click_d_lbl.setText(self.widget.mouse_d_lbl.text())
        self.widget.img_widget_click_q_lbl.setText(self.widget.mouse_q_lbl.text())
        self.widget.img_widget_click_azi_lbl.setText(self.widget.mouse_azi_lbl.text())

    def set_iteration_mode_number(self):
        self.img_model.set_file_iteration_mode('number')

    def set_iteration_mode_time(self):
        self.img_model.set_file_iteration_mode('time')

    def convert_x_value(self, value, previous_unit, new_unit):
        wavelength = self.calibration_model.wavelength
        if previous_unit == '2th_deg':
            tth = value
        elif previous_unit == 'q_A^-1':
            tth = np.arcsin(
                value * 1e10 * wavelength / (4 * np.pi)) * 360 / np.pi
        elif previous_unit == 'd_A':
            tth = 2 * np.arcsin(wavelength / (2 * value * 1e-10)) * 180 / np.pi
        else:
            tth = 0

        if new_unit == '2th_deg':
            res = tth
        elif new_unit == 'q_A^-1':
            res = 4 * np.pi * \
                  np.sin(tth / 360 * np.pi) / \
                  wavelength / 1e10
        elif new_unit == 'd_A':
            res = wavelength / (2 * np.sin(tth / 360 * np.pi)) * 1e10
        else:
            res = 0
        return res

    def load_calibration(self, filename=None):
        if filename is None:
            filename = str(QtGui.QFileDialog.getOpenFileName(
                self.widget, "Load calibration...",
                self.working_dir[
                    'calibration'],
                '*.poni'))
        if filename is not '':
            self.working_dir['calibration'] = os.path.dirname(filename)
            self.calibration_model.load(filename)
            self.widget.calibration_lbl.setText(
                self.calibration_model.calibration_name)
            self.img_model.notify()

    def create_auto_process_signal(self):
        self.widget.autoprocess_cb.clicked.connect(self.auto_process_cb_click)
        self.autoprocess_timer.setInterval(50)
        self.widget.connect(self.autoprocess_timer,
                            QtCore.SIGNAL('timeout()'),
                            self.check_files)

    def auto_process_cb_click(self):
        if self.widget.autoprocess_cb.isChecked():
            self._start_auto_process()
        else:
            self._stop_auto_process()

    def _start_auto_process(self):
        self._files_before = dict(
            [(f, None) for f in os.listdir(self.working_dir['image'])])
        self.autoprocess_timer.start()

    def _stop_auto_process(self):
        self.autoprocess_timer.stop()

    def check_files(self):
        self.autoprocess_timer.blockSignals(True)
        self._files_now = dict(
            [(f, None) for f in os.listdir(self.working_dir['image'])])
        self._files_added = [
            f for f in self._files_now if not f in self._files_before]
        self._files_removed = [
            f for f in self._files_before if not f in self._files_now]
        if len(self._files_added) > 0:
            new_file_str = self._files_added[-1]
            path = os.path.join(self.working_dir['image'], new_file_str)
            acceptable_file_endings = ['.img', '.sfrm', '.dm3', '.edf', '.xml',
                                       '.cbf', '.kccd', '.msk', '.spr', '.tif',
                                       '.mccd', '.mar3450', '.pnm']
            read_file = False
            for ending in acceptable_file_endings:
                if path.endswith(ending):
                    read_file = True
                    break
            file_info = os.stat(path)
            if file_info.st_size > 100:
                if read_file:
                    self.load_file(path)
                self._files_before = self._files_now
        self.autoprocess_timer.blockSignals(False)

    def save_img(self, filename=None):
        if filename is None:
            filename = str(QtGui.QFileDialog.getSaveFileName(self.widget, "Save Image.",
                                                             self.working_dir['image'],
                                                             ('Image (*.png);;Data (*.tiff)')))
        if filename is not '':
            if filename.endswith('.png'):
                if self.img_mode == 'Cake':
                    self.widget.img_view.deactivate_vertical_line()
                elif self.img_mode == 'Image':
                    self.widget.img_view.deactivate_circle_scatter()
                    self.widget.img_view.deactivate_roi()

                QtGui.QApplication.processEvents()
                self.widget.img_view.save_img(filename)

                if self.img_mode == 'Cake':
                    self.widget.img_view.activate_vertical_line()
                elif self.img_mode == 'Image':
                    self.widget.img_view.activate_circle_scatter()
                    if self.roi_active:
                        self.widget.img_view.activate_roi()
            elif filename.endswith('.tiff'):
                if self.img_mode == 'Image':
                    im_array = np.int32(self.img_model.img_data)
                elif self.img_mode == 'Cake':
                    im_array = np.int32(self.calibration_model.cake_img)
                im_array = np.flipud(im_array)
                im = Image.fromarray(im_array)
                im.save(filename)

    def cbn_groupbox_changed(self):
        if not self.calibration_model.is_calibrated:
            self.widget.cbn_groupbox.setChecked(False)
            QtGui.QMessageBox.critical(self.widget,
                                       'ERROR',
                                       'Please calibrate the geometry first or load an existent calibration file. ' + \
                                       'The cBN seat correction needs a calibrated geometry.')
            return

        if self.widget.cbn_groupbox.isChecked():
            diamond_thickness = float(str(self.widget.cbn_diamond_thickness_txt.text()))
            seat_thickness = float(str(self.widget.cbn_seat_thickness_txt.text()))
            inner_seat_radius = float(str(self.widget.cbn_inner_seat_radius_txt.text()))
            outer_seat_radius = float(str(self.widget.cbn_outer_seat_radius_txt.text()))
            tilt = float(str(self.widget.cbn_cell_tilt_txt.text()))
            tilt_rotation = float(str(self.widget.cbn_tilt_rotation_txt.text()))
            center_offset = float(str(self.widget.cbn_center_offset_txt.text()))
            center_offset_angle = float(str(self.widget.cbn_center_offset_angle_txt.text()))
            seat_absorption_length = float(str(self.widget.cbn_seat_al_txt.text()))
            anvil_absorption_length = float(str(self.widget.cbn_anvil_al_txt.text()))

            tth_array = 180.0 / np.pi * self.calibration_model.spectrum_geometry.ttha
            azi_array = 180.0 / np.pi * self.calibration_model.spectrum_geometry.chia
            import time

            t1 = time.time()

            cbn_correction = CbnCorrection(
                tth_array=tth_array,
                azi_array=azi_array,
                diamond_thickness=diamond_thickness,
                seat_thickness=seat_thickness,
                small_cbn_seat_radius=inner_seat_radius,
                large_cbn_seat_radius=outer_seat_radius,
                tilt=tilt,
                tilt_rotation=tilt_rotation,
                center_offset=center_offset,
                center_offset_angle=center_offset_angle,
                cbn_abs_length=seat_absorption_length,
                diamond_abs_length=anvil_absorption_length
            )
            print "Time needed for correction calculation: {0}".format(time.time() - t1)
            try:
                self.img_model.delete_img_correction("cbn")
            except KeyError:
                pass
            self.img_model.add_img_correction(cbn_correction, "cbn")
        else:
            self.img_model.delete_img_correction("cbn")


    def cbn_plot_correction_btn_clicked(self):
        if str(self.widget.cbn_plot_correction_btn.text()) == 'Plot':
            self.widget.img_view.plot_image(self.img_model._img_corrections.get_correction("cbn").get_data(),
                                            True)
            self.widget.cbn_plot_correction_btn.setText('Back')
            self.widget.oiadac_plot_btn.setText('Plot')
        else:
            self.widget.cbn_plot_correction_btn.setText('Plot')
            if self.img_mode == 'Cake':
                self.plot_cake(True)
            elif self.img_mode == 'Image':
                self.plot_img(True)


    def oiadac_groupbox_changed(self):
        if not self.calibration_model.is_calibrated:
            self.widget.oiadac_groupbox.setChecked(False)
            QtGui.QMessageBox.critical(
                self.widget,
                'ERROR',
                'Please calibrate the geometry first or load an existent calibration file. ' + \
                'The oblique incidence angle detector absorption correction needs a calibrated' + \
                'geometry.'
            )
            return

        if self.widget.oiadac_groupbox.isChecked():
            detector_thickness = float(str(self.widget.oiadac_thickness_txt.text()))
            absorption_length = float(str(self.widget.oiadac_abs_length_txt.text()))

            _, fit2d_parameter = self.calibration_model.get_calibration_parameter()
            detector_tilt = fit2d_parameter['tilt']
            detector_tilt_rotation = fit2d_parameter['tiltPlanRotation']

            tth_array = self.calibration_model.spectrum_geometry.ttha
            azi_array = self.calibration_model.spectrum_geometry.chia
            import time

            t1 = time.time()

            oiadac_correction = ObliqueAngleDetectorAbsorptionCorrection(
                tth_array, azi_array,
                detector_thickness=detector_thickness,
                absorption_length=absorption_length,
                tilt=detector_tilt,
                rotation=detector_tilt_rotation,
            )
            print "Time needed for correction calculation: {0}".format(time.time() - t1)
            try:
                self.img_model.delete_img_correction("oiadac")
            except KeyError:
                pass
            self.img_model.add_img_correction(oiadac_correction, "oiadac")
        else:
            self.img_model.delete_img_correction("oiadac")

    def oiadac_plot_btn_clicked(self):
        if str(self.widget.oiadac_plot_btn.text()) == 'Plot':
            self.widget.img_view.plot_image(self.img_model._img_corrections.get_correction("oiadac").get_data(),
                                            True)
            self.widget.oiadac_plot_btn.setText('Back')
            self.widget.cbn_plot_correction_btn.setText('Plot')
        else:
            self.widget.oiadac_plot_btn.setText('Plot')
            if self.img_mode == 'Cake':
                self.plot_cake(True)
            elif self.img_mode == 'Image':
                self.plot_img(True)
