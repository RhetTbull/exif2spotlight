""" Read metadata from image files using exiftool and 
write the data to various extended attributes for easy 
searching with Spotlight on MacOS.  Requires exiftool: 
https://exiftool.org/
"""

import os
import re

import click
from osxmetadata import ATTRIBUTES, OSXMetaData

from ._version import __version__
from .exiftool import ExifTool, get_exiftool_path

from osxmetadata.constants import (  # _FINDERINFO_NAMES,; _TAGS_NAMES,
    _COLORNAMES_LOWER,
    FINDER_COLOR_NONE,
)

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
    """ Custom click.Command that overrides get_help() to show additional info """

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()

        # build help text from all the attribute names
        # get set of attribute names
        # (to eliminate the duplicate entries for short_constant and long costant)
        # then sort and get the short constant, long constant, and help text
        # passed to click.HelpFormatter.write_dl for formatting
        # attr_tuples = [("Short Name", "Description")]
        # attr_tuples.extend(
        #     (
        #         ATTRIBUTES[attr].name,
        #         f"{ATTRIBUTES[attr].short_constant}, "
        #         + f"{ATTRIBUTES[attr].constant}; {ATTRIBUTES[attr].help}",
        #     )
        #     for attr in sorted(
        #         [attr for attr in {attr.name for attr in ATTRIBUTES.values()}]
        #     )
        # )

        # formatter.write("\n\n")
        # formatter.write_text(
        #     "Valid attributes for ATTRIBUTE: "
        #     + "Each attribute has a short name, a constant name, and a long constant name. "
        #     + "Any of these may be used for ATTRIBUTE"
        # )
        # formatter.write("\n")
        # formatter.write_text(
        #     "Attributes that are strings can only take one value for --set; "
        #     + "--append will append to the existing value.  "
        #     + "Attributes that are arrays can be set multiple times to add to the array: "
        #     + "e.g. --set keywords 'foo' --set keywords 'bar' will set keywords to ['foo', 'bar']"
        # )
        # formatter.write("\n")
        # formatter.write_text(
        #     "Options are executed in the following order regardless of order "
        #     + "passed on the command line: "
        #     + "restore, wipe, copyfrom, clear, set, append, update, remove, mirror, get, list, backup.  "
        #     + "--backup and --restore are mutually exclusive.  "
        #     + "Other options may be combined or chained together."
        # )
        # formatter.write("\n")
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


def verbose(message_str):
    if not VERBOSE:
        return
    click.echo(message_str)


def error(error_str):
    click.echo(click.style(error_str, fg="CLI_COLOR_ERROR"))


def warn(warn_str):
    click.echo(click.style(warn_str), fg="CLI_COLOR_WARN")


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
@click.argument("files", metavar="FILE", nargs=-1, type=click.Path(exists=True))
@click.pass_context
def cli(ctx, help_, verbose_, exiftool_path, files):

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
            verbose(f"Processing file {filename}")
            process_file(filename, exiftool_path)

    if nullfp:
        nullfp.close()

def process_file(filename, exiftool_path):
    """ Process each filename applying exif metadata to extended attributes """
    exiftool = ExifTool(filename, exiftool=exiftool_path)
    exifdict = exiftool.asdict()

    # ExifTool returns dict with tag group names (e.g. IPTC:Keywords)
    # also add the tag names without group name
    exif_no_group = {}
    for k, v in exifdict.items():
        k = re.sub(r".*:", "", k)
        exif_no_group[k] = v
    exifdict.update(exif_no_group)