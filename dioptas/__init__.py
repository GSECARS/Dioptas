# SPDX-License-Identifier: MIT

import logging
import os
import sys
from sys import platform as _platform

from .log import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

# If QT_API is not set, use PyQt6 by default
if "QT_API" not in os.environ:
    try:
        import PyQt6.QtCore
    except ImportError:
        pass

from qtpy import QtWidgets
from qt_material import apply_stylesheet

try:
    from pyshortcuts import make_shortcut
except ImportError:
    make_shortcut = None

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("dioptas")
except Exception:
    try:
        import tomllib
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(_root, "pyproject.toml"), "rb") as _f:
            __version__ = tomllib.load(_f)["project"]["version"]
    except Exception:
        __version__ = "0.0.0"

from .paths import resources_path, calibrants_path, icons_path, data_path, style_path
from .excepthook import excepthook
from .controller.MainController import MainController


theme_path = os.path.join(style_path, "dark_orange.xml")
qss_path = os.path.join(style_path, "qt_material.css")

_dioptrin_available = False


def _check_dioptrin_license():
    """Check dioptrin license at startup. Returns True if usable."""
    try:
        import dioptrin

        dioptrin.validate_license()
        return True
    except ImportError:
        return False
    except dioptrin.LicenseNotFoundError:
        return False
    except dioptrin.LicenseExpiredError:
        QtWidgets.QMessageBox.warning(
            None,
            "Dioptrin License Expired",
            "Your Dioptrin license has expired. "
            "Dioptas will use pyFAI for integration.\n\n"
            "Please renew your license to continue using Dioptrin.",
        )
        return False
    except dioptrin.LicenseError:
        return False


def _win_local_icon():
    """Return a locally cached copy of icon.ico on Windows.

    Windows Explorer resolves shortcut icons at shell startup, before network
    shares are necessarily mapped.  Caching the .ico in %APPDATA% ensures the
    shortcut and taskbar always show the Dioptas icon even when the source
    tree lives on a Samba share.  Falls back to the package path on failure.
    """
    import shutil

    src = os.path.join(icons_path, "icon.ico")
    from .paths import user_data_dir
    dest_dir = user_data_dir()
    try:
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, "icon.ico")
        shutil.copy2(src, dest)
        return dest
    except OSError:
        return src


def _set_application_icon(app):
    """Application-wide icon, inherited by every top-level window.

    On Windows the .ico is used: it carries pre-rendered 16-256 px entries,
    which the shell can consume directly for the taskbar and Alt-Tab. The
    other platforms take the SVG, which scales to any size Qt asks for.
    """
    from qtpy import QtGui

    if _platform == "win32":
        icon_file = _win_local_icon()
    else:
        icon_file = os.path.join(icons_path, "icon.svg")
    app.setWindowIcon(QtGui.QIcon(icon_file))


def main():
    global _dioptrin_available

    if _platform == "win32":
        # Windows resolves the taskbar button's icon through the application
        # identity, not the window; without an explicit one it has to guess,
        # which comes up empty on the first run of a fresh executable.
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "com.dioptas.Dioptas"
        )

    app = QtWidgets.QApplication([])
    _set_application_icon(app)

    apply_stylesheet(
        app,
        theme=theme_path,
        css_file=qss_path,
        extra={"density_scale": -2},
    )
    sys.excepthook = excepthook
    logger.info("Dioptas %s", __version__)

    _dioptrin_available = _check_dioptrin_license()

    if len(sys.argv) == 1:  # normal start
        controller = MainController()
        controller.show_window()
        app.exec_()
    else:  # with command line arguments
        if sys.argv[1] == "test":
            controller = MainController(use_settings=False)
            controller.show_window()

        elif sys.argv[1].startswith("makeshortcut") or sys.argv[1] in ("--make-icon", "-m", "-p", "--public"):
            if make_shortcut is None:
                raise ImportError("pyshortcuts not installed.  Try `pip install pyshortcuts`")
            if _platform == "win32":
                # Pass the full .ico path. pyshortcuts falls back to Python's
                # icon when Path(icon).exists() is False, which happens if the
                # extension is omitted. The local AppData copy is always
                # accessible even when the Samba share isn't mounted yet.
                icon = _win_local_icon()
            else:
                icon = os.path.join(icons_path, "icon")
            public = sys.argv[1] in ("-p", "--public") or "-p" in sys.argv[2:] or "--public" in sys.argv[2:]
            make_shortcut(
                "-m dioptas",
                name="Dioptas",
                description="Dioptas 2D XRD {}".format(__version__),
                icon=icon,
                terminal=False,
                public=public,
            )

        elif sys.argv[1].startswith("version"):
            print(__version__)

        elif sys.argv[1].endswith(".json"):
            controller = MainController(config_file=sys.argv[1])
            controller.show_window()
            app.exec_()
    del app
