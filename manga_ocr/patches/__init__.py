from .run_patch import patch as patch_run
from .ImageGrab import patch as patch_image_grab
from .pyperclipinit import patch as patch_pyperclip

def apply_patches():
    patch_run()
    patch_image_grab()
    patch_pyperclip()
