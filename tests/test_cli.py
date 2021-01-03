""" tests for exif2spotlight CLI """

import pathlib
import shutil

import pytest
from click.testing import CliRunner

TEST_IMAGES_DIR = "tests/test_images"
TEST_FILE_WARNING = "exiftool_warning.heic"
TEST_FILE_BADFILE = "badimage.jpeg"
TEST_FILE_WRONG_FILETYPE = "not-a-jpeg-really-a-png.jpeg"
TEST_FILE_1 = "jackrose.jpeg"
TEST_FILE_2 = "statue.jpg"


def copy_test_files(dest, source=None):
    """ copy test images to temp directory, returns list of files copied """
    if source is None:
        source = pathlib.Path("tests/test_images")
    else:
        source = pathlib.Path(source)
    
    files_copied = []
    for source_file in source.glob("*"):
        dest_file = pathlib.Path(dest) / source_file.name
        shutil.copy2(str(source_file), str(dest_file))
        files_copied.append(dest_file)
    return files_copied


def test_help_1():
    """ test help shown if called with no options """
    from exif2spotlight.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, [])
    output = result.output

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "[OPTIONS] FILE" in result.output


def test_help_2():
    """ test help shown if called --help option """
    from exif2spotlight.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    output = result.output

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "[OPTIONS] FILE" in result.output


def test_verbose():
    """ test --verbose """
    from exif2spotlight.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--verbose"])
    output = result.output

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "[OPTIONS] FILE" in result.output


def test_exiftool():
    """ test --exiftool option """
    import os
    import shutil

    from exif2spotlight.cli import cli
    from exif2spotlight.exiftool import get_exiftool_path

    runner = CliRunner()
    cwd = pathlib.Path(os.getcwd())
    # pylint: disable=not-context-manager
    with runner.isolated_filesystem():
        test_dir = pathlib.Path(os.getcwd())
        copy_test_files(str(test_dir), source=str(cwd / TEST_IMAGES_DIR))
        exiftool_source = get_exiftool_path()
        exiftool_path = test_dir / "myexiftool"
        shutil.copy2(exiftool_source, exiftool_path)
        result = runner.invoke(
            cli, ["--verbose", "--exiftool", exiftool_path, str(test_dir / TEST_FILE_1)]
        )
        assert result.exit_code == 0
        assert f"exiftool path: {exiftool_path}" in result.output
