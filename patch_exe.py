import argparse
import sys
from pathlib import Path

from pefile import PE

parser = argparse.ArgumentParser()
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--dry-run", "-d", action="store_true")
parser.add_argument("exe", metavar="path/to/Indivisible.exe")
args = parser.parse_args()


exe = Path(args.exe)
if exe.is_dir():
	exe /= "Indivisible.exe"

if not exe.exists():
	print(f"File not found {exe}", file=sys.stderr)
	sys.exit(1)

if exe.name != "Indivisible.exe":
	yn = input("Warning: expecting to modify Indivisible.exe, continue? ")
	if yn not in "yY":
		sys.exit(0)

if args.dry_run:
	backup = exe
else:
	backup = exe.with_suffix(exe.suffix + ".bak")
	if backup.exists():
		yn = input("Warning: backup already exists, overwrite? ")
		if yn in "yY":
			backup.unlink(True)
			exe.rename(backup)
		else:
			print("Warning: proceeding without backup")
	else:
		exe.rename(backup)

# Modify binary
print("Searching for locations...")

def identify_return_value(addr: int):
	if data[addr:addr+2] == b"\x83\xc8":
		# Replace OR EAX,nn with XOR EAX,EAX; NOP
		return b"\x33\xc0\x90"
	elif data[addr] == 0xb8:
		# Replace MOV EAX,nn with MOV EAX,0
		return b"\xb8\0\0\0\0"
	raise ValueError(f"unknown return value pattern at virtual address ${addr:08x}")

def get_u4(addr: int):
	return int.from_bytes(data[addr:addr+4], "little", signed=True)

pe = PE(backup)
data = bytearray(pe.get_memory_mapped_image())
err1 = data.find(b"HashFile returned an error...\n")
err2 = data.find(b"VerifyHash returned an error...\n")
err3 = data.find(b"VerifyHash reports signature verification failed!\n")
test = data.find(b"\x48\x8d\x0d")
found = 0
call_loc = 0
replacements = list[tuple[bytes, bytes]]()
while test >= 0 and found < 3:
	if data[test+7] == 0xe8:
		# CALL
		offset = get_u4(test+3)
		address = test + 7 + offset
		if address in (err1, err2, err3):
			found += 1
			if args.verbose:
				print(f"  found {found} at virtual address ${test:08x}")
			cl = test + 12 + get_u4(test+8)
			if not call_loc:
				call_loc = cl
			elif call_loc != cl:
				raise ValueError("call was to an unexpected function")
			replacements.append((
				data[test:test+12],
				identify_return_value(test+12)
			))
	test = data.find(b"\x48\x8d\x0d", test+7)
del pe
assert len(replacements) == 3

# pefile won't do a minimal write-back so we do it ourselves
data = bytearray(backup.read_bytes())
for s, r in replacements:
	pos = data.find(s) + len(s)
	print(f"Replacement at ${pos:08x}: {r.hex(' ')}")
	data[pos:pos+len(r)] = r
if not args.dry_run:
	exe.write_bytes(data)
	print("Patch written")
