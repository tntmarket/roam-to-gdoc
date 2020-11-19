# Copied from https://github.com/MatthieuBizien/roam-to-git
import json
import zipfile
from pathlib import Path


def get_zip_path(zip_dir_path: Path) -> Path:
    """Return the path to the single zip file in a directory, and fail if there is not one single
    zip file"""
    zip_files = list(zip_dir_path.iterdir())
    zip_files = [f for f in zip_files if f.name.endswith(".zip")]
    assert len(zip_files) == 1, (zip_files, zip_dir_path)
    zip_path, = zip_files
    return zip_path


def unzip_and_save_json_archive(zip_dir_path: Path, directory: Path):
    directory.mkdir(exist_ok=True)
    zip_path = get_zip_path(zip_dir_path)
    with zipfile.ZipFile(zip_path) as zip_file:
        files = list(zip_file.namelist())
        for file in files:
            assert file.endswith(".json")
            content = json.loads(zip_file.read(file).decode())
            with open(directory / file, "w") as f:
                json.dump(content, f, sort_keys=True, indent=2, ensure_ascii=True)
