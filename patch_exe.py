import argparse
import sys

from dividedpkg.patch_exe import patch_exe, PatchError

parser = argparse.ArgumentParser()
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--dry-run", "-d", action="store_true")
parser.add_argument("exe", metavar="path/to/Indivisible.exe")
args = parser.parse_args()

try:
	print("Searching for locations...")
	patch_exe(args.exe, args.dry_run, args.verbose)
except PatchError as err:
	print(str(err), file=sys.stderr)
	sys.exit(1)
