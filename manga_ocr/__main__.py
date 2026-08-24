import fire

import manga_ocr.run
from .patches import apply_patches

def main():
    apply_patches()
    fire.Fire(manga_ocr.run.run)

if __name__ == "__main__":
    main()
