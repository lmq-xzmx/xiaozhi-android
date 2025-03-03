package info.dourok.voicebot

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
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
    private val frameSize = (sampleRate * frameSizeMs) / 1000
    private val frameBytes = frameSize * channels * 2 // 16-bit PCM
    private val audioChannel = Channel<ByteArray>(capacity = 50)

    @SuppressLint("MissingPermission")
    fun startRecording(): Flow<ByteArray> {
        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            channelConfig,
            AudioFormat.ENCODING_PCM_16BIT,
            bufferSize
        ).apply {
            if (state == AudioRecord.STATE_INITIALIZED) {
                startRecording()
                Log.i(TAG, "Started recording")
            } else {
                throw IllegalStateException("Failed to initialize AudioRecord")
            }
        }

        Thread {
            val buffer = ByteArray(frameBytes)
            while (audioRecord?.recordingState == AudioRecord.RECORDSTATE_RECORDING) {
                val read = audioRecord?.read(buffer, 0, frameBytes) ?: 0
                if (read > 0) {
                    audioChannel.trySend(buffer.copyOf(read)).isSuccess
                }
            }
        }.start()

        return audioChannel.receiveAsFlow()
    }

    fun stopRecording() {
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
        audioChannel.close()
        Log.i(TAG, "Stopped recording")
    }
}