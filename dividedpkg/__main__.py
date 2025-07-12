
import argparse
import sys
from pathlib import Path

from . import *

def crypt(src: Path, dest: Path):
	key = get_key()
	if dest.is_dir():
		dest /= src.with_stem(src.stem + "_decrypted")
	data = bytearray(src.read_bytes())
	xor_parallel(data)
	dest.write_bytes(data, key, 0)

def decrypt(src: Path, dest: Path):
	if dest.is_dir():
		dest /= src.with_stem(src.name.replace("_encrypted", "") + "_decrypted")
	print(f"Decrypting {src} to {dest}")
	crypt(src, dest)

def encrypt(src: Path, dest: Path):
	if dest.is_dir():
		if src.name.endswith("_decrypted"):
			dest /= src.name.replace("_decrypted", "")
		else:
			dest /= src.with_stem(src.stem + "_encrypted")
	print(f"Encrypting {src} to {dest}")
	crypt(src, dest)

parser = argparse.ArgumentParser("DividedPKG", description="Packer and unpacker for Indivisible game")
group = parser.add_mutually_exclusive_group()
group.add_argument("--unpack", "-u", action="store_true",
	help="Unpack the given pkg file(s) to the given directory")
group.add_argument("--pack", "-p", action="store_true",
	help="Pack the given directory or file(s) into the given pkg file")
group.add_argument("--list", "-l", action="store_true",
	help="List the contents of the given pkg file(s)")
gcrypt = parser.add_mutually_exclusive_group()
gcrypt.add_argument("--decrypt", "-d", action="store_true",
	help="Decrypt the given pkg file(s)")
gcrypt.add_argument("--encrypt", "-e", action="store_true",
	help="Encrypt the given pkg file(s)")
gcompress = parser.add_mutually_exclusive_group()
gcompress.add_argument("--compress", "-C", action="store_true",
	help=argparse.SUPPRESS)
gcompress.add_argument("--uncompress", "-U", action="store_true",
	help=argparse.SUPPRESS)
parser.add_argument("--include", "-i", action="append",
	help="Include only files which match this glob (can be specified multiple times)")
parser.add_argument("--exclude", "-x", action="append",
	help="Exclude any files which match this glob (can be specified multiple times)")
parser.add_argument("--compress-include", "-c", action="append",
	help=("Compress files which match this glob (can be specified multiple times). "
		"Only used with --pack when creating a pkg file from scratch."))
parser.add_argument("src", nargs="*", type=Path)
parser.add_argument("dest", type=Path)
args = parser.parse_args()

include = list[str](args.include or [])
exclude = list[str](args.exclude or [])
compress_include = list[str](args.compress_include or [])
src = list[Path](args.src or [])
dest = Path(args.dest)
encrypted = args.encrypt if args.decrypt is None else not args.decrypt

try:
	if args.list:
		print_filename = bool(src)
		for pkg_fn in [*src, dest]:
			pkg = PKG.load(dest, encrypted=encrypted)
			if print_filename:
				print("# {pkg_fn}:")
			print(f"{'offset':18s}, {'size':10s}, name")
			for entry in pkg.files.values():
				file = Path(entry.name)
				if (
					(not include or any(file.match(x) for x in include))
					and not any(file.match(x) for x in exclude)
				):
					print(f"0x{entry.offset:016x}, 0x{entry.size:08x}, {entry.name}")
		sys.exit(0)
	elif args.pack:
		outdir = ""
		if dest.is_file():
			pkg = PKG.load(dest)
			if len(src) == 1 and src[0].is_file():
				ssrc = src[0].as_posix()
				for fn in pkg.files.keys():
					fn2 = fn.removesuffix(".lz4")
					if ssrc.endswith(fn2):
						outdir = ssrc[:-len(fn2)]
						pkg.import1(fn, outdir)
						print(f"Imported 1 file into {dest}")
						sys.exit(0)
				raise FileNotFoundError(f"Could not find file in pkg: {ssrc}")
		elif len(src) > 1 or src and src[0].is_file():
			import os.path
			outdir = Path(os.path.commonpath(src))
			# TODO?: expand directories
			pkg = PKG.create(outdir, encrypt=not args.decrypt,
				file_list=[x.relative_to(outdir).as_posix() for x in src])
		elif src:
			outdir = src[0]
			pkg = PKG.create(outdir, encrypt=not args.decrypt,
				include=include, exclude=exclude, compress_include=compress_include)
		elif dest.is_dir():
			outdir = dest
			dest = dest.with_suffix(".pkg")
			pkg = PKG.create(outdir, encrypt=not args.decrypt,
				include=include, exclude=exclude, compress_include=compress_include)
		else:
			print("Dunno what to pack", file=sys.stderr)
			sys.exit(1)
		pkg.write(dest, outdir)
		print(f"Wrote {len(pkg.files)} to {dest}")
		sys.exit(0)
	elif not args.unpack:
		if args.compress:
			from lz4fwrapper import compress_frame
			count = 0
			for file in [*src, dest]:
				file.with_suffix(file.suffix + ".lz4").write_bytes(
					compress_frame(file.read_bytes(), 12))
				count += 1
			print(f"Compressed {count} files")
			sys.exit(0)
		elif args.uncompress:
			from lz4fwrapper import decompress_frame
			for file in [*src, dest]:
				try:
					data = decompress_frame(file.read_bytes())
				except:
					print(f"Failed to decompress file: {file}")
					continue
				if file.suffix == ".lz4":
					file.with_suffix("").write_bytes(data)
				else:
					file.with_stem(file.stem + "_decompressed").write_bytes(data)
			sys.exit(0)

	add_name = False
	if len(src) > 1:
		if not dest.is_dir():
			print("Destination must be a directory when there are multiple sources", file=sys.stderr)
			sys.exit(1)
		add_name = True

	s: Path
	if args.unpack:
		if not src:
			src = [dest]
			dest = dest.with_suffix("")
		for s in src:
			out = dest / s.with_suffix("") if add_name else dest
			out.mkdir(exist_ok=True)
			PKG.load(s, encrypted=encrypted).export_all(out, include, exclude, decompress=not args.compress)
	elif args.decrypt:
		for s in src:
			decrypt(s, dest / s.with_suffix("") if add_name else dest)
	elif args.encrypt:
		for s in src:
			encrypt(s, dest / s.with_suffix("") if add_name else dest)
except FileNotFoundError as err:
	print(str(err), file=sys.stderr)
	sys.exit(2)
except (InterruptedError, EOFError):
	print("\nCancelled by user", file=sys.stderr)
