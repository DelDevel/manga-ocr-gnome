import os
import platform
import subprocess
import warnings
import pyperclip

_PYTHON_STR_TYPE = str
ENCODING = 'utf-8'


def init_gpaste_clipboard():
    def copy_gpaste(text, primary=False):
        text = _PYTHON_STR_TYPE(text)  # Converts non-str values to str.

        if not text:
            subprocess.check_call(["gpaste-client", "empty"], close_fds=True)
        else:
            args = ["gpaste-client"]
            p = subprocess.Popen(args, stdin=subprocess.PIPE, close_fds=True)
            p.communicate(input=text.encode(ENCODING))

    def paste_gpaste(primary=False):
        args = ["gpaste-client", "--raw", "--use-index", "get", "0"]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        stdout, _stderr = p.communicate()
        return stdout.decode(ENCODING)

    return copy_gpaste, paste_gpaste


def patched_set_clipboard(clipboard):
    clipboard_types = {
        "pbcopy": pyperclip.init_osx_pbcopy_clipboard,
        "pyobjc": pyperclip.init_osx_pyobjc_clipboard,
        "qt": pyperclip.init_qt_clipboard,
        "xclip": pyperclip.init_xclip_clipboard,
        "xsel": pyperclip.init_xsel_clipboard,
        "wl-clipboard": pyperclip.init_wl_clipboard,
        "gpaste": init_gpaste_clipboard,
        "klipper": pyperclip.init_klipper_clipboard,
        "windows": pyperclip.init_windows_clipboard,
        "no": pyperclip.init_no_clipboard,
    }

    if clipboard not in clipboard_types:
        raise ValueError('Argument must be one of %s' % (', '.join([repr(_) for _ in clipboard_types.keys()])))

    pyperclip.copy, pyperclip.paste = clipboard_types[clipboard]()


def patched_determine_clipboard():
    if 'cygwin' in platform.system().lower():
        if os.path.exists('/dev/clipboard'):
            warnings.warn('Pyperclip\'s support for Cygwin is not perfect, see https://github.com/asweigart/pyperclip/issues/55')
            return pyperclip.init_dev_clipboard_clipboard()

    elif os.name == 'nt' or platform.system() == 'Windows':
        return pyperclip.init_windows_clipboard()

    if platform.system() == 'Linux' and os.path.isfile('/proc/version'):
        with open('/proc/version', 'r') as f:
            if "microsoft" in f.read().lower():
                return pyperclip.init_wsl_clipboard()

    if os.name == 'mac' or platform.system() == 'Darwin':
        try:
            import Foundation
            import AppKit
        except ImportError:
            return pyperclip.init_osx_pbcopy_clipboard()
        else:
            return pyperclip.init_osx_pyobjc_clipboard()

    if os.getenv("XDG_CURRENT_DESKTOP") == "GNOME" and pyperclip._executable_exists("gpaste-client"):
        return init_gpaste_clipboard()

    elif os.getenv("WAYLAND_DISPLAY") and pyperclip._executable_exists("wl-copy") and pyperclip._executable_exists("wl-paste"):
        return pyperclip.init_wl_clipboard()

    elif os.getenv("DISPLAY"):
        if pyperclip._executable_exists("xclip"):
            return pyperclip.init_xclip_clipboard()
        if pyperclip._executable_exists("xsel"):
            return pyperclip.init_xsel_clipboard()
        if pyperclip._executable_exists("klipper") and pyperclip._executable_exists("qdbus"):
            return pyperclip.init_klipper_clipboard()

        try:
            import qtpy
            return pyperclip.init_qt_clipboard()
        except ImportError:
            pass

        try:
            import PyQt5
            return pyperclip.init_qt_clipboard()
        except ImportError:
            pass

    return pyperclip.init_no_clipboard()


def patch():
    pyperclip.init_gpaste_clipboard = init_gpaste_clipboard
    pyperclip.determine_clipboard = patched_determine_clipboard
    pyperclip.set_clipboard = patched_set_clipboard
    pyperclip.copy, pyperclip.paste = pyperclip.determine_clipboard()
