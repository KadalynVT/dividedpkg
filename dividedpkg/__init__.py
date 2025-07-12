#!/usr/bin/env python
# Decryption credits to Ekey
# Unpacking credits to aluigi & Ekey

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from xorcrypt import xor_buffer, xor_parallel

_KEY: bytes|None = None

# Options
CONSOLE = False
CHECK_CONTENTS_BEFORE_BACKUP = True

def get_key():
	global _KEY
	if not _KEY:
		_KEY = (Path(__file__).parent / "key.dat").read_bytes()
	return _KEY


def get_backup_name(original: Path):
	return original.with_stem(original.stem + ".bak")

def check_backup(original: Path):
	backup = original.with_stem(original.stem + ".bak")
	if backup.exists():
		if CONSOLE:
			yn = input("Delete backup (y/n)? ")
			if yn not in "yY":
				raise KeyboardInterrupt()
		backup.unlink()
	return backup


class PKG:
	# Header components
	format: str = "Reverge Package File"
	version: str = "1.1"
	count: int = 0

	# Properties
	filename: Path|None = None
	backed_up = False
	encrypted: bool|None = None

	def __init__(self):
		self.files = dict[str, FileEntry]()

	@classmethod
	def load(cls, fn: str|Path, encrypted: bool|None = None):
		f = open(fn, "rb")
		ret = cls()
		ret.filename = Path(fn)
		key = get_key()
		offset_b = bytearray(f.read(4))

		if encrypted is None:
			# Guess encryption
			f.seek(8, 1)
			format_b = f.read(20)
			f.seek(4)
			encrypted = format_b != b"Reverge Package File"
		ret.encrypted = encrypted

		if encrypted: xor_buffer(offset_b, key, 0)
		offset = int.from_bytes(offset_b)
		header_b = bytearray(f.read(offset - 4))
		if encrypted: xor_buffer(header_b, key, 4)
		header = BytesIO(header_b)

		# Read header information
		format_sz = int.from_bytes(header.read(8))
		ret.format = header.read(format_sz).decode("ascii")
		version_sz = int.from_bytes(header.read(8))
		ret.version = header.read(version_sz).decode("ascii")
		ret.count = int.from_bytes(header.read(8))

		# Read file entries
		for _ in range(ret.count):
			fn_sz = int.from_bytes(header.read(8))
			fn = header.read(fn_sz).decode("ascii")
			sz = int.from_bytes(header.read(8))
			dummy = int.from_bytes(header.read(4))
			ret.files[fn] = FileEntry(fn, sz, dummy, offset)
			offset += sz
		f.close()
		return ret

	@classmethod
	def create(cls, outdir: str|Path, *,
		encrypt=True, file_list: list[str] = [],
		include: list[str] = [], exclude: list[str] = [],
		compress_include: list[str] = [],
		prefer_compressed=False,
	):
		outdir = Path(outdir)
		ret = cls()
		ret.encrypted = encrypt
		ret.format = "Reverge Package File"
		ret.version = "1.1"
		# Offset, length and format, length and version, file count
		offset = 4 + 8 + 20 + 8 + 3 + 8
		for root, _, files in outdir.walk():
			for file in files:
				on_disk = root / file
				file = on_disk.relative_to(outdir)
				fn = file.as_posix()
				compress = False
				if file_list:
					if (fn + ".lz4") in file_list:
						compress = True
					elif not fn in file_list:
						continue
				else:
					if include and not any(file.match(x) for x in include):
						continue
					if any(file.match(x) for x in exclude):
						continue
					compress = any(file.match(x) for x in compress_include)
				data = b""
				if compress:
					from lz4fwrapper import compress_frame
					data = compress_frame(on_disk.read_bytes(), 12)
					fn += ".lz4"
				# Offsets adjusted later
				# TODO: weakref data
				ret.files[fn] = FileEntry(fn, on_disk.stat().st_size, 1, 0, data)
				# Length and filename, size, dummy
				offset += 8 + len(fn) + 8 + 4

		for fn in (file_list or ret.files.keys()):
			file = ret.files[fn]
			file.offset = offset
			offset += file.size
		return ret

	def read(self, fn: str):
		if fn not in self.files:
			raise KeyError(f"{fn} not in file list")
		entry = self.files[fn]
		if not entry.size or entry.data:
			return entry.data
		
		key = get_key()
		with self.filename.open("rb") as f:
			f.seek(entry.offset)
			data = bytearray(f.read(entry.size))
			if self.encrypted:
				xor_buffer(data, key, entry.offset)
			entry.data = bytes(data)
		return entry.data

	def write(self, archive: str|Path = "", outdir: str|Path = ""):
		outpkg = Path(archive) if archive else self.filename
		if not outpkg:
			raise RuntimeError("must specify filename to write to")

		files = sorted(self.files.values(), key=lambda f: f.offset)

		datasrc = self.filename
		if outpkg.exists():
			if not self.backed_up:
				backup = check_backup(outpkg)
				outpkg.rename(backup)
				self.backed_up = True
			else:
				backup = get_backup_name(outpkg)

			if outpkg.samefile(self.filename):
				datasrc = backup

		self.filename = outpkg

		key = get_key()
		def fetch(entry: FileEntry, offset: int):
			if entry.data:
				data = bytearray(entry.data)
				entry.size = len(data)  # just to be safe
			elif outdir:
				infile = Path(outdir) / entry.name
				if infile.suffix == ".lz4":
					from lz4fwrapper import compress_frame
					data = bytearray(compress_frame(infile.with_suffix("").read_bytes(), 12))
				else:
					data = bytearray(infile.read_bytes())
				entry.size = len(data)
			else:
				with datasrc.open("rb") as f:
					data = bytearray(f.seek(entry.offset).read(entry.size))
					if self.encrypted:
						xor_parallel(data, key, entry.offset)
			
			if self.encrypted:
				xor_parallel(data, key, offset)
			entry.offset = offset
			return data

		with outpkg.open("wb") as f:
			# Write header
			header_b = bytearray(
				(0).to_bytes(4, "big")
				+ len(self.format).to_bytes(8, "big")
				+ self.format.encode("ascii")
				+ len(self.version).to_bytes(8, "big")
				+ self.version.encode("ascii")
				+ len(self.files).to_bytes(8, "big")
			)
			if self.encrypted:
				xor_buffer(header_b, key, 0)
			f.write(header_b)
			
			offset = f.tell()
			if files:
				# Write file listing
				entry_size_offset = []
				for file in files:
					entry_b = bytearray(
						len(file.name).to_bytes(8, "big")
						+ file.name.encode("ascii")
						+ file.size.to_bytes(8, "big")
						+ file.dummy.to_bytes(4, "big")
					)
					if self.encrypted:
						xor_buffer(entry_b, key, offset)
					f.write(entry_b)
					offset = f.tell()
					entry_size_offset.append(offset - 12)

			# Write offset
			f.seek(0)
			offset_b = bytearray(offset.to_bytes(4, "big"))
			if self.encrypted:
				xor_buffer(offset_b, key, 0)
			f.write(offset_b)
			if not files:
				return offset
			f.seek(offset)

			# Write file data
			size_changed = list[int]()
			for i, file in enumerate(files):
				pre_size = file.size
				f.write(fetch(file, offset))
				offset += file.size
				if pre_size != file.size:
					size_changed.append(i)

			# Re-write file sizes
			for i in size_changed:
				sz_offset = entry_size_offset[i]
				f.seek(sz_offset)
				size_b = bytearray(files[i].size.to_bytes(8, "big"))
				if self.encrypted:
					xor_buffer(size_b, key, sz_offset)
				f.write(size_b)

			return offset

	def export(self, fn: str, outdir: str|Path, decompress=True):
		outdir = Path(outdir)
		data = self.read(fn)
		entry = self.files[fn]
		fp = outdir / entry.name
		if decompress and fp.suffix == ".lz4":
			fp = fp.with_suffix("")
			from lz4fwrapper import decompress_frame
			data = decompress_frame(data)
		if fp.exists():
			if not CHECK_CONTENTS_BEFORE_BACKUP or fp.read_bytes() != data:
				fp.rename(check_backup(fp))
		else:
			fp.parent.mkdir(exist_ok=True, parents=True)
		fp.write_bytes(data)

	def export_all(self, outdir: str|Path,
		include: list[str] = [], exclude: list[str] = [],
		decompress = True
	):
		outdir = Path(outdir)
		exported = 0
		if not self.files:
			return exported
		# Get first offset and read whole file into memory
		offset = min(x.offset for x in self.files.values())
		key = get_key()
		with self.filename.open("rb") as f:
			f.seek(offset)
			data = bytearray(f.read())
			if self.encrypted:
				xor_parallel(data, key, offset)
		f = BytesIO(data)
		for fn, entry in self.files.items():
			file = Path(fn)
			if include and not any(x in fn or file.match(x) for x in include):
				continue
			if any(file.match(x) for x in exclude):
				continue
			f.seek(entry.offset - offset)
			entry.data = f.read(entry.size)
			self.export(fn, outdir, decompress=decompress)
			exported += 1
		return exported
	
	def import1(self, fn: str, outdir: str|Path, prefer_compressed=False):
		outdir = Path(outdir)
		if fn not in self.files:
			raise KeyError(f"{fn} not in file list")
		entry = self.files[fn]

		# Get file to import
		infile = outdir / entry.name
		if infile.suffix == ".lz4" and not (prefer_compressed and infile.exists()):
			from lz4fwrapper import compress_frame
			data = bytearray(compress_frame(infile.with_suffix("").read_bytes(), 12))
		else:
			data = bytearray(infile.read_bytes())

		if not self.backed_up:
			backup = check_backup(self.filename)
			self.filename.rename(backup)
			self.backed_up = True
		else:
			backup = get_backup_name(self.filename)
		
		key = get_key()
		with backup.open("rb") as fin, self.filename.open("wb") as fout:
			offset = next(iter(self.files.values())).offset
			header = BytesIO()
			header.write(offset.to_bytes(4))
			header.write(len(self.format).to_bytes(8))
			header.write(self.format.encode("ascii"))
			header.write(len(self.version).to_bytes(8))
			header.write(self.version.encode("ascii"))
			header.write(self.count.to_bytes(8))
			for k, v in self.files.items():
				header.write(len(k).to_bytes(8))
				header.write(k.encode("ascii"))
				sz = len(data) if k == fn else v.size
				header.write(sz.to_bytes(8))
				header.write(v.dummy.to_bytes(4))
			header = bytearray(header.getbuffer())
			if self.encrypted:
				xor_parallel(header, key, 0)
			fout.write(header)
			assert fout.tell() == offset

			# Write data
			fin.seek(offset)
			intro = fin.read(entry.offset - offset)
			fout.write(intro)
			fin.seek(entry.size, 1)
			outro_offset = fin.tell()
			outro = bytearray(fin.read())
			if self.encrypted:
				xor_parallel(outro, key, outro_offset)  # decrypt
			assert fout.tell() == entry.offset
			if self.encrypted:
				xor_parallel(data, key, fout.tell())
			fout.write(data)
			if self.encrypted:
				xor_parallel(outro, key, fout.tell())  # encrypt
			fout.write(outro)


@dataclass
class FileEntry:
	# Part of the table
	name: str
	size: int
	dummy: int  # version? count? always(?) 1

	# Extra info
	offset: int
	data: bytes = b""
