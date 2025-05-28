package info.dourok.voicebot

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import kotlinx.coroutines.runBlocking

/**
 * ESP32兼容的实时音频播放器
 * 完全模拟ESP32端的I2S实时播放机制，无缓冲延迟
 */
class OpusStreamPlayer(
    private val sampleRate: Int,
    private val channels: Int,
    frameSizeMs: Int
) {
    companion object {
        private const val TAG = "OpusStreamPlayer"
        
        // ESP32兼容参数
        private const val FRAME_DURATION_MS = 60L // ESP32使用60ms帧
        private const val SAMPLES_PER_FRAME = 960 // 16kHz * 60ms = 960 samples
        private const val BYTES_PER_SAMPLE = 2    // 16-bit PCM = 2 bytes
        private const val FRAME_SIZE_BYTES = SAMPLES_PER_FRAME * BYTES_PER_SAMPLE // 1920 bytes
        
        // 最小硬件缓冲，模拟I2S硬件缓冲
        private const val MIN_HARDWARE_BUFFER_FRAMES = 2 // 只保留2帧的硬件缓冲
    }

    private var audioTrack: AudioTrack
    private val playerScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var isStreaming = false
    private val mutex = Mutex()
    
    // ESP32模拟：实时播放统计
    private var framesReceived = 0
    private var framesPlayed = 0
    private var playbackStartTime = 0L

    init {
        val channelConfig = if (channels == 1) AudioFormat.CHANNEL_OUT_MONO else AudioFormat.CHANNEL_OUT_STEREO
        
        // ESP32兼容：最小缓冲区配置，模拟I2S硬件缓冲
        val minBufferSize = AudioTrack.getMinBufferSize(
            sampleRate,
            channelConfig,
            AudioFormat.ENCODING_PCM_16BIT
        )
        
        // 只使用最小缓冲区大小，模拟ESP32的I2S硬件缓冲
        val bufferSize = maxOf(minBufferSize, FRAME_SIZE_BYTES * MIN_HARDWARE_BUFFER_FRAMES)

        audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(sampleRate)
                    .setChannelMask(channelConfig)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .build()
            )
            .setBufferSizeInBytes(bufferSize)
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
        
        Log.i(TAG, "ESP32兼容播放器初始化: sampleRate=$sampleRate, channels=$channels, bufferSize=$bufferSize, 最小延迟模式")
    }

    /**
     * ESP32兼容：启动实时流式播放
     * 模拟ESP32的I2S实时接收和播放机制
     */
    fun start(pcmFlow: Flow<ByteArray?>) {
        playerScope.launch {
            try {
                mutex.withLock {
                    if (isStreaming) {
                        Log.w(TAG, "实时播放已在运行，跳过重复启动")
                        return@withLock
                    }
                    
                    isStreaming = true
                    framesReceived = 0
                    framesPlayed = 0
                    playbackStartTime = System.currentTimeMillis()
                    
                    Log.i(TAG, "🎵 启动ESP32兼容实时音频播放...")
                    
                    // 启动AudioTrack
            if (audioTrack.state == AudioTrack.STATE_INITIALIZED) {
                audioTrack.play()
                        Log.i(TAG, "AudioTrack启动成功，进入实时播放模式")
                    } else {
                        Log.e(TAG, "AudioTrack初始化失败")
                        return@withLock
                    }
            }

                // ESP32兼容：实时处理每个音频帧
                try {
                pcmFlow.collect { pcmData ->
                        // 检查协程是否被取消
                        ensureActive()
                        
                        pcmData?.let { data ->
                            if (isStreaming) {
                                processRealtimeAudioFrame(data)
                            }
                        }
                    }
                } catch (e: CancellationException) {
                    Log.i(TAG, "音频播放流被正常取消")
                    throw e
                } catch (e: Exception) {
                    Log.e(TAG, "音频播放流发生异常", e)
                    throw e
                }
                
            } catch (e: CancellationException) {
                Log.i(TAG, "ESP32实时播放被取消")
                // 协程取消是正常的，不需要报告为错误
            } catch (e: Exception) {
                Log.e(TAG, "ESP32实时播放失败", e)
            } finally {
                // 安全清理资源
                try {
                    withContext(NonCancellable) {
                        mutex.withLock {
                            isStreaming = false
                            if (audioTrack.state == AudioTrack.STATE_INITIALIZED) {
                                audioTrack.stop()
                                Log.i(TAG, "AudioTrack已安全停止")
                            }
                        }
                    }
                        } catch (e: Exception) {
                    Log.e(TAG, "清理播放资源时发生异常", e)
                }
            }
        }
    }
    
    /**
     * ESP32兼容：实时处理音频帧
     * 模拟ESP32接收Opus包后立即解码并写入I2S的过程
     */
    private suspend fun processRealtimeAudioFrame(pcmData: ByteArray) {
        if (!isStreaming || audioTrack.state != AudioTrack.STATE_INITIALIZED) {
            return
        }
        
        try {
            framesReceived++
            
            // ESP32兼容：直接写入AudioTrack，模拟I2S直接播放
            val bytesWritten = audioTrack.write(pcmData, 0, pcmData.size)
            
            if (bytesWritten > 0) {
                framesPlayed++
                
                Log.d(TAG, "实时播放帧 #$framesPlayed: 写入${bytesWritten}字节 (接收#$framesReceived)")
                
                // ESP32兼容：按60ms帧间隔控制播放节奏
                // 这里不需要sleep，因为AudioTrack的内部缓冲会控制播放速度
                // 这样才能真正模拟ESP32的I2S实时播放
                
            } else if (bytesWritten < 0) {
                Log.e(TAG, "AudioTrack写入失败: $bytesWritten")
                
                // ESP32兼容：写入失败时的处理策略
                when (bytesWritten) {
                    AudioTrack.ERROR_INVALID_OPERATION -> {
                        Log.e(TAG, "AudioTrack处于无效状态")
                    }
                    AudioTrack.ERROR_BAD_VALUE -> {
                        Log.e(TAG, "AudioTrack参数错误")
                        }
                    AudioTrack.ERROR_DEAD_OBJECT -> {
                        Log.e(TAG, "AudioTrack对象已死亡，尝试重新初始化")
                        // 这里可以尝试重新初始化AudioTrack
                    }
                    else -> {
                        Log.e(TAG, "未知的AudioTrack错误: $bytesWritten")
                }
            }
            } else {
                Log.w(TAG, "AudioTrack写入返回0，可能缓冲区已满")
                
                // ESP32兼容：如果AudioTrack缓冲区满了，稍等一下再继续
                // 这模拟了ESP32的I2S当硬件缓冲满时的行为
                delay(5) // 短暂延迟5ms
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "实时音频帧处理失败", e)
        }
    }

    /**
     * ESP32兼容：停止实时播放
     */
    fun stop() {
        playerScope.launch {
            try {
                mutex.withLock {
                    if (!isStreaming) return@withLock
                    
                    Log.i(TAG, "🛑 停止ESP32兼容实时播放...")
                    isStreaming = false
                    
            if (audioTrack.state == AudioTrack.STATE_INITIALIZED) {
                        // ESP32兼容：停止播放，但让已有的音频播放完毕
                audioTrack.stop()
                        Log.i(TAG, "AudioTrack已停止")
                    }
                    
                    // ESP32兼容：输出播放统计信息
                    val totalDuration = System.currentTimeMillis() - playbackStartTime
                    Log.i(TAG, "播放统计: 接收帧数=$framesReceived, 播放帧数=$framesPlayed, 总时长=${totalDuration}ms")
                }
            } catch (e: Exception) {
                Log.e(TAG, "停止播放时发生异常", e)
            }
        }
    }

    /**
     * 释放所有资源
     */
    fun release() {
        try {
            // 首先停止播放
            runBlocking {
                withContext(NonCancellable) {
                    mutex.withLock {
                        isStreaming = false
                        if (audioTrack.state == AudioTrack.STATE_INITIALIZED) {
                            audioTrack.stop()
                        }
                    }
                }
            }
            
            // 取消协程作用域
            playerScope.cancel()
            
            // 释放AudioTrack
        audioTrack.release()
            Log.i(TAG, "ESP32兼容播放器资源已释放")
            
        } catch (e: Exception) {
            Log.e(TAG, "释放播放器资源时发生异常", e)
        }
    }

    /**
     * ESP32兼容：等待播放完成
     * 模拟ESP32等待I2S硬件缓冲区播放完毕的过程
     */
    suspend fun waitForPlaybackCompletion() {
        if (!isStreaming) {
            Log.d(TAG, "播放器未运行，无需等待")
            return
        }
        
        Log.i(TAG, "等待实时播放完成...")
        
        // ESP32兼容：检查AudioTrack的播放头位置
        var previousPosition = audioTrack.playbackHeadPosition
        var stableCount = 0
        val maxStableChecks = 5 // 最多检查5次稳定状态
        val checkInterval = 100L // 每100ms检查一次
        
        while (audioTrack.playState == AudioTrack.PLAYSTATE_PLAYING && stableCount < maxStableChecks) {
            delay(checkInterval)
            
            val currentPosition = audioTrack.playbackHeadPosition
            if (currentPosition == previousPosition) {
                stableCount++
                Log.d(TAG, "播放头位置稳定 #$stableCount: $currentPosition")
            } else {
                stableCount = 0
                previousPosition = currentPosition
                Log.d(TAG, "播放头位置变化: $currentPosition")
            }
        }
        
        Log.i(TAG, "✅ 实时播放完成等待结束")
    }
    
    /**
     * ESP32兼容：获取播放器状态信息
     */
    fun getPlaybackInfo(): String {
        return if (isStreaming) {
            val bufferPosition = audioTrack.playbackHeadPosition
            val playState = when (audioTrack.playState) {
                AudioTrack.PLAYSTATE_STOPPED -> "STOPPED"
                AudioTrack.PLAYSTATE_PAUSED -> "PAUSED"
                AudioTrack.PLAYSTATE_PLAYING -> "PLAYING"
                else -> "UNKNOWN"
            }
            "实时播放中: 状态=$playState, 播放位置=$bufferPosition, 接收帧数=$framesReceived, 播放帧数=$framesPlayed"
        } else {
            "播放器已停止"
        }
    }
}