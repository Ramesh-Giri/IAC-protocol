"""Build the static diagram page using only the five public browser assets."""
from pathlib import Path
import shutil


ASSETS = ("index.html", "styles.css", "switch.js", "simple.svg", "complex.svg")


def build():
    root = Path(__file__).resolve().parent
    output = root / "dist"
    if output.is_symlink():
        raise ValueError("Build output must not be a symlink")
    output.mkdir(exist_ok=True)
    unexpected = {p.name for p in output.iterdir()} - set(ASSETS)
    if unexpected:
        raise ValueError("Unexpected files in dist; inspect before building")
    for name in ASSETS:
        source, destination = root / name, output / name
        if source.is_symlink() or destination.is_symlink():
            raise ValueError("Browser assets must not be symlinks")
        shutil.copyfile(source, destination)
    print("Built five public assets in", output)


if __name__ == "__main__":
    build()
