# SPDX-License-Identifier: MIT

import os
import sys

resources_path = os.path.join(os.path.dirname(__file__), 'resources')
calibrants_path = os.path.join(resources_path, 'calibrants')
icons_path = os.path.join(resources_path, 'icons')
data_path = os.path.join(resources_path, 'data')
style_path = os.path.join(resources_path, 'style')
diagrams_path = os.path.join(resources_path, 'diagrams')


def user_data_dir() -> str:
    """Return the platform-appropriate local user data directory for Dioptas.

    - Windows : %LOCALAPPDATA%\\Dioptas
    - macOS / Linux : ~/.config/Dioptas
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "Dioptas")