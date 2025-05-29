package info.dourok.voicebot

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class OpusEncoder(
    private val sampleRate: Int,
    private val channels: Int,
    frameSizeMs: Int
) {
    companion object {
        private const val TAG = "OpusEncoder"

        init {
            // 临时注释掉，避免CMake问题
            // System.loadLibrary("app")
        }
    }

    private var nativeEncoderHandle: Long = 0
    private val frameSize: Int = (sampleRate * frameSizeMs) / 1000

    init {
        // 临时使用模拟实现
        // nativeEncoderHandle = nativeInitEncoder(sampleRate, channels, 2048) // OPUS_APPLICATION_VOIP
        // if (nativeEncoderHandle == 0L) {
        //     throw IllegalStateException("Failed to initialize Opus encoder")
        // }
        nativeEncoderHandle = 1L // 模拟句柄
    }

    suspend fun encode(pcmData: ByteArray): ByteArray? = withContext(Dispatchers.IO) {
        val frameBytes = frameSize * channels * 2 // 16-bit PCM
        if (pcmData.size != frameBytes) {
            Log.e(TAG, "Input buffer size must be $frameBytes bytes (got ${pcmData.size})")
            return@withContext null
        }

        // 临时返回原始数据，跳过实际编码
        return@withContext pcmData
        
        // val outputBuffer = ByteArray(frameBytes) // 分配足够大的缓冲区
        // val encodedBytes = nativeEncodeBytes(
        //     nativeEncoderHandle,
        //     pcmData,
        //     pcmData.size,
        //     outputBuffer,
        //     outputBuffer.size
        // )
        // 
        // if (encodedBytes > 0) {
        //     outputBuffer.copyOf(encodedBytes)
        // } else {
        //     Log.e(TAG, "Failed to encode frame")
        //     null
        // }
    }

    fun release() {
        if (nativeEncoderHandle != 0L) {
            // nativeReleaseEncoder(nativeEncoderHandle)
            nativeEncoderHandle = 0
        }
    }

    protected fun finalize() {
        release()
    }

    // 临时注释掉native方法
    // private external fun nativeInitEncoder(sampleRate: Int, channels: Int, application: Int): Long
    // private external fun nativeEncodeBytes(
    //     encoderHandle: Long,
    //     inputBuffer: ByteArray,
    //     inputSize: Int,
    //     outputBuffer: ByteArray,
    //     maxOutputSize: Int
    // ): Int
    // 
    // private external fun nativeReleaseEncoder(encoderHandle: Long)
}