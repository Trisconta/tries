""" tryls.py

A simple listing script.

(c)2026 Henrique Moreira
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

DEF_VERBOSE = 0


def main():
    """ Main entry point that handles arguments and coordinates the scan.
    """
    # Check if a path was provided as a command-line argument
    tup = do_script(sys.argv[1:])
    _, scanner = tup
    if scanner is None:
        sys.exit(1)
    show_errors(scanner)
    sys.exit(0)

def do_script(args):
    """ Main script! """
    do_sort = True
    param = args
    while param and param[0].startswith("--"):
        if param[0] in ("--no-sort",):
            do_sort = False
            del param[0]
            continue
        return False, None
    target = param[0] if param else None
    scanner = DirectoryScanner(target, sort=do_sort)
    #print(f"Scanning: {scanner.target_path}\n")
    isok, msg = scanner.scan()
    scanner.display()
    return isok, scanner

def show_errors(scanner):
    if not scanner.errors:
        return True
    for idx, err in enumerate(scanner.errors, 1):
        astr = f"Error {idx}/{len(scanner.errors)}: {err}"
        sys.stderr.write(f"{astr}\n")
    return False


class DirectoryScanner:
    """ Class to handle recursive directory scanning and metadata collection.
    """
    date_format = '%Y-%m-%d %H:%M:%S'
    default_verbose = DEF_VERBOSE

    def __init__(self, target_path=None, sort=True):
        """ Initializer. """
        self.do_sort = sort	# Sorts automatically by modification time
        self._path = target_path
        self.verbose = DirectoryScanner.default_verbose
        self._style, self.errors = "", []
        # Fallback to current working directory if no path is provided
        path = Path(target_path) if target_path else Path.cwd()
        if target_path is None:
            self._stt = os.getcwd().replace("\\", "/") + "/"
        else:
            self._stt = str(path).replace("\\", "/") + "/"
            if self._stt.endswith("@/"):
                self._style = "@"
                path = Path(target_path[:-1])
        self.target_path = path
        self.results = []

    def scan(self):
        """ Recursively scans the target path for all files and directories."""
        self.errors = []
        tup = self._scan(self._style)
        return tup

    def _scan(self, style=""):
        """ Interim method for getting the listing. """
        if not self.target_path.exists():
            self.errors = [f"Error: Path '{self.target_path}' does not exist."]
            return False, self.errors[0]
        # Use rglob("*") for recursive scanning of all items
        if style:
            if style in ("@",):
                sets = self.target_path.glob("*")
            else:
                sets = None
        else:
            sets = self.target_path.rglob("*")
        assert sets is not None, f"Wrong doing: {self._path}"
        for item in sets:
            try:
                stats = item.stat()
                shown = str(item).replace("\\", "/")
                ori = shown
                if shown.startswith(self._stt):
                    shown = shown[len(self._stt):]
                tux = "d." if item.is_dir() else "f."
                tux += str(time)
                dct = {
                    'name': shown,
                    'mtime': stats.st_mtime,
                    'size': stats.st_size,
                    'is_dir': item.is_dir(),
                    'tux': tux,
                }
                self.results.append(dct)
            except (PermissionError, OSError):
                # Skip files/folders with access restrictions
                self.errors.append(f"Permission: {ori}")
                print("Failed:", ori)
                continue
        if self.do_sort:
            self.sort_by_mtime()
        return True, ""

    def sort_by_mtime(self):
        """Sorts gathered results by modification time (oldest first)."""
        self.results.sort(key=lambda x: x['mtime'])

    def display(self):
        """ Prints the results in a format similar to 'ls -lG'.
        """
        iso_fmt = DirectoryScanner.date_format
        if self.verbose > 0:
            print(f"{'MODIFIED TIME':<20} {'SIZE (Bytes)':>12} {'PATH'}")
            print("-" * 76)
        for item in self.results:
            formatted_time = datetime.fromtimestamp(item['mtime']).strftime(iso_fmt)
            size_label = "<DIR>" if item['is_dir'] else self._sized(item)
            print(f"{formatted_time:<20} {size_label:>12} {item['name']}")

    def _sized(self, item, commas=False):
        """ Returns the size with commas (','), or not. """
        if commas:
            astr = f"{item['size']:,}"
        else:
            astr = f"{item['size']}"
        return astr


if __name__ == "__main__":
    main()
