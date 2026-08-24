import io
import os
import shutil
import subprocess
import sys
from PIL import BmpImagePlugin, Image, PngImagePlugin, ImageGrab


def patched_grabclipboard() -> Image.Image | list[str] | None:
    if sys.platform == "darwin":
        p = subprocess.run(
            ["osascript", "-e", "get the clipboard as «class PNGf»"],
            capture_output=True,
        )
        if p.returncode != 0:
            return None

        import binascii

        data = io.BytesIO(binascii.unhexlify(p.stdout[11:-3]))
        return Image.open(data)
    elif sys.platform == "win32":
        fmt, data = Image.core.grabclipboard_win32()
        if fmt == "file":  # CF_HDROP
            import struct

            o = struct.unpack_from("I", data)[0]
            if data[16] == 0:
                files = data[o:].decode("mbcs").split("\0")
            else:
                files = data[o:].decode("utf-16le").split("\0")
            return files[: files.index("")]
        if isinstance(data, bytes):
            data = io.BytesIO(data)
            if fmt == "png":
                from PIL import PngImagePlugin

                return PngImagePlugin.PngImageFile(data)
            elif fmt == "DIB":
                from PIL import BmpImagePlugin

                return BmpImagePlugin.DibImageFile(data)
        return None
    else:
        is_gnome = os.getenv("XDG_CURRENT_DESKTOP") == "GNOME"
        if os.getenv("WAYLAND_DISPLAY"):
            session_type = "wayland"
        elif os.getenv("DISPLAY"):
            session_type = "x11"
        else:
            session_type = None

        using_gpaste = False

        if is_gnome and shutil.which("gpaste-client"):
            args = ["gpaste-client", "--raw", "--use-index", "get", "0"]
            using_gpaste = True

        elif shutil.which("wl-paste") and session_type in ("wayland", None):
            args = ["wl-paste", "-t", "image"]

        elif shutil.which("xclip") and session_type in ("x11", None):
            args = ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"]
        else:
            msg = "gpaste-client, wl-paste, or xclip is required for ImageGrab.grabclipboard() on Linux"
            raise NotImplementedError(msg)

        p = subprocess.run(args, capture_output=True)
        if p.returncode != 0:
            err = p.stderr
            for silent_error in [
                b"Nothing is copied",
                b"No selection",
                b"No suitable type of content copied",
                b" not available",
                b"cannot convert ",
                b"xclip: Error: There is no owner for the ",
            ]:
                if silent_error in err:
                    return None
            msg = f"{args[0]} error"
            if err:
                msg += f": {err.strip().decode()}"
            raise ChildProcessError(msg)

        # GPaste Image Routing Logic:
        # Check if GPaste returned an absolute file path to a cached image
        if using_gpaste:
            try:
                # Convert bytes to a clean string path
                file_path = p.stdout.decode('utf-8').strip()

                # Verify it looks like a valid absolute file path pointing to a PNG
                if file_path.startswith("/") and file_path.endswith(".png"):
                    im = Image.open(file_path)
                    im.load()
                    return im
            except Exception:
                pass # If it's not a file path (e.g. text was copied), fall through

        # Standard Fallback (wl-paste / xclip raw binary buffer stream)
        try:
            data = io.BytesIO(p.stdout)
            im = Image.open(data)
            im.load()
            return im
        except Exception:
            return None

def patch():
    ImageGrab.grabclipboard = patched_grabclipboard
