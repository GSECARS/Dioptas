# -*- coding: utf-8 -*-
# Dioptas - GUI program for fast processing of 2D X-ray diffraction data
# Principal author: Clemens Prescher (clemens.prescher@gmail.com)
# Copyright (C) 2014-2019 GSECARS, University of Chicago, USA
# Copyright (C) 2015-2018 Institute for Geology and Mineralogy, University of Cologne, Germany
# Copyright (C) 2019-2020 DESY, Hamburg, Germany
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
import numpy as np
from qtpy import QtWidgets

from dioptas.model import DioptasModel
from dioptas.model.util.calc import convert_units
from dioptas.widgets.MapWidget import MapWidget

from ..widgets.UtilityWidgets import get_progress_dialog, open_files_dialog
from .integration.phase.PhaseInPatternController import PhaseInPatternController


class MapController(object):
    def __init__(self, widget: MapWidget, dioptas_model: DioptasModel):
        self.widget = widget
        self.model = dioptas_model

        self.phase_in_pattern_controller = PhaseInPatternController(
            self.widget.pattern_plot_widget, self.model
        )

        self.create_signals()

    def create_signals(self):
        self.widget.control_widget.load_btn.clicked.connect(self.load_btn_clicked)
        self.widget.control_widget.file_list.currentRowChanged.connect(
            self.file_list_row_changed
            # needs to be its own function, to always recall the model.map_model
            # this ensures, that the currently selected configuration is used
        )
        self.widget.map_plot_widget.mouse_left_clicked.connect(self.map_point_selected)
        self.widget.pattern_plot_widget.mouse_left_clicked.connect(self.pattern_clicked)
        self.widget.pattern_plot_widget.map_interactive_roi.sigRegionChanged.connect(
            self.pattern_roi_changed
        )
        self.widget.map_plot_control_widget.map_dimension_cb.currentIndexChanged.connect(
            self.map_dimension_cb_changed
        )
        self.widget.map_plot_widget.mouse_moved.connect(self.map_plot_mouse_moved)
        self.widget.img_plot_widget.mouse_left_clicked.connect(
            self.img_plot_left_clicked
        )

        self.model.map_model.map_changed.connect(self.update_map)
        self.model.map_model.map_changed.connect(self.update_file_list)
        self.model.clicked_tth_changed.connect(self.update_pattern_green_line)
        self.model.clicked_tth_changed.connect(self.update_image_green_line)

        self.activate_model_signals()

    def activate(self):
        self.activate_model_signals()
        self.configuration_selected()

    def activate_model_signals(self):
        self.model.img_changed.connect(self.update_image)
        self.model.pattern_changed.connect(self.update_pattern)
        self.model.configuration_selected.connect(self.configuration_selected)

    def deactivate(self):
        self.model.img_changed.disconnect(self.update_image)
        self.model.pattern_changed.disconnect(self.update_pattern)
        self.model.configuration_selected.disconnect(self.configuration_selected)

    def load_btn_clicked(self):
        filenames = open_files_dialog(
            self.widget,
            "Load image data file(s)",
            self.model.working_directories["image"],
        )
        if len(filenames) == 0:
            return

        progressDialog = get_progress_dialog(
            "Loading image data", "Abort Integration", 100, self.widget.map_pg_layout
        )

        def update_progress_dialog(value):
            progress_value = int(value / len(filenames) * 100)
            progressDialog.setValue(progress_value)
            QtWidgets.QApplication.processEvents()

        self.model.map_model.point_integrated.connect(update_progress_dialog)
        try:
            self.model.map_model.load(filenames)
            self.model.map_model.select_point(0, 0)
        except ValueError as e:
            QtWidgets.QMessageBox.critical(
                self.widget, "Error loading image data.", str(e)
            )
        finally:
            self.model.map_model.point_integrated.disconnect(progressDialog.setValue)
            progressDialog.close()

    def update_file_list(self):
        # get current items
        items = [
            self.widget.control_widget.file_list.item(i).text()
            for i in range(self.widget.control_widget.file_list.count())
        ]
        if items == self.model.map_model.get_filenames():
            return

        self.widget.control_widget.file_list.blockSignals(True)
        self.widget.control_widget.file_list.clear()
        filenames = self.model.map_model.get_filenames()
        if len(filenames) == 0:  # no files loaded
            return
        self.widget.control_widget.file_list.addItems(filenames)
        self.widget.control_widget.file_list.blockSignals(False)

    def update_map(self):
        if self.model.map_model.map is None:
            # clear image
            self.widget.map_plot_widget.plot_image(np.array([[], []]))
        else:
            self.widget.map_plot_widget.plot_image(
                np.flipud(self.model.map_model.map), auto_level=True
            )
            self.update_dimension_cb()

    def update_dimension_cb(self):
        dim_cb = self.widget.map_plot_control_widget.map_dimension_cb
        dim_cb.blockSignals(True)
        dim_cb.clear()
        possible_dimensions_str = [
            f"{x}x{y}" for x, y in self.model.map_model.possible_dimensions
        ]
        dim_cb.addItems(possible_dimensions_str)
        current_dimension_index = self.model.map_model.possible_dimensions.index(
            self.model.map_model.dimension
        )
        dim_cb.setCurrentIndex(current_dimension_index)
        dim_cb.blockSignals(False)

    def update_image(self):
        if self.model.img_model.img_data is None:
            # clear image
            self.widget.img_plot_widget.plot_image(np.array([[], []]))
        else:
            self.widget.img_plot_widget.plot_image(
                self.model.img_model.img_data, auto_level=True
            )
            self.plot_mask()

    def plot_mask(self):
        if self.model.current_configuration.use_mask:
            self.widget.img_plot_widget.activate_mask()
            self.widget.img_plot_widget.plot_mask(self.model.mask_model.get_mask())
        else:
            self.widget.img_plot_widget.deactivate_mask()

    def update_pattern(self):
        self.widget.pattern_plot_widget.plot_data(
            self.model.pattern.x, self.model.pattern.y
        )
        self.update_pattern_green_line(self.model.clicked_tth)

    def update_pattern_green_line(self, pos):
        if self.model.integration_unit == "2th_deg":
            self.widget.pattern_plot_widget.set_pos_line(pos)
        else:
            wavelength = self.model.calibration_model.wavelength
            new_pos = convert_units(
                pos, wavelength, "2th_deg", self.model.integration_unit
            )
            self.widget.pattern_plot_widget.set_pos_line(new_pos)

    def update_image_green_line(self, pos):
        if not self.model.current_configuration.is_calibrated:
            return

        self.widget.img_plot_widget.set_circle_line(
            self.model.calibration_model.pattern_geometry.ttha, np.deg2rad(pos)
        )

    def file_list_row_changed(self, row):
        self.model.map_model.select_point_by_index(row)
        row, col = self.model.map_model.get_point_coordinates(row)
        map_shape = self.model.map_model.map.shape
        self.widget.map_plot_widget.set_mouse_click_position(
            col + 0.5, map_shape[0] - row - 0.5  # 0.5 are there to shift to center
        )

    def _get_mouse_row_col(self, x, y):
        x, y = np.floor(x), np.floor(y)
        row = self.widget.map_plot_widget.img_data.shape[0] - int(y) - 1
        col = int(x)
        return row, col

    def _row_col_in_map(self, row, col):
        map_shape = self.widget.map_plot_widget.img_data.shape
        if row < 0 or col < 0 or row >= map_shape[0] or col >= map_shape[1]:
            return False
        return True

    def map_point_selected(self, clicked_x, clicked_y):
        # skip when now map is loaded
        if self.model.map_model.map is None:
            return

        row, col = self._get_mouse_row_col(clicked_x, clicked_y)

        # skip when the mouse is outside of the map
        if not self._row_col_in_map(row, col):
            return

        self.model.map_model.select_point(row, col)
        ind = self.model.map_model.get_point_index(row, col)

        self.widget.control_widget.file_list.blockSignals(True)
        self.widget.control_widget.file_list.setCurrentRow(ind)
        self.widget.control_widget.file_list.blockSignals(False)

    def map_dimension_cb_changed(self, _):
        dimension_str = (
            self.widget.map_plot_control_widget.map_dimension_cb.currentText()
        )
        dimension = tuple([int(x) for x in dimension_str.split("x")])
        self.model.map_model.set_dimension(dimension)

    def map_plot_mouse_moved(self, x, y):
        # shows the information for a point inside of the map
        # since pyqtgraph gives the coordinates in the image coordinate system
        # we need to flip the y axis

        # skip when no image is loaded
        if self.widget.map_plot_widget.img_data is None:
            return

        row, col = self._get_mouse_row_col(x, y)

        # if the mouse is outside of the image, we don't want to show any information
        if not self._row_col_in_map(row, col):
            self.widget.map_plot_control_widget.mouse_x_label.setText(f"X: ")
            self.widget.map_plot_control_widget.mouse_y_label.setText(f"Y: ")
            self.widget.map_plot_control_widget.mouse_int_label.setText(f"I: ")
            self.widget.map_plot_control_widget.filename_label.setText(f"")
            return

        self.widget.map_plot_control_widget.mouse_x_label.setText(f"X: {col:.0f}")
        self.widget.map_plot_control_widget.mouse_y_label.setText(f"Y: {row:.0f}")
        self.widget.map_plot_control_widget.mouse_int_label.setText(
            f"I: {self.model.map_model.map[row, col]:.0f}"
        )

        point_info = self.model.map_model.get_point_info(row, col)
        if point_info.frame_index == 0:
            self.widget.map_plot_control_widget.filename_label.setText(
                f"{point_info.filename}"
            )
        else:
            self.widget.map_plot_control_widget.filename_label.setText(
                f"{point_info.filename} - Frame: {point_info.frame_index}"
            )

    def img_plot_left_clicked(self, x, y):
        if not self.model.current_configuration.is_calibrated:
            return

        calibration_model = self.model.calibration_model
        img_shape = self.model.img_model.img_data.shape

        x, y = np.array([y]), np.array([x])
        if 0.5 < x < img_shape[0] - 0.5 and 0.5 < y < img_shape[1] - 0.5:
            tth = calibration_model.get_two_theta_img(x, y)
            azi = calibration_model.get_azi_img(x, y)

            self.model.clicked_tth_changed.emit(np.rad2deg(tth))
            self.model.clicked_azi_changed.emit(np.rad2deg(azi))

    def pattern_clicked(self, x, _):
        self.widget.pattern_plot_widget.map_interactive_roi.setCenter(x)

    def pattern_roi_changed(self, interactive_roi):
        region = interactive_roi.getRegion()
        self.model.map_model.set_window(region)

    def configuration_selected(self):
        self.update_file_list()
        self.update_map()
        self.update_image()
        self.update_pattern()
