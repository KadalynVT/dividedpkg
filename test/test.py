import os, sys
import subprocess
from pathlib import Path

test = Path(__file__).parent
cwd = test.parent

sys.path.append(str(cwd))
from dividedpkg import PKG

venv = cwd / "venv"
contents = test / "contents"

env = os.environ.copy()
try: del env["PYTHONHOME"]
except: pass
env["PATH"] = f"{venv}/Scripts:{env['PATH']}"

def run(*args: str):
	return subprocess.run(
		["./venv/Scripts/python.exe", "-m", "dividedpkg", *map(str, args)],
		cwd=cwd,
		env=env,
		encoding="utf8",
		capture_output=True,
	)


fails = 0
def err(msg: str):
	global fails
	print(msg, file=sys.stderr)
	fails += 1


success = 0
def ok(msg: str):
	global success
	print(msg, file=sys.stderr)
	success += 1


a_id = "a.txt"
b_id = "b.compressme.txt"
a = contents / a_id
b = contents / b_id
a_bytes = a.read_bytes()
b_bytes = b.read_bytes()

# LZ4 test
b_lz4 = b.with_suffix(b.suffix + ".lz4")

if (
	run("-C", b).returncode == 0
	and run("-U", b_lz4).returncode == 0
	and b_bytes == b.read_bytes()
):
	b_lz4.unlink()
	ok("lz4 test success")
else:
	b.write_bytes(b_bytes)
	err("lz4 test failed")

# Create new pkg with compression
pkg = test / "contents.pkg"
if (
	run("-p", a, b_lz4, pkg).returncode == 0
	and pkg.exists()
	and b"Reverge Package File" not in pkg.read_bytes()
	and PKG.load(pkg, True).read(a_id) == a_bytes
):
	ok("create pkg test success")

	# Test listing
	p = run("-l", pkg)
	lines = p.stdout.splitlines()
	if (
		lines[0] == "offset            , size      , name"
		and lines[1] == "0x0000000000000074, 0x0000000d, a.txt"
		and lines[2].split(", ")[::2] == ["0x0000000000000081", "b.compressme.txt.lz4"]
	):
		ok("list pkg test success")
	else:
		err("list pkg test failed")
	pkg.unlink()
else:
	err("create pkg test failed")
	err("list pkg test skipped")

# Create new pkg from folder with compression
if (
	run("-p", "-c", "*.compressme.*", contents, pkg).returncode == 0
	and pkg.exists()
	and b"Reverge Package File" not in pkg.read_bytes()
	and PKG.load(pkg, True).read(a_id) == a_bytes
	and (b_id + ".lz4") in PKG.load(pkg, True).files
):
	ok("create pkg from folder test success")
	out = test / "out"
	out.mkdir(exist_ok=True)
	if (
		run("-u", pkg, out).returncode == 0
		and out.exists()
		and (out / a_id).read_bytes() == a_bytes
		and (out / b_id).read_bytes() == b_bytes
	):
		ok("unpack pkg test success")
		(out / a_id).unlink()
		(out / b_id).unlink()
		out.rmdir()
	else:
		err("unpack pkg test failed")
	pkg.unlink()
else:
	err("create pkg from folder test failed")
	err("unpack pkg test skipped")


# Create new package only specifying folder

if (
	run("-p", contents).returncode == 0
	and pkg.exists()
):
	ok("create pkg from folder only test success")
	pkg.unlink()
else:
	err("create pkg from folder only test failed")

# TODO: include1 path
# TODO: encrypt/decrypt paths as well as in combination with

print(f"Success: {success} / {success+fails}")
