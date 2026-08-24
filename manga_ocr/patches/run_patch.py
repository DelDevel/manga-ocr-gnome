import manga_ocr.run as original_run
from . import ImageGrab
from PIL import Image
from PIL import UnidentifiedImageError

def patched_run(
    read_from="clipboard",
    write_to="clipboard",
    pretrained_model_name_or_path="kha-white/manga-ocr-base",
    force_cpu=False,
    delay_secs=0.1,
    verbose=False,
):
    """
    Patched version of manga_ocr.run.run.
    """
    MangaOcr = original_run.MangaOcr
    sys = original_run.sys
    time = original_run.time
    Path = original_run.Path
    pyperclip = original_run.pyperclip
    logger = original_run.logger
    process_and_write_results = original_run.process_and_write_results
    are_images_identical = original_run.are_images_identical
    get_path_key = original_run.get_path_key

    mocr = MangaOcr(pretrained_model_name_or_path, force_cpu)

    if sys.platform not in ("darwin", "win32") and write_to == "clipboard":
        import os
        import shutil

        # 1. Check if the environment is GNOME first
        if os.environ.get("XDG_CURRENT_DESKTOP") == "GNOME":
            if shutil.which("gpaste-client"):
                pyperclip.set_clipboard("gpaste")  # Or your custom registered backend name
                logger.info("Using gpaste")
            else:
                msg = (
                    "Your session uses GNOME and does not have gpaste installed. "
                    "Install gpaste for clipboard writing to work."
                )
                raise NotImplementedError(msg)

        # 2. Fallback: Check if the system is using Wayland (Non-GNOME)
        elif os.environ.get("WAYLAND_DISPLAY"):
            if shutil.which("wl-copy"):
                pyperclip.set_clipboard("wl-clipboard")
                logger.info("Using wl-clipboard")
            else:
                msg = (
                    "Your session uses Wayland and does not have wl-clipboard installed. "
                    "Install wl-clipboard for clipboard writing to work."
                )
                raise NotImplementedError(msg)

    if read_from == "clipboard":

        logger.info("Reading from clipboard")

        img = None
        while True:
            old_img = img

            try:
                img = ImageGrab.patched_grabclipboard()
            except OSError as error:
                if not verbose and "cannot identify image file" in str(error):
                    # Pillow error when clipboard hasn't changed since last grab (Linux)
                    pass
                elif not verbose and "target image/png not available" in str(error):
                    # Pillow error when clipboard contains text (Linux, X11)
                    pass
                else:
                    logger.warning("Error while reading from clipboard ({})".format(error))
            else:
                if isinstance(img, Image.Image) and not are_images_identical(img, old_img):
                    process_and_write_results(mocr, img, write_to)

            time.sleep(delay_secs)

    else:
        read_from = Path(read_from)
        if not read_from.is_dir():
            raise ValueError('read_from must be either "clipboard" or a path to a directory')

        logger.info(f"Reading from directory {read_from}")

        old_paths = set()
        for path in read_from.iterdir():
            old_paths.add(get_path_key(path))

        while True:
            for path in read_from.iterdir():
                path_key = get_path_key(path)
                if path_key not in old_paths:
                    old_paths.add(path_key)

                    try:
                        img = Image.open(path)
                        img.load()
                    except (UnidentifiedImageError, OSError) as e:
                        logger.warning(f"Error while reading file {path}: {e}")
                    else:
                        process_and_write_results(mocr, img, write_to)

            time.sleep(delay_secs)

def patch():
    original_run.run = patched_run
