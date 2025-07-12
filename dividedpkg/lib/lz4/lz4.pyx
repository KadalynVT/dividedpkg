# distutils: language = c
# cython: language_level=3

from libc.stdlib cimport malloc, free
from libc.string cimport memset
from libc.stdint cimport uint8_t
from lz4f cimport *

def compress_frame(bytes src, int compressionLevel):
	cdef size_t srcSize = len(src)
	cdef LZ4F_preferences_t prefs
	memset(&prefs, 0, sizeof(LZ4F_preferences_t))
	prefs.frameInfo.blockMode = LZ4F_blockIndependent
	prefs.frameInfo.blockSizeID = LZ4F_max4MB
	prefs.frameInfo.contentChecksumFlag = LZ4F_contentChecksumEnabled
	prefs.frameInfo.contentSize = srcSize
	prefs.compressionLevel = compressionLevel
	prefs.favorDecSpeed = 1
	cdef size_t dstCap = LZ4F_compressFrameBound(srcSize, &prefs)
	cdef char* dst = <char*> malloc(dstCap)
	if not dst:
		raise MemoryError()

	cdef const uint8_t[:] src_view = src
	cdef size_t result = LZ4F_compressFrame(dst, dstCap, <const void*> &src_view[0], srcSize, &prefs)
	if LZ4F_isError(result):
		msg = LZ4F_getErrorName(result)
		free(dst)
		raise RuntimeError(f"LZ4 error: {msg.decode()}")

	out = bytes(dst[:result])
	free(dst)
	return out

def decompress_frame(bytes src):
	cdef LZ4F_dctx* ctx
	cdef LZ4F_errorCode_t err = LZ4F_createDecompressionContext(&ctx, LZ4F_VERSION)
	if LZ4F_isError(err):
		msg = LZ4F_getErrorName(err)
		raise RuntimeError(f"failed to create decompression ctx {msg.decode()}")

	cdef size_t srcSize = len(src)
	cdef size_t srcRead = srcSize
	cdef const uint8_t[:] cSrc = src
	cdef const uint8_t *src_view = &cSrc[0]
	cdef LZ4F_frameInfo_t info
	LZ4F_getFrameInfo(ctx, &info, <const void*> src_view, &srcRead)
	src_view += srcRead
	srcSize -= srcRead

	cdef LZ4F_decompressOptions_t opts
	memset(&opts, 0, sizeof(LZ4F_decompressOptions_t))

	cdef size_t dstSize = info.contentSize
	cdef size_t dstWritten
	cdef char *dst = <char*> malloc(dstSize)
	if not dst:
		raise RuntimeError("failed to allocate destination memory")

	out = b""
	cdef char *dst_view = dst
	while srcSize:
		srcRead = srcSize
		dstWritten = dstSize
		LZ4F_decompress(ctx, <void*> dst_view, &dstWritten, <const void*> src_view, &srcRead, &opts)
		dst_view += dstWritten
		src_view += srcRead
		srcSize -= srcRead

	out = bytes(dst[:dstSize])
	free(dst)
	return out
