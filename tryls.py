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
    do_sort, no_dots = True, False
    param = args
    while param and param[0].startswith("--"):
        if param[0] in ("--no-sort",):
            do_sort = False
            del param[0]
            continue
        if param[0] in ("--no-dots",):
            no_dots = True
            del param[0]
            continue
        return False, None
    target = param[0] if param else None
    scanner = DirectoryScanner(
        SwabName(target).path,
        sort=do_sort,
        dot_files=not no_dots,
    )
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


class SwabName:
    """ Swab a path name! """
    def __init__(self, astr, name="N"):
        self.name = name
        self._ori_str = astr
        self._rigit = False
        self.path = self._build_path(astr)

    def __str__(self):
        return self.path

    def __repr__(self):
        """ Returns a representation of the object. """
        tup = (self.path, None if self._ori_str == self.path else self._ori_str)
        return repr(tup)

    def _build_path(self, astr):
        """ Converts friendly path into a name; if its 'null', we just return None. """
        if astr is None:
            return None
        if self._rigit:
            return astr
        if astr.startswith("~"):
            there = os.path.expanduser(astr)
        else:
            there = astr
        return there


class DirectoryScanner:
    """ Class to handle recursive directory scanning and metadata collection.
    """
    date_format = '%Y-%m-%d %H:%M:%S'
    default_verbose = DEF_VERBOSE

    def __init__(self, target_path=None, sort=True, dot_files=True):
        """ Initializer. """
        self.do_sort = sort	# Sorts automatically by modification time
        self._path = target_path
        self._exclude_dots = not dot_files
        self.verbose = DirectoryScanner.default_verbose
        self._style, self.errors = "", []
        # Fallback to current working directory if no path is provided
        path = Path(target_path) if target_path else Path.cwd()
        if target_path is None:
            self._stt = os.getcwd().replace("\\", "/") + "/"
        else:
            assert SwabName(target_path).path
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
            # Exclude dots if needed
            last = item.parts[-1]
            if last.startswith(".") and self._exclude_dots:
                continue
            ori = str(item)
            try:
                stats = item.stat()
            except (PermissionError, OSError):
                # Skip files/folders with access restrictions
                self.errors.append(f"Permission: {ori}")
                #print("Failed:", ori)
                continue
            shown = ori.replace("\\", "/")
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
        if self.do_sort:
            self.sort_by_mtime()
        return True, ""

    def sort_by_mtime(self):
        """Sorts gathered results by modification time (oldest first)."""
        self.results.sort(key=lambda x: x['mtime'])

    def display(self):
        """ Prints the results in a format similar to 'ls -lG'.
        """
        if self.verbose > 0:
            print(f"{'MODIFIED TIME':<20} {'SIZE (Bytes)':>12} {'PATH'}")
            print("-" * 76)
        for item in self.results:
            astr = self._formatted_item(item)
            print(astr)

    def _formatted_item(self, item):
        """ Returns a string from the name. """
        iso_fmt = DirectoryScanner.date_format
        formatted_time = datetime.fromtimestamp(item['mtime']).strftime(iso_fmt)
        size_label = "<DIR>" if item['is_dir'] else DirectoryScanner._sized(item)
        return f"{formatted_time:<20} {size_label:>12} {item['name']}"

    @staticmethod
    def _sized(item, commas=False):
        """ Returns the size with commas (','), or not. """
        if commas:
            astr = f"{item['size']:,}"
        else:
            astr = f"{item['size']}"
        return astr


if __name__ == "__main__":
    main()
