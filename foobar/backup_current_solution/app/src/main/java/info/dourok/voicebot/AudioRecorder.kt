package info.dourok.voicebot

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.media.audiofx.AcousticEchoCanceler
import android.media.audiofx.NoiseSuppressor
import android.util.Log
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.receiveAsFlow

class AudioRecorder(
    private val sampleRate: Int,
    private val channels: Int,
    private val frameSizeMs: Int
) {
    companion object {
        private const val TAG = "AudioRecorder"
    }

    private val channelConfig = if (channels == 1) AudioFormat.CHANNEL_IN_MONO else AudioFormat.CHANNEL_IN_STEREO
    private val bufferSize = AudioRecord.getMinBufferSize(
        sampleRate,
        channelConfig,
        AudioFormat.ENCODING_PCM_16BIT
    ) * 2
    private var audioRecord: AudioRecord? = null
    private var aec: AcousticEchoCanceler? = null
    private var ns: NoiseSuppressor? = null
    private val frameSize = (sampleRate * frameSizeMs) / 1000
    private val frameBytes = frameSize * channels * 2 // 16-bit PCM
    private var audioChannel: Channel<ByteArray>? = null
    private var isRecording = false
    private var audioDataCount = 0
    private var recordingThread: Thread? = null


    @SuppressLint("MissingPermission")
    fun startRecording(): Flow<ByteArray> {
        Log.i(TAG, "Starting audio recording...")
        Log.d(TAG, "Audio config: sampleRate=$sampleRate, channels=$channels, frameSizeMs=$frameSizeMs")
        Log.d(TAG, "Buffer config: bufferSize=$bufferSize, frameSize=$frameSize, frameBytes=$frameBytes")
        
        // 防止重复启动
        if (isRecording) {
            Log.w(TAG, "Recording already in progress, stopping previous recording first")
            stopRecording()
        }
        
        // 创建新的音频通道
        audioChannel = Channel<ByteArray>(capacity = 50)
        
        try {
            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate,
                channelConfig,
                AudioFormat.ENCODING_PCM_16BIT,
                bufferSize
            ).apply {
                if (state == AudioRecord.STATE_INITIALIZED) {
                    Log.i(TAG, "AudioRecord initialized successfully")
                    
                    // 初始化 AEC
                    if (AcousticEchoCanceler.isAvailable()) {
                        aec = AcousticEchoCanceler.create(audioSessionId).apply {
                            enabled = true
                            Log.i(TAG, "AEC initialized and enabled")
                        }
                    } else {
                        Log.w(TAG, "AEC not available on this device")
                    }

                    if(NoiseSuppressor.isAvailable()) {
                        ns = NoiseSuppressor.create(audioSessionId).apply {
                            enabled = true
                            Log.i(TAG, "NS initialized and enabled")
                        }
                    } else {
                        Log.w(TAG, "NS not available on this device")
                    }

                    startRecording()
                    isRecording = true
                    Log.i(TAG, "AudioRecord recording started")
                } else {
                    Log.e(TAG, "Failed to initialize AudioRecord, state: $state")
                    throw IllegalStateException("Failed to initialize AudioRecord")
                }
            }
        } catch (e: SecurityException) {
            Log.e(TAG, "Security exception - missing audio permission: ${e.message}")
            throw e
        } catch (e: Exception) {
            Log.e(TAG, "Exception initializing AudioRecord: ${e.message}", e)
            throw e
        }

        recordingThread = Thread {
            val buffer = ByteArray(frameBytes)
            Log.i(TAG, "Audio recording thread started")
            
            try {
                while (audioRecord?.recordingState == AudioRecord.RECORDSTATE_RECORDING && isRecording) {
                    val read = audioRecord?.read(buffer, 0, frameBytes) ?: 0
                    if (read > 0) {
                        audioDataCount++
                        val currentChannel = audioChannel
                        if (currentChannel != null && !currentChannel.isClosedForSend) {
                            val success = currentChannel.trySend(buffer.copyOf(read)).isSuccess
                            
                            // 每100帧打印一次状态
                            if (audioDataCount % 100 == 0) {
                                Log.d(TAG, "Audio frames processed: $audioDataCount, last frame size: $read bytes, send success: $success")
                            }
                            
                            if (!success) {
                                Log.w(TAG, "Failed to send audio data to channel, frame $audioDataCount")
                            }
                        } else {
                            Log.w(TAG, "Audio channel is closed, stopping recording thread")
                            break
                        }
                    } else if (read < 0) {
                        Log.e(TAG, "AudioRecord read error: $read")
                        break
                    } else {
                        Log.w(TAG, "AudioRecord read returned 0 bytes")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Exception in recording thread", e)
            } finally {
                Log.i(TAG, "Audio recording thread ended. Total frames: $audioDataCount")
            }
        }
        recordingThread?.start()

        Log.i(TAG, "Audio recording flow created")
        return audioChannel?.receiveAsFlow() ?: throw IllegalStateException("Audio channel not initialized")
    }

    fun stopRecording() {
        Log.i(TAG, "Stopping audio recording...")
        isRecording = false
        
        // 等待录音线程结束
        recordingThread?.let { thread ->
            try {
                thread.join(1000) // 最多等待1秒
                if (thread.isAlive) {
                    Log.w(TAG, "Recording thread did not stop gracefully")
                }
            } catch (e: InterruptedException) {
                Log.e(TAG, "Interrupted while waiting for recording thread to stop", e)
            }
        }
        recordingThread = null
        
        audioRecord?.apply {
            try {
                if (recordingState == AudioRecord.RECORDSTATE_RECORDING) {
                    stop()
                    Log.i(TAG, "AudioRecord stopped")
                }
                release()
                Log.i(TAG, "AudioRecord released")
            } catch (e: Exception) {
                Log.e(TAG, "Error stopping/releasing AudioRecord", e)
            }
        }
        audioRecord = null
        
        aec?.apply {
            try {
                enabled = false
                release()
                Log.i(TAG, "AEC disabled and released")
            } catch (e: Exception) {
                Log.e(TAG, "Error releasing AEC", e)
            }
        }
        aec = null
        
        ns?.apply {
            try {
                enabled = false
                release()
                Log.i(TAG, "NS disabled and released")
            } catch (e: Exception) {
                Log.e(TAG, "Error releasing NS", e)
            }
        }
        ns = null
        
        audioChannel?.close()
        audioChannel = null
        Log.i(TAG, "Audio channel closed. Total frames processed: $audioDataCount")
        audioDataCount = 0
    }
}