#!/bin/bash

# =============================================================================
# Android CMake功能恢复脚本
# 用途：恢复OpusEncoder/OpusDecoder的完整native实现
# 作者：AI Assistant
# 日期：2024-12-28
# =============================================================================

echo "🔧 开始恢复Android项目的CMake功能..."

PROJECT_ROOT="/Users/xzmx/Downloads/my-project/xiaozhi-android"
cd "$PROJECT_ROOT"

# 1. 恢复gradle.properties配置
echo "📝 1. 更新gradle.properties..."
cat > gradle.properties << 'EOF'
# Project-wide Gradle settings.
# IDE (e.g. Android Studio) users:
# Gradle settings configured through the IDE *will override*
# any settings specified in this file.
# For more details on how to configure your build environment visit
# http://www.gradle.org/docs/current/userguide/build_environment.html
# Specifies the JVM arguments used for the daemon process.
# The setting is particularly useful for tweaking memory settings.
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8 --enable-native-access=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED
# When configured, Gradle will run in incubating parallel mode.
# This option should only be used with decoupled projects. For more details, visit
# https://developer.android.com/r/tools/gradle-multi-project-decoupled-projects
# org.gradle.parallel=true
# AndroidX package structure to make it clearer which packages are bundled with the
# Android operating system, and which are packaged with your app's APK
# https://developer.android.com/topic/libraries/support-library/androidx-rn
android.useAndroidX=true
# Kotlin code style for this project: "official" or "obsolete":
kotlin.code.style=official
# Enables namespacing of each library's R class so that its R class includes only the
# resources declared in the library itself and none from the library's dependencies,
# thereby reducing the size of the R class for that library
android.nonTransitiveRClass=true
EOF

# 2. 恢复build.gradle.kts配置
echo "📝 2. 恢复build.gradle.kts中的CMake配置..."
sed -i '' 's|// \(externalNativeBuild\)|\1|g' app/build.gradle.kts
sed -i '' 's|// \(cmake\)|\1|g' app/build.gradle.kts
sed -i '' 's|// \(arguments\)|\1|g' app/build.gradle.kts
sed -i '' 's|// \(cppFlags\)|\1|g' app/build.gradle.kts
sed -i '' 's|// \(path\)|\1|g' app/build.gradle.kts
sed -i '' 's|// \(version\)|\1|g' app/build.gradle.kts

# 3. 恢复OpusEncoder.kt
echo "📝 3. 恢复OpusEncoder.kt的native实现..."
cat > app/src/main/java/info/dourok/voicebot/OpusEncoder.kt << 'EOF'
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
            System.loadLibrary("app")
        }
    }

    private var nativeEncoderHandle: Long = 0
    private val frameSize: Int = (sampleRate * frameSizeMs) / 1000

    init {
        nativeEncoderHandle = nativeInitEncoder(sampleRate, channels, 2048) // OPUS_APPLICATION_VOIP
        if (nativeEncoderHandle == 0L) {
            throw IllegalStateException("Failed to initialize Opus encoder")
        }
    }

    suspend fun encode(pcmData: ByteArray): ByteArray? = withContext(Dispatchers.IO) {
        val frameBytes = frameSize * channels * 2 // 16-bit PCM
        if (pcmData.size != frameBytes) {
            Log.e(TAG, "Input buffer size must be $frameBytes bytes (got ${pcmData.size})")
            return@withContext null
        }

        val outputBuffer = ByteArray(frameBytes) // 分配足够大的缓冲区
        val encodedBytes = nativeEncodeBytes(
            nativeEncoderHandle,
            pcmData,
            pcmData.size,
            outputBuffer,
            outputBuffer.size
        )

        if (encodedBytes > 0) {
            outputBuffer.copyOf(encodedBytes)
        } else {
            Log.e(TAG, "Failed to encode frame")
            null
        }
    }

    fun release() {
        if (nativeEncoderHandle != 0L) {
            nativeReleaseEncoder(nativeEncoderHandle)
            nativeEncoderHandle = 0
        }
    }

    protected fun finalize() {
        release()
    }

    private external fun nativeInitEncoder(sampleRate: Int, channels: Int, application: Int): Long
    private external fun nativeEncodeBytes(
        encoderHandle: Long,
        inputBuffer: ByteArray,
        inputSize: Int,
        outputBuffer: ByteArray,
        maxOutputSize: Int
    ): Int

    private external fun nativeReleaseEncoder(encoderHandle: Long)
}
EOF

# 4. 恢复OpusDecoder.kt
echo "📝 4. 恢复OpusDecoder.kt的native实现..."
cat > app/src/main/java/info/dourok/voicebot/OpusDecoder.kt << 'EOF'
package info.dourok.voicebot

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class OpusDecoder(
    private val sampleRate: Int,
    private val channels: Int,
    frameSizeMs: Int
) {
    companion object {
        private const val TAG = "OpusDecoder"

        init {
            System.loadLibrary("app")
        }
    }

    private var nativeDecoderHandle: Long = 0
    private val frameSize: Int = (sampleRate * frameSizeMs) / 1000

    init {
        nativeDecoderHandle = nativeInitDecoder(sampleRate, channels)
        if (nativeDecoderHandle == 0L) {
            throw IllegalStateException("Failed to initialize Opus decoder")
        }
    }

    // 使用协程进行解码，运行在 IO 线程
    suspend fun decode(opusData: ByteArray): ByteArray? = withContext(Dispatchers.IO) {
        val maxPcmSize = frameSize * channels * 2 // 16-bit PCM
        val pcmBuffer = ByteArray(maxPcmSize)

        val decodedBytes = nativeDecodeBytes(
            nativeDecoderHandle,
            opusData,
            opusData.size,
            pcmBuffer,
            maxPcmSize
        )

        if (decodedBytes > 0) {
            if (decodedBytes < pcmBuffer.size) {
                pcmBuffer.copyOf(decodedBytes)
            } else {
                pcmBuffer
            }
        } else {
            Log.e(TAG, "Failed to decode frame")
            null
        }
    }

    fun release() {
        if (nativeDecoderHandle != 0L) {
            nativeReleaseDecoder(nativeDecoderHandle)
            nativeDecoderHandle = 0
        }
    }

    protected fun finalize() {
        release()
    }

    private external fun nativeInitDecoder(sampleRate: Int, channels: Int): Long
    private external fun nativeDecodeBytes(
        decoderHandle: Long,
        inputBuffer: ByteArray,
        inputSize: Int,
        outputBuffer: ByteArray,
        maxOutputSize: Int
    ): Int

    private external fun nativeReleaseDecoder(decoderHandle: Long)
}
EOF

# 5. 停止gradle daemon
echo "🛑 5. 停止Gradle daemon..."
./gradlew --stop

echo ""
echo "✅ CMake功能恢复完成！"
echo ""
echo "🚀 现在可以尝试编译："
echo "   export JAVA_TOOL_OPTIONS=\"--enable-native-access=ALL-UNNAMED\""
echo "   ./gradlew clean assembleDebug"
echo ""
echo "📝 如果仍有问题，请检查："
echo "   1. JDK版本（建议使用JDK 11）"
echo "   2. CMakeLists.txt配置"
echo "   3. opus库依赖"
echo "" 