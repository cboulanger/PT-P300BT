"""Entry point for `uv run print "My label"`.

Thin wrapper around printlabel.py (which is left untouched, as upstream) that
offers --port and --font options with defaults in place of its COM_PORT and
FONT_NAME positionals, so only the text (and any options) need to be given.
Every printlabel.py option is passed through unchanged.

Progress and printer status output is suppressed unless --verbose is given, and
errors are reported as a one-line message on stderr (exit status 1) instead of
a traceback.

Defaults (overridable with the options below or the environment variables):
    --port  / LABEL_PORT   printer target   (default: bt:PT-P300)
    --font  / LABEL_FONT   font file path   (default: Arial on macOS, else arial.ttf)
"""
import argparse
import os
import sys

DEFAULT_PORT = "bt:PT-P300"
_MACOS_ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
DEFAULT_FONT = _MACOS_ARIAL if os.path.exists(_MACOS_ARIAL) else "arial.ttf"


def _wrapper_parser():
    # No abbreviations: "--f" must not be taken for "--font" here, since other
    # options are meant for printlabel.py.
    p = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    p.add_argument("--port", default=os.environ.get("LABEL_PORT", DEFAULT_PORT))
    p.add_argument("--font", default=os.environ.get("LABEL_FONT", DEFAULT_FONT))
    p.add_argument("--verbose", action="store_true")
    return p


def _print_help(port, font):
    import printlabel

    print(
        'usage: print [--port PORT] [--font FONT] [--verbose] [printlabel options] "TEXT"\n'
        "\n"
        "Print a label on a Brother PT-P300BT. Use \\n in TEXT for line breaks.\n"
        "Silent on success; errors are reported as a single line.\n"
        "\n"
        "  --verbose     show progress and printer status while printing\n"
        "\n"
        "defaults (override with the option or the environment variable):\n"
        f"  --port PORT   printer target [LABEL_PORT]  (default: {port})\n"
        f"  --font FONT   font file path [LABEL_FONT]  (default: {font})\n"
        "\n"
        "examples:\n"
        '  uv run print "Hello"\n'
        '  uv run print "Top\\nBottom"\n'
        '  uv run print --font /path/to/Font.ttf "Custom font"\n'
        '  uv run print -n -S /tmp/preview.png "Preview only"\n'
        "\n"
        "All other options are those of printlabel.py, listed below. Its COM_PORT\n"
        "and FONT_NAME positionals are filled in by this command, so give only the\n"
        "text; use --port and --font to change them.\n"
        "\n"
        "--- printlabel.py options ---\n"
    )
    printlabel.set_args().print_help()


def _run(quiet):
    import contextlib
    import io

    import printlabel

    # Progress and printer status go to stdout; when quiet, hold them back and
    # only show the "** ..." failure lines if the job fails. Command line
    # errors go to stderr as a usage block followed by "prog: error: ...";
    # hold that back too and show only the error.
    out, err = io.StringIO(), io.StringIO()
    code = 0
    try:
        with contextlib.ExitStack() as stack:
            if quiet:
                stack.enter_context(contextlib.redirect_stdout(out))
                stack.enter_context(contextlib.redirect_stderr(err))
            printlabel._run_gui()
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
        code = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        code = 1
    if code:
        for line in out.getvalue().splitlines():
            if line.startswith("**"):
                print(line, file=sys.stderr)
        lines = err.getvalue().splitlines()
        start = next((i for i, l in enumerate(lines) if ": error:" in l), None)
        if start is not None:
            print("\n".join(lines[start:]), file=sys.stderr)
    return code


def main():
    opts, rest = _wrapper_parser().parse_known_args()
    if not rest or any(a in ("-h", "--help") for a in rest):
        _print_help(opts.port, opts.font)
        return

    # printlabel.py takes COM_PORT and FONT_NAME as positionals (TEXT...
    # follows); they must come first so that options such as --list-ligatures
    # don't swallow them.
    sys.argv = [sys.argv[0], opts.port, opts.font, *rest]

    # These commands exist to print information, so never silence them.
    informational = any(
        a == "--list-bt" or a.startswith("--list-ligatures") for a in rest
    )
    sys.exit(_run(quiet=not (opts.verbose or informational)))


def gui():
    """Entry point for `uv run gui`: launch the Tkinter GUI."""
    sys.argv = [sys.argv[0], "--gui"]
    sys.exit(_run(quiet=False))


if __name__ == "__main__":
    main()
