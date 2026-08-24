import fire

# Remove the top-level direct import of 'run'
import manga_ocr.run
from .patches import apply_patches

def main():
    apply_patches()
    # Reference the run function directly through the module namespace
    fire.Fire(manga_ocr.run.run)

if __name__ == "__main__":
    main()
