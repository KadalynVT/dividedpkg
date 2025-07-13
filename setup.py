from setuptools import find_packages, setup, Extension
from Cython.Build import cythonize

ext = [
	Extension(
		name="lz4fwrapper",
		sources=["dividedpkg/lib/lz4/lz4.pyx"],
		include_dirs=["lib/lz4"],
		extra_objects=["lib/lz4/liblz4.lib"],
		language="c"
	),
	Extension(
		"xorcrypt",
		["dividedpkg/xorcrypt.py"],
		extra_compile_args=["/openmp"]
	),
]

setup(
	ext_modules=cythonize(ext, compiler_directives={"language_level": 3}),
	packages=find_packages(include=['dividedpkg', 'dividedpkg.*']),
)
