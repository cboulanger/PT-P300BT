# `print` — a command-line shortcut for printing labels

`print` is a small wrapper around [`printlabel.py`](printlabel.py) that turns
label printing into a one-liner:

```bash
uv run print "Hello World"
```

It fills in the printer and the font from defaults, stays silent when
everything works, and reports a failure as a single readable line instead of a
Python traceback. Everything else `printlabel.py` can do is still available
through it.

## Why

`printlabel.py` is a complete label maker, but it is built for scripted use
and expects the printer port and the font as positional arguments on every
call:

```bash
uv run python printlabel.py "bt:PT-P300" "/System/Library/Fonts/Supplemental/Arial.ttf" "Hello World"
```

It also prints the whole conversation with the printer (status dumps, a
progress bar), and any error ends in a stack trace. That is useful when
debugging and noisy when all you want is a label. `print` handles this for
day-to-day use.

The wrapper is deliberately separate from `printlabel.py`, which is not
modified. That keeps it easy to merge upstream changes.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- A Brother PT-P300BT, switched on and paired with your computer. On macOS the
  default `bt:PT-P300` target uses the native Bluetooth bridge described in
  [native/README.md](native/README.md).

Nothing else needs to be installed by hand. The first `uv run print ...`
creates `.venv` and installs the dependencies (Python 3.12 or newer, Pillow,
pyserial, fontTools and the others listed in [pyproject.toml](pyproject.toml)).

## Quick start

```bash
git clone https://github.com/cboulanger/PT-P300BT
cd PT-P300BT
uv run print "Hello World"
```

Running `uv run print` with no arguments (or with `--help`) shows the help.

## Usage

```text
uv run print [--port PORT] [--font FONT] [--verbose] [printlabel options] TEXT...
```

`TEXT` is the label text. Several arguments are joined with spaces, and a
literal `\n` starts a new line. Options can go before or after the text.

### Options of the wrapper

| Option | Environment variable | Default |
| --- | --- | --- |
| `--port PORT` | `LABEL_PORT` | `bt:PT-P300` |
| `--font FONT` | `LABEL_FONT` | Arial (`/System/Library/Fonts/Supplemental/Arial.ttf`) on macOS, otherwise `arial.ttf` |
| `--verbose` | | off |

- **`--port`** is the printer target: `bt:NAME` for native Bluetooth on
  macOS, or a serial port such as `COM7` or `/dev/rfcomm0`.
- **`--font`** is the path of a TrueType or OpenType font file.
- **`--verbose`** shows the progress messages and the printer status that are
  normally hidden.

A value given on the command line wins over the environment variable, which
wins over the built-in default.

### Options of `printlabel.py`

Any other option is passed through unchanged, so all of these work as
documented in the main [README](README.md): `-M` to merge an image or PDF,
`-H` and `--stroke-width` for bold text, `--fixed-width`, `--tape-width`,
`-n` (do not print), `-S` (save the image), `-s` (show the image),
`--ligatures` and so on. `uv run print --help` prints the wrapper's own
section followed by the complete list.

## Examples

Print a label, or a two-line label (the font shrinks to fit):

```bash
uv run print "Hello World"
uv run print "Top\nBottom"
```

Use a different font or printer for one label:

```bash
uv run print --font "/System/Library/Fonts/Supplemental/Courier New.ttf" "Courier"
uv run print --port bt:PT-P300 "Explicit printer"
```

Set your own defaults, for example in `~/.zshrc`:

```bash
export LABEL_PORT=bt:PT-P300
export LABEL_FONT="$HOME/Library/Fonts/MyFont.ttf"
```

Check how a label will look without printing it (`-n` skips printing, `-S`
saves the image, `-s` opens it):

```bash
uv run print -n -S /tmp/preview.png "Preview only"
uv run print -n -s "Show it on screen"
```

Use `printlabel.py` options:

```bash
uv run print -H --stroke-width 2 "Bold"
uv run print -M resources/happy-sun.pdf "With an icon"
uv run print --fixed-width 40 "Exactly 40 mm"
```

Watch what is going on while printing:

```bash
uv run print --verbose "Hello World"
```

List paired Bluetooth devices, or the OpenType features of a font (these
commands print information, so they are never silenced):

```bash
uv run print --list-bt
uv run print --list-ligatures "Fira Code"
```

Run it from another directory:

```bash
uv run --project /path/to/PT-P300BT print "Hello World"
```

Relative paths (such as an image for `-M`) are resolved from the directory
you run the command in.

## Behaviour

**Silent on success.** Progress messages, the printer status dumps and the
progress bar are hidden, and so are non-fatal warnings. Use `--verbose` to see
them.

**One-line errors.** If something goes wrong, the message goes to stderr and
the command exits with a non-zero status, with no traceback:

```text
error: Printer reported an error: Low battery
```

```text
error: Cannot load font "/nope.ttf" - cannot open resource
```

When the printer refuses a job or does not answer, its own `** ...` message is
shown as well.

**Exit status.**

| Status | Meaning |
| --- | --- |
| `0` | Success |
| `1` | The job failed (printer error, unreadable font or image, and similar) |
| `2` | Invalid command line, or the printer could not be reached (reported by `printlabel.py`) |
| `130` | Interrupted with Ctrl-C |

This makes `print` usable in scripts: `uv run print "Done" || echo "Label
failed"`.

Status `2` errors come from `printlabel.py`'s argument handling, for example
`print: error: unrecognized arguments: --bogus`. Its usage text, which normally
precedes such a message, is hidden unless `--verbose` is given.

## How it works

[`printcmd.py`](printcmd.py) is registered as the `print` script in
[pyproject.toml](pyproject.toml). When run, it:

1. Reads `--port`, `--font` and `--verbose` (falling back to the environment
   variables and defaults) and leaves all other arguments alone.
2. Calls `printlabel.py` as `printlabel.py PORT FONT <your arguments>`. The
   port and font go first so that an option such as `--list-ligatures`, which
   takes an optional value, cannot swallow them.
3. Unless `--verbose` (or `--list-bt` / `--list-ligatures`) is given, collects
   what `printlabel.py` writes to standard output and standard error. If the
   job fails, it shows only the `** ...` lines from the former and the
   `prog: error: ...` message (without the usage text) from the latter.
4. Turns any exception into `error: <message>` on stderr with exit status 1.

The wrapper's own options must be spelled out in full; abbreviations such as
`--f` are not accepted, so they cannot be confused with options of
`printlabel.py`.

## Troubleshooting

- **`print: command not found`, or nothing is printed.** Run it as
  `uv run print`. In zsh, a bare `print` is a shell built-in and takes
  precedence over the script, even when the virtual environment is activated.
- **`Printer reported an error: Low battery`** (or another printer error). The
  message comes from the printer. Fix the cause and run again, or add
  `--verbose` to see the full status exchange.
- **The printer is not found.** Check that it is on and paired, and that
  `uv run print --list-bt` lists it. If your printer has a different name,
  pass it with `--port bt:NAME`.
- **`Cannot load font`.** The `--font` path is wrong, or the default font does
  not exist on this system. Set `LABEL_FONT` or pass `--font`.
- **Something looks wrong and there is no output.** Add `--verbose`. Warnings,
  for example about text that does not fit, are hidden otherwise.

To use the original interface directly:

```bash
uv run python printlabel.py "bt:PT-P300" "/System/Library/Fonts/Supplemental/Arial.ttf" "Hello World"
```
