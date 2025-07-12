def compress_frame(data: bytes, compressionLevel: int) -> bytes:
    """
	LZ4 compress a blob using the frame format.
	"""
    ...

def decompress_frame(src: bytes) -> bytes:
	"""
	Decompress a LZ4 compressed frame
	"""
	...
