import cython
from cython.parallel import prange # type: ignore

@cython.locals(i="Py_ssize_t", keylen="Py_ssize_t")
@cython.ccall
def xor_buffer(data: bytearray, key: bytes, key_offset: cython.Py_ssize_t):
	dview: cython.uchar[:] = data
	kview: cython.const_uchar[:] = key
	keylen = len(key)
	for i in range(len(data)):
		dview[i] ^= kview[(i + key_offset) % keylen]


@cython.locals(i="Py_ssize_t", n="Py_ssize_t", keylen="Py_ssize_t")
@cython.boundscheck(False)
@cython.ccall
def xor_parallel(data: bytearray, key: bytes, key_offset: cython.Py_ssize_t):
	dview: cython.uchar[:] = data
	kview: cython.const_uchar[:] = key
	n = len(data)
	keylen = len(key)
	for i in prange(n, nogil=True, schedule="static"):
		dview[i] ^= kview[(i + key_offset) % keylen]
