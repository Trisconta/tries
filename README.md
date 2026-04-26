# tryls.py

A lightweight, self-contained directory-listing utility written in Python.  
It provides recursive scanning, optional sorting, dot-file filtering, and a clean, "ls -l"-style output format.  
Designed for portability and clarity, with no external dependencies.

## License

1. [(here)](https://github.com/Trisconta/tries/blob/master/LICENSE) MIT LICENSE

## Features

- Recursive directory scanning using pathlib.Path.rglob
- Optional sorting by modification time
- Optional inclusion/exclusion of dot-files
- Verbose mode with headers and formatted columns
- Graceful handling of permission errors
- Clean, normalized path output (POSIX-style "/")
- Simple command-line interface
- Fully self-contained (no third-party libraries)

## Usage

```bash
python3 tryls.py [options] [path1 ... pathN]
```

Use also in Windows the same way.

## Limitations

Does not detect loops for `rglob`.
