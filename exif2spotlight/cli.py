""" Read metadata from image files using exiftool and 
write the data to various extended attributes for easy 
searching with Spotlight on MacOS.  Requires exiftool: 
https://exiftool.org/
"""

import os
import pathlib
import re

import click
from osxmetadata import ATTRIBUTES, OSXMetaData
from osxmetadata.constants import (  # _FINDERINFO_NAMES,; _TAGS_NAMES,
    _COLORNAMES_LOWER,
    FINDER_COLOR_NONE,
)

from ._version import __version__
from .exiftool import ExifTool, get_exiftool_path

# if True, shows verbose output, controlled via --verbose flag
VERBOSE = False
CLI_COLOR_ERROR = "red"
CLI_COLOR_WARN = "yellow"

# class CLI_Obj:
#     def __init__(self, debug=False, files=None):
#         self.debug = debug
#         if debug:
#             osxmetadata.debug._set_debug(True)

#         self.files = files


class MyClickCommand(click.Command):
    """Custom click.Command that overrides get_help() to show additional info"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()

        # formatter.write_text(
        #     "Finder tags (tags attribute) contain both a name and an optional color. "
        #     + "To specify the color, append comma + color name (e.g. 'red') after the "
        #     + "tag name.  For example --set tags Foo,red. "
        #     + "Valid color names are: "
        #     + f"{', '.join([color for color, colorid in _COLORNAMES_LOWER.items() if colorid != FINDER_COLOR_NONE])}. "
        #     + "If color is not specified but a tag of the same name has already been assigned a color "
        #     + "in the Finder, the same color will automatically be assigned. "
        # )
        # formatter.write("\n")

        # formatter.write_dl(attr_tuples)
        help_text += formatter.getvalue()
        return help_text


def verbose(message_str, **kwargs):
    if not VERBOSE:
        return
    click.secho(message_str, **kwargs)


def error(error_str):
    click.secho(error_str, err=True, fg="CLI_COLOR_ERROR")


def warn(warn_str):
    click.secho(warn_str, fg="CLI_COLOR_WARN")


@click.command(cls=MyClickCommand)
@click.version_option(__version__, "--version", "-v")
@click.option(
    # add this only so I can show help text via echo_via_pager
    "--help",
    "-h",
    "help_",
    help="Show this message and exit.",
    is_flag=True,
)
@click.option("--verbose", "-V", "verbose_", is_flag=True, help="Show verbose output")
@click.option(
    "--exiftool",
    "exiftool_path",
    type=click.Path(exists=True),
    required=False,
    help="Optionally specify path to exiftool; if not provided, will search for exiftool in $PATH.",
)
@click.option(
    "--walk",
    "-w",
    is_flag=True,
    help="Recursively walk directories and process any files found",
)
@click.argument("files", metavar="FILE", nargs=-1, type=click.Path(exists=True))
@click.pass_context
def cli(ctx, help_, verbose_, exiftool_path, walk, files):

    global VERBOSE
    VERBOSE = verbose_

    if help_ or not files:
        click.echo_via_pager(ctx.get_help())
        ctx.exit(0)

    if not exiftool_path:
        exiftool_path = get_exiftool_path()
    verbose(f"exiftool path: {exiftool_path}")

    click.echo(f"Processing {len(files)} files")
    nullfp = open(os.devnull, "w") if verbose_ else None
    with click.progressbar(files, file=nullfp) as bar:
        for filename in bar:
            file = pathlib.Path(filename)
            if file.is_dir():
                if walk:
                    verbose(f"Processing directory {file}")
                    process_directory(file, exiftool_path)
                else:
                    verbose(f"Skipping directory {file}")
            else:
                verbose(f"Processing file {filename}")
                process_file(filename, exiftool_path)

    if nullfp:
        nullfp.close()


def process_directory(dir, exiftool_path):
    """Process each directory applying exif metadata to extended attributes"""
    for path_object in pathlib.Path(dir).glob("**/*"):
        if path_object.is_file():
            verbose(f"Processing file {path_object}")
            process_file(path_object, exiftool_path)
        elif path_object.is_dir():
            verbose(f"Processing directory {path_object}")
            process_directory(path_object, exiftool_path)


def process_file(filename, exiftool_path):
    """Process each filename applying exif metadata to extended attributes"""
    exiftool = ExifTool(filename, exiftool=exiftool_path)
    exifdict = exiftool.asdict()

    # ExifTool returns dict with tag group names (e.g. IPTC:Keywords)
    # also add the tag names without group name
    exif_no_group = {}
    for k, v in exifdict.items():
        k = re.sub(r".*:", "", k)
        exif_no_group[k] = v
    exifdict.update(exif_no_group)
