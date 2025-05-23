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
    private val audioChannel = Channel<ByteArray>(capacity = 50)
    private var isRecording = false
    private var audioDataCount = 0


    @SuppressLint("MissingPermission")
    fun startRecording(): Flow<ByteArray> {
        Log.i(TAG, "Starting audio recording...")
        Log.d(TAG, "Audio config: sampleRate=$sampleRate, channels=$channels, frameSizeMs=$frameSizeMs")
        Log.d(TAG, "Buffer config: bufferSize=$bufferSize, frameSize=$frameSize, frameBytes=$frameBytes")
        
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

        Thread {
            val buffer = ByteArray(frameBytes)
            Log.i(TAG, "Audio recording thread started")
            
            while (audioRecord?.recordingState == AudioRecord.RECORDSTATE_RECORDING && isRecording) {
                val read = audioRecord?.read(buffer, 0, frameBytes) ?: 0
                if (read > 0) {
                    audioDataCount++
                    val success = audioChannel.trySend(buffer.copyOf(read)).isSuccess
                    
                    // 每100帧打印一次状态
                    if (audioDataCount % 100 == 0) {
                        Log.d(TAG, "Audio frames processed: $audioDataCount, last frame size: $read bytes, send success: $success")
                    }
                    
                    if (!success) {
                        Log.w(TAG, "Failed to send audio data to channel, frame $audioDataCount")
                    }
                } else if (read < 0) {
                    Log.e(TAG, "AudioRecord read error: $read")
                } else {
                    Log.w(TAG, "AudioRecord read returned 0 bytes")
                }
            }
            Log.i(TAG, "Audio recording thread ended. Total frames: $audioDataCount")
        }.start()

        Log.i(TAG, "Audio recording flow created")
        return audioChannel.receiveAsFlow()
    }

    fun stopRecording() {
        Log.i(TAG, "Stopping audio recording...")
        isRecording = false
        
        audioRecord?.apply {
            if (recordingState == AudioRecord.RECORDSTATE_RECORDING) {
                stop()
                Log.i(TAG, "AudioRecord stopped")
            }
            release()
            Log.i(TAG, "AudioRecord released")
        }
        audioRecord = null
        
        aec?.apply {
            enabled = false
            release()
            Log.i(TAG, "AEC disabled and released")
        }
        aec = null
        
        ns?.apply {
            enabled = false
            release()
            Log.i(TAG, "NS disabled and released")
        }
        ns = null
        
        audioChannel.close()
        Log.i(TAG, "Audio channel closed. Total frames processed: $audioDataCount")
        audioDataCount = 0
    }
}