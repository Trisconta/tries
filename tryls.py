""" tryls.py

A simple listing script.

(c)2026 Henrique Moreira
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# pylint: disable=missing-function-docstring

DEF_VERBOSE = 0


def main():
    """ Main entry point that handles arguments and coordinates the scan.
    """
    # Check if a path was provided as a command-line argument
    tup = do_script(sys.argv[1:])
    _, scanners = tup
    if scanners is None:
        usage()
    for scanner in scanners:
        show_errors(scanner)
    sys.exit(0)


def usage():
    myfile = __file__
    print(f"""{os.path.realpath(myfile)} [options] [path1 ...[path2]]

Options are:
   -v			Verbose (or more verbose).
   --no-sorts		Do not sort files.
   --no-dots		Do not show files starting with '.'
""")
    sys.exit(0)


def do_script(args):
    """ Main script! """
    do_sort, no_dots = True, False
    opts = {
        "verbose": 0,
        "sort": do_sort,
        "dot-files": not no_dots,
    }
    param = args
    while param and param[0].startswith("-"):
        if param[0] in ("-v", "--verbose"):
            opts["verbose"] += 1
            del param[0]
            continue
        if param[0] in ("--no-sort",):
            opts["sort"] = False
            del param[0]
            continue
        if param[0] in ("--no-dots",):
            no_dots = True
            del param[0]
            continue
        return False, None
    targets = param if param else None
    isok, scans = do_scans(targets, opts)
    return isok, scans


def do_scans(targets, opts: dict) -> tuple:
    """ Do one path, or several.
    """
    scans = []
    allok = True
    verbose = opts.get("verbose", 0)
    do_sort, dot_files = opts.get("sort", True), opts.get("dot-files", True)
    a_set = [None] if targets is None else targets
    lines = 0
    for target in a_set:
        a_pre = "\n" if lines else ""
        if (verbose > 0 or len(a_set) > 1) and target is not None:
            if verbose > 0:
                print(
                    a_pre + os.path.realpath(target) + ":",
                )
            else:
                print(target, ":")
        scanner = DirectoryScanner(
            SwabName(target).path,
            verbose=verbose,
            sort=do_sort,
            dot_files=dot_files,
        )
        isok, msg = scanner.scan()
        lines += scanner.display()
        if not isok:
            allok = False
        scans.append(scanner)
    return allok, scans


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

    def __init__(self, target_path=None, verbose=None, sort=True, dot_files=True):
        """ Initializer. """
        self.do_sort = sort	# Sorts automatically by modification time
        self._path = target_path
        self._exclude_dots = not dot_files
        self.verbose = DirectoryScanner.default_verbose if verbose is None else int(verbose)
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
        myiter = None
        if style:
            if style in ("@",):
                sets = self.target_path.glob("*")
            else:
                sets = None
        else:
            sets = self.target_path.rglob("*")
        assert sets is not None, f"Wrong doing: {self._path}"
        for item in sets:
            last = item.parts[-1]
            ori = str(item)
            if self._exclude_dots:
                if last.startswith(".") or (
                    str_exclusion(item.parts)
                ):
                    continue
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
            lux = "d." if item.is_dir() else "f."
            tux = lux + str(time)
            dct = {
                'name': shown,
                'mtime': stats.st_mtime,
                'size': stats.st_size,
                'is_dir': item.is_dir(),
                'is_symlink': item.is_symlink(),
                'lux': lux,
                'tux': tux,
                'dir_stat': None if lux == "f." else is_accessible_dir(item)
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
            alen = 2
        else:
            alen = 0
        for item in self.results:
            astr = self._formatted_item(item)
            print(astr)
            alen += 1
        return alen

    def _formatted_item(self, item):
        """ Returns a string from the name. """
        iso_fmt = DirectoryScanner.date_format
        formatted_time = datetime.fromtimestamp(item['mtime']).strftime(iso_fmt)
        if item['dir_stat'] == True:
            size_label = "<DIR{}>".format("-LINK" if item['is_symlink'] else "")
        elif item['dir_stat'] == False:
            size_label = "<DIR.>"
        else:
            size_label = DirectoryScanner._sized(item)
        return f"{formatted_time:<20} {size_label:>12} {item['name']}"

    @staticmethod
    def _sized(item, commas=False):
        """ Returns the size with commas (','), or not. """
        if commas:
            astr = f"{item['size']:,}"
        else:
            astr = f"{item['size']}"
        return astr

def str_exclusion(alist):
    """ Exclusion from a string or list. """
    def in_exclude(astr):
        there = astr.startswith(
            (
                ".",
                "__pycache__",
            )
        )
        return there
    there = any(in_exclude(s) for s in alist)
    return there


def is_accessible_dir(path: Path) -> bool:
    try:
        next(path.iterdir(), None)
        return True
    except PermissionError:
        return False


if __name__ == "__main__":
    main()
