cdef extern from "lz4frame.h":

    cdef unsigned LZ4F_VERSION = 100
    ctypedef size_t LZ4F_errorCode_t

    # Opaque structs
    cdef struct LZ4F_cctx_s: pass
    cdef struct LZ4F_dctx_s: pass
    cdef struct LZ4F_CDict: pass

    ctypedef LZ4F_cctx_s LZ4F_cctx
    ctypedef LZ4F_dctx_s LZ4F_dctx
    ctypedef LZ4F_cctx* LZ4F_compressionContext_t
    ctypedef LZ4F_dctx* LZ4F_decompressionContext_t

    ctypedef enum LZ4F_blockSizeID_t:
        LZ4F_default = 0
        LZ4F_max64KB = 4
        LZ4F_max256KB = 5
        LZ4F_max1MB = 6
        LZ4F_max4MB = 7

    ctypedef enum LZ4F_blockMode_t:
        LZ4F_blockLinked = 0
        LZ4F_blockIndependent = 1

    ctypedef enum LZ4F_contentChecksum_t:
        LZ4F_noContentChecksum = 0
        LZ4F_contentChecksumEnabled = 1

    ctypedef enum LZ4F_blockChecksum_t:
        LZ4F_noBlockChecksum = 0
        LZ4F_blockChecksumEnabled = 1

    ctypedef enum LZ4F_frameType_t:
        LZ4F_frame = 0
        LZ4F_skippableFrame = 1

    ctypedef struct LZ4F_frameInfo_t:
        LZ4F_blockSizeID_t blockSizeID
        LZ4F_blockMode_t blockMode
        LZ4F_contentChecksum_t contentChecksumFlag
        LZ4F_frameType_t frameType
        unsigned long long contentSize
        unsigned dictID
        LZ4F_blockChecksum_t blockChecksumFlag

    ctypedef struct LZ4F_preferences_t:
        LZ4F_frameInfo_t frameInfo
        int compressionLevel
        unsigned autoFlush
        unsigned favorDecSpeed
        unsigned reserved[3]

    ctypedef struct LZ4F_compressOptions_t:
        unsigned stableSrc
        unsigned reserved[3]

    ctypedef struct LZ4F_decompressOptions_t:
        unsigned stableDst
        unsigned skipChecksums
        unsigned reserved1
        unsigned reserved0

    # Functions
    size_t LZ4F_getFrameInfo(LZ4F_dctx* dctx,
                             LZ4F_frameInfo_t* frameInfoPtr,
                             const void* srcBuffer, size_t* srcSizePtr)

    size_t LZ4F_decompress(LZ4F_dctx* dctx,
                           void* dstBuffer, size_t* dstSizePtr,
                           const void* srcBuffer, size_t* srcSizePtr,
                           const LZ4F_decompressOptions_t* dOptPtr)

    size_t LZ4F_compressFrame(void* dst, size_t dstCap,
                              const void* src, size_t srcSize,
                              const LZ4F_preferences_t* prefs)

    size_t LZ4F_compressFrameBound(size_t srcSize,
                                   const LZ4F_preferences_t* prefs)

    int LZ4F_compressionLevel_max()

    LZ4F_errorCode_t LZ4F_createCompressionContext(LZ4F_cctx** cctx, unsigned version)
    LZ4F_errorCode_t LZ4F_freeCompressionContext(LZ4F_cctx* cctx)
    LZ4F_errorCode_t LZ4F_createDecompressionContext(LZ4F_dctx** dctxPtr, unsigned version)
    LZ4F_errorCode_t LZ4F_freeDecompressionContext(LZ4F_dctx* dctx)

    size_t LZ4F_compressBegin(LZ4F_cctx* cctx, void* dst, size_t dstCap,
                              const LZ4F_preferences_t* prefs)

    size_t LZ4F_compressUpdate(LZ4F_cctx* cctx, void* dst, size_t dstCap,
                               const void* src, size_t srcSize,
                               const LZ4F_compressOptions_t* opts)

    size_t LZ4F_flush(LZ4F_cctx* cctx, void* dst, size_t dstCap,
                      const LZ4F_compressOptions_t* opts)

    size_t LZ4F_compressEnd(LZ4F_cctx* cctx, void* dst, size_t dstCap,
                            const LZ4F_compressOptions_t* opts)

    unsigned LZ4F_isError(LZ4F_errorCode_t code)
    const char* LZ4F_getErrorName(LZ4F_errorCode_t code)
