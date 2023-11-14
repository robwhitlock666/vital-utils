from dataclasses import dataclass
from typing import List, Dict
import json
from pathlib import Path
import shutil
from zipfile import ZipFile
import zipfile
import typer

app = typer.Typer()

@dataclass
class Preset:
    name: str
    author: str
    path: Path

from pathlib import Path
def get_presets(input_dir: str):
    p = Path(input_dir)
    return list(p.glob("*.vital"))

def parse_presets(paths: List[Path]) -> List[Preset]:
    return [parse_one_preset(x) for x in paths]

def parse_one_preset(path: Path) -> Preset:
    data = json.loads(path.read_text())
    return Preset(name=data['preset_name'], author=data['author'], path=path.absolute())

def create_user_directories(presets: List[Preset], base_dir: Path):
    new_paths = set([get_user_dir(preset=x, base_dir=base_dir) for x in presets])
    [x.mkdir(parents=True, exist_ok=True) for x in new_paths]
    return list(new_paths)

def get_user_dir(preset: Preset, base_dir: Path):
    author = preset.author
    if author == "":
        author = "Unknown"
    return Path(base_dir, author)


def copy_preset(preset: Preset, base_dir: Path):
    preset_dir = get_preset_dir(preset=preset, base_dir=base_dir)
    preset_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(preset.path), str(preset_dir))

def copy_presets(presets: List[Preset], output_dir: Path):
    [copy_preset(preset=x, base_dir=output_dir) for x in presets]

def get_preset_dir(preset: Preset, base_dir: Path):
    
    return Path(get_user_dir(preset=preset, base_dir=base_dir),'Presets')

def zip_directory(directory_path, output_zip_path):
    directory_path = Path(directory_path)
    output_zip_path = Path(output_zip_path)

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in directory_path.rglob('*'):
            arcname = file_path.relative_to(directory_path.parent)  # Changed this line
            if file_path.is_file():
                zipf.write(file_path, arcname=arcname)
            else:
                zipf.write(file_path, arcname=arcname / '')  # Add directory entry


def make_banks(user_directories: List[Path], output_dir: Path):
    [zip_directory(x, Path(output_dir, f'{x.name}.vitalbank')) for x in user_directories]


@app.command()
def main(presets_dir: str, output_dir: str):
    output_path = Path(output_dir)
    print(output_path)
    print(Path(__file__))
    if output_path == Path(__file__).parent:
        raise Exception("Refusing to delete current directory as output dir")
    
    shutil.rmtree(str(output_path), ignore_errors=True)
    output_path.mkdir(parents=True, exist_ok=True)
    #print(f"Made path {output_path}")
    presets = parse_presets(get_presets(input_dir=presets_dir))
    if not presets:
        raise Exception(f"No .vital presets found in {presets_dir}")
    user_directories = create_user_directories(presets=presets, base_dir=output_path)
    #print(f'Made user dirs: {user_directories}')
    copy_presets(presets=presets, output_dir=output_path)
    banks = Path(output_path, "banks")
    banks.mkdir()
    zip_directory(user_directories[0], Path(banks, f'{user_directories[0].name}.vitalbank'))
    make_banks(user_directories=user_directories, output_dir=banks)

if __name__ == "__main__":
    app()

    