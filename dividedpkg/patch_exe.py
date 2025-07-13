import sys
from pathlib import Path

from pefile import PE


class PatchError(Exception): pass


def patch_exe(exe: str|Path, dry_run=False, verbose=False):
	can_ask_user = sys.stdin.isatty()
	exe = Path(exe)
	if exe.is_dir():
		exe /= "Indivisible.exe"

	if not exe.exists():
		raise PatchError(f"File not found {exe}")

	if can_ask_user and exe.name != "Indivisible.exe":
		yn = input("Warning: expecting to modify Indivisible.exe, continue? ")
		if yn not in "yY":
			sys.exit(0)

	pe = PE(exe)
	data = bytearray(pe.get_memory_mapped_image())
	err1 = data.find(b"HashFile returned an error...\n")
	err2 = data.find(b"VerifyHash returned an error...\n")
	err3 = data.find(b"VerifyHash reports signature verification failed!\n")
	test = data.find(b"\x48\x8d\x0d")
	found = 0
	call_loc = 0
	replacements = list[tuple[bytes, bytes]]()
	patched = list[int]()

	def get_u4(addr: int):
		return int.from_bytes(data[addr:addr+4], "little", signed=True)

	while test >= 0 and found < 3:
		if data[test+7] == 0xe8:
			# CALL
			offset = get_u4(test+3)
			address = test + 7 + offset
			if address in (err1, err2, err3):
				found += 1
				if verbose:
					print(f"  found {found} at virtual address ${test:08x}")
				cl = test + 12 + get_u4(test+8)
				if not call_loc:
					call_loc = cl
				elif call_loc != cl:
					raise ValueError("call was to an unexpected function")
				value_code = identify_return_value(data, test+12)
				if value_code:
					replacements.append((
						data[test:test+12],
						value_code
					))
				else:
					patched.append(test+12)
		test = data.find(b"\x48\x8d\x0d", test+7)
	pe.close()
	del pe
	assert len(replacements) + len(patched) == 3

	if replacements:
		if dry_run:
			backup = exe
		else:
			backup = exe.with_suffix(exe.suffix + ".bak")
			if backup.exists():
				if not can_ask_user:
					raise PatchError("backup exists but patch isn't applied")
				yn = input("Warning: backup already exists, overwrite? ")
				if yn in "yY":
					backup.unlink(True)
					exe.rename(backup)
				else:
					print("Warning: proceeding without backup", file=sys.stderr)
			else:
				exe.rename(backup)

		# pefile won't do a minimal write-back so we do it ourselves
		data = bytearray(backup.read_bytes())
		for s, r in replacements:
			pos = data.find(s) + len(s)
			print(f"Replacement at ${pos:08x}: {r.hex(' ')}")
			data[pos:pos+len(r)] = r
		for addr in patched:	
			print(f"Patch already found at ${addr:08x}")
		if not dry_run:
			exe.write_bytes(data)
			print(f"Patch written to {exe}")


def identify_return_value(data: bytes, addr: int) -> None|bytes:
	if data[addr:addr+2] == b"\x83\xc8":
		# Replace OR EAX,nn with XOR EAX,EAX; NOP
		return b"\x33\xc0\x90"
	elif data[addr] == 0xb8:
		# Replace MOV EAX,nn with MOV EAX,0
		if data[addr+1:addr+5] == b"\0\0\0\0":
			# Already patched
			return None
		return b"\xb8\0\0\0\0"
	elif data[addr:addr+3] == b"\x33\xc0\x90":
		# Already patched
		return None
	raise ValueError(f"unknown return value pattern at virtual address ${addr:08x}")
