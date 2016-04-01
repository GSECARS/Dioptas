# -*- coding: utf8 -*-
# Dioptas - GUI program for fast processing of 2D X-ray data
# Copyright (C) 2015  Clemens Prescher (clemens.prescher@gmail.com)
# Institute for Geology and Mineralogy, University of Cologne
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

from __future__ import absolute_import

import sys
import os
import time
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import traceback
from PyQt4 import QtGui

from widgets.UtilityWidgets import ErrorMessageBox

app = QtGui.QApplication(sys.argv)
app.setGraphicsSystem("raster")

dioptas_version = "unknown"


def excepthook(exc_type, exc_value, traceback_obj):
    """
    Global function to catch unhandled exceptions. This function will result in an error dialog which displays the
    error information.

    :param exc_type: exception type
    :param exc_value: exception value
    :param traceback_obj: traceback object
    :return:
    """

    separator = '-' * 80
    log_file = "error.log"
    notice = \
        """An unhandled exception occurred. Please report the bug under:\n """ \
        """\t%s\n""" \
        """or via email to:\n\t <%s>.\n\n""" \
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("https://github.com/Dioptas/Dioptas/issues",
         "clemens.prescher@gmail.com",
         os.path.join(os.path.dirname(__file__), log_file))
    version_info = '\n'.join((separator, "Dioptas Version: %s" % dioptas_version))
    time_string = time.strftime("%Y-%m-%d, %H:%M:%S")
    tb_info_file = StringIO()
    traceback.print_tb(traceback_obj, None, tb_info_file)
    tb_info_file.seek(0)
    tb_info = tb_info_file.read()
    errmsg = '%s: \n%s' % (str(exc_type), str(exc_value))
    sections = [separator, time_string, separator, errmsg, separator, tb_info]
    msg = '\n'.join(sections)
    try:
        f = open(log_file, "w")
        f.write(msg)
        f.write(version_info)
        f.close()
    except IOError:
        pass
    errorbox = ErrorMessageBox()
    errorbox.setText(str(notice) + str(msg) + str(version_info))
    errorbox.exec_()

sys.excepthook = excepthook


if __name__ == "__main__":

    from sys import platform as _platform
    from controller.MainController import MainController, get_version
    dioptas_version = get_version()
    print("Dioptas {}".format(dioptas_version))

    if _platform == "linux" or _platform == "linux2" or _platform == "win32" or _platform == 'cygwin':
        app.setStyle('plastique')

    controller = MainController()
    controller.show_window()
    app.exec_()
    del app
