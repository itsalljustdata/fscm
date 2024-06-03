#!/usr/local/bin/python3

from .fscm import *

from datetime import datetime

try:
    import pretty_errors

    pretty_errors.configure(
        line_color=pretty_errors.BRIGHT_RED,
        exception_color=pretty_errors.BRIGHT_MAGENTA,
        exception_arg_color=pretty_errors.CYAN,
        exception_file_color=pretty_errors.RED_BACKGROUND + pretty_errors.BRIGHT_WHITE,
        display_timestamp=1,
        timestamp_function=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        lines_before=2,
        lines_after=1,
        display_locals=1,
        display_link=1,
    )
except ImportError:  # pretty_errors not installed.
    pass