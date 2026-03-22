""" tryls.py

A simple listing script.

(c)2026 Henrique Moreira
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path


def main():
    """ Main entry point that handles arguments and coordinates the scan.
    """
    # Check if a path was provided as a command-line argument
    do_script(sys.argv[1:])

def do_script(args):
    param = args
    target = param[0] if param else None
    scanner = DirectoryScanner(target)
    #print(f"Scanning: {scanner.target_path}\n")
    isok, msg = scanner.scan()
    if msg:
        print(msg)
    #scanner.sort_by_mtime()
    scanner.display()
    return scanner


class DirectoryScanner:
    """ Class to handle recursive directory scanning and metadata collection.
    """
    date_format = '%Y-%m-%d %H:%M:%S'

    def __init__(self, target_path=None):
        """ Initializer. """
        self._path = target_path
        # Fallback to current working directory if no path is provided
        path = Path(target_path) if target_path else Path.cwd()
        if target_path is None:
            self._stt = os.getcwd().replace("\\", "/") + "/"
        else:
            self._stt = str(path).replace("\\", "/") + "/"
        if target_path in ("@",):
            self._style = target_path
            path = Path(".")
        else:
            self._style = ""
        self.target_path = path
        self.results = []

    def scan(self):
        """Recursively scans the target path for all files and directories."""
        if not self.target_path.exists():
            return False, f"Error: Path '{self.target_path}' does not exist."
        # Use rglob("*") for recursive scanning of all items
        if self._style:
            sets = self.target_path.glob("*")
        else:
            sets = self.target_path.rglob("*")
        for item in sets:
            try:
                stats = item.stat()
                shown = str(item).replace("\\", "/")
                if shown.startswith(self._stt):
                    shown = shown[len(self._stt):]
                tux = "d." if item.is_dir() else "f."
                tux += str(time)
                self.results.append({
                    'name': shown,
                    'mtime': stats.st_mtime,
                    'size': stats.st_size,
                    'is_dir': item.is_dir(),
                    'tux': tux,
                })
            except (PermissionError, OSError):
                # Skip files/folders with access restrictions
                continue
        return True, ""

    def sort_by_mtime(self):
        """Sorts gathered results by modification time (oldest first)."""
        self.results.sort(key=lambda x: x['mtime'])

    def display(self):
        """ Prints the results in a format similar to 'ls -lG'.
        """
        iso_fmt = DirectoryScanner.date_format
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
