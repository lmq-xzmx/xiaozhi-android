/**
 * 第二阶段实施前的完整备份
 * 当前ChatViewModel.kt的完整实现
 * 时间: 2025-05-28
 */

// 以下是ChatViewModel.kt的当前完整内容备份
// 这个备份将在第二阶段实施失败时用于回滚

/*
=== ChatViewModel.kt 当前实现备份 ===
package info.dourok.voicebot.ui

import android.content.Context
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import info.dourok.voicebot.AudioRecorder
import info.dourok.voicebot.NavigationEvents
import info.dourok.voicebot.OpusDecoder
import info.dourok.voicebot.OpusEncoder
import info.dourok.voicebot.OpusStreamPlayer
import info.dourok.voicebot.config.BindingState
import info.dourok.voicebot.config.NavigationEvent
import info.dourok.voicebot.config.OtaIntegrationService
import info.dourok.voicebot.data.SettingsRepository
import info.dourok.voicebot.data.model.DeviceInfo
import info.dourok.voicebot.data.model.TransportType
import info.dourok.voicebot.protocol.AbortReason
import info.dourok.voicebot.protocol.ListeningMode
import info.dourok.voicebot.protocol.MqttProtocol
import info.dourok.voicebot.protocol.Protocol
import info.dourok.voicebot.protocol.WebsocketProtocol
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Locale
import javax.inject.Inject

@HiltViewModel
class ChatViewMode @Inject constructor(
    @ApplicationContext private val context: Context,
    @NavigationEvents private val navigationEvents: MutableSharedFlow<String>,
    deviceInfo: DeviceInfo,
    settings: SettingsRepository,
    private val otaIntegrationService: OtaIntegrationService
) : ViewModel() {

    companion object {
        private const val TAG = "ChatViewModel"
    }

    private var keepListening = false
    private var aborted = false

    var deviceState by mutableStateOf(DeviceState.UNKNOWN)
        private set

    private val _shouldShowBindingDialog = MutableStateFlow(false)
    val shouldShowBindingDialog: StateFlow<Boolean> = _shouldShowBindingDialog.asStateFlow()

    private val _bindingMessage = MutableStateFlow<String?>(null)
    val bindingMessage: StateFlow<String?> = _bindingMessage.asStateFlow()

    // 其他状态变量
    val bindingState: StateFlow<BindingState> = otaIntegrationService.bindingState

    // 核心组件
    private lateinit var protocol: Protocol
    private var encoder: OpusEncoder? = null
    private var decoder: OpusDecoder? = null
    private var player: OpusStreamPlayer? = null
    private var recorder: AudioRecorder? = null

    val display = Display()

    init {
        // 初始化逻辑
        setupBindingStateObserver()
        setupNavigationEventObserver()
        
        // 初始化协议
        protocol = when (settings.transportType) {
            TransportType.WebSockets -> {
                WebsocketProtocol(
                    deviceInfo,
                    deviceInfo.websocket_url,
                    deviceInfo.access_token
                )
            }
            TransportType.MQTT -> {
                MqttProtocol(context, deviceInfo.toMqttConfig())
            }
        }

        // 初始化其他组件
        encoder = OpusEncoder()
        decoder = OpusDecoder()
        player = OpusStreamPlayer()
        recorder = AudioRecorder()

        viewModelScope.launch {
            launch {
                protocol.incomingAudioFlow.map {
                    decoder?.decode(it)
                }.collect { pcmData ->
                    if (pcmData != null && deviceState == DeviceState.SPEAKING && !aborted) {
                        player?.write(pcmData)
                    }
                }
            }

            launch {
                recorder?.startRecording()?.map {
                    encoder?.encode(it)
                }?.collect {
                    if (it != null && deviceState == DeviceState.LISTENING) {
                        protocol.sendAudio(it)
                    }
                }
            }

            launch {
                protocol.incomingJsonFlow.collect { json ->
                    val type = json.optString("type")
                    when (type) {
                        "tts" -> {
                            val state = json.optString("state")
                            when (state) {
                                "start" -> {
                                    schedule {
                                        aborted = false
                                        if (deviceState == DeviceState.IDLE || deviceState == DeviceState.LISTENING) {
                                            deviceState = DeviceState.SPEAKING
                                        }
                                    }
                                }

                                "stop" -> {
                                    schedule {
                                        if (deviceState == DeviceState.SPEAKING) {
                                            Log.i(TAG, "waiting for TTS to stop")
                                            player?.waitForPlaybackCompletion()
                                            Log.i(TAG, "TTS stopped")
                                            if (keepListening) {
                                                protocol.sendStartListening(ListeningMode.AUTO_STOP)
                                                deviceState = DeviceState.LISTENING
                                            } else {
                                                deviceState = DeviceState.IDLE
                                            }
                                        }
                                    }
                                }

                                "sentence_start" -> {
                                    val text = json.optString("text")
                                    schedule {
                                        display.setChatMessage("assistant", text)
                                    }
                                }
                            }
                        }

                        "stt" -> {
                            val text = json.optString("text")
                            schedule {
                                display.setChatMessage("user", text)
                            }
                        }

                        "llm" -> {
                            val emotion = json.optString("emotion")
                            schedule {
                                display.setEmotion(emotion)
                            }
                        }

                        "iot" -> {
                            val commands = json.optJSONArray("commands")
                            Log.i(TAG, "IOT commands: $commands")
                        }
                    }
                }
            }
        }
    }

    // 绑定相关方法
    private fun setupBindingStateObserver() {
        viewModelScope.launch {
            bindingState.collect { bindingState ->
                when (bindingState) {
                    is BindingState.Idle -> {
                        Log.d(TAG, "绑定状态: 空闲")
                    }
                    
                    is BindingState.Checking -> {
                        Log.d(TAG, "绑定状态: 检查中...")
                        _bindingMessage.value = "正在检查绑定状态..."
                    }
                    
                    is BindingState.NotBound -> {
                        Log.i(TAG, "设备未绑定，显示绑定对话框")
                        _shouldShowBindingDialog.value = true
                        _bindingMessage.value = "设备未绑定，请扫描小程序二维码完成绑定"
                    }
                    
                    is BindingState.Bound -> {
                        Log.i(TAG, "✅ 设备已绑定成功")
                        _bindingMessage.value = "设备绑定成功！"
                        _shouldShowBindingDialog.value = false
                        
                        refreshProtocolConnectionIfNeeded(bindingState.websocketUrl)
                    }
                    
                    is BindingState.Error -> {
                        Log.e(TAG, "❌ 绑定错误: ${bindingState.message}")
                        _bindingMessage.value = "绑定错误: ${bindingState.message}"
                        _shouldShowBindingDialog.value = false
                    }
                    
                    is BindingState.CheckTimeout -> {
                        Log.w(TAG, "⏰ 绑定检查超时")
                        _bindingMessage.value = "绑定检查超时，请重试"
                    }
                }
            }
        }
    }

    private fun setupNavigationEventObserver() {
        viewModelScope.launch {
            otaIntegrationService.navigationEvents.collect { event ->
                when (event) {
                    is NavigationEvent.NavigateToChat -> {
                        Log.i(TAG, "🔄 绑定成功，自动跳转到聊天界面")
                        _shouldShowBindingDialog.value = false
                        _bindingMessage.value = "绑定成功！正在初始化语音功能..."
                        
                        navigationEvents.emit("navigate_to_chat")
                        otaIntegrationService.clearNavigationEvent()
                    }
                    null -> {
                        // 无导航事件
                    }
                }
            }
        }
    }

    private fun refreshProtocolConnectionIfNeeded(newWebSocketUrl: String) {
        viewModelScope.launch {
            try {
                Log.i(TAG, "🔄 绑定成功，检查是否需要更新WebSocket连接...")
                
                if (protocol is WebsocketProtocol) {
                    val currentUrl = otaIntegrationService.getCurrentWebSocketUrl()
                    if (currentUrl != newWebSocketUrl) {
                        Log.i(TAG, "🔄 WebSocket URL已更新，准备重新连接...")
                        Log.i(TAG, "旧URL: $currentUrl")
                        Log.i(TAG, "新URL: $newWebSocketUrl")
                        
                        _bindingMessage.value = "WebSocket配置已更新"
                    } else {
                        Log.i(TAG, "✅ WebSocket URL无变化，保持当前连接")
                        _bindingMessage.value = "设备配置已是最新"
                    }
                } else {
                    Log.i(TAG, "ℹ️ 当前使用非WebSocket协议，跳过连接更新")
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "❌ 更新协议连接失败", e)
                _bindingMessage.value = "连接更新失败: ${e.message}"
            }
        }
    }

    fun manualRefreshBinding() {
        Log.i(TAG, "🔄 手动刷新绑定状态...")
        viewModelScope.launch {
            try {
                val otaResult = otaIntegrationService.refreshOtaConfig()
                if (otaResult != null) {
                    _bindingMessage.value = "绑定状态已刷新"
                } else {
                    _bindingMessage.value = "刷新失败，请检查网络连接"
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ 手动刷新失败", e)
                _bindingMessage.value = "刷新失败: ${e.message}"
            }
        }
    }

    fun dismissBindingDialog() {
        _shouldShowBindingDialog.value = false
        otaIntegrationService.stopBindingMonitor()
    }

    fun clearBindingMessage() {
        _bindingMessage.value = null
    }

    // STT相关方法
    fun toggleChatState() {
        viewModelScope.launch {
            when (deviceState) {
                DeviceState.ACTIVATING -> {
                    reboot()
                }

                DeviceState.IDLE -> {
                    if (protocol.openAudioChannel()) {
                        keepListening = true
                        protocol.sendStartListening(ListeningMode.AUTO_STOP)
                        deviceState = DeviceState.LISTENING
                    } else {
                        deviceState = DeviceState.IDLE
                    }
                }

                DeviceState.SPEAKING -> {
                    abortSpeaking(AbortReason.NONE)
                }

                DeviceState.LISTENING -> {
                    protocol.closeAudioChannel()
                }

                else -> {
                    Log.e(TAG, "Protocol not initialized or invalid state")
                }
            }
        }
    }

    fun startListening() {
        viewModelScope.launch {
            if (deviceState == DeviceState.ACTIVATING) {
                reboot()
                return@launch
            }

            keepListening = false
            if (deviceState == DeviceState.IDLE) {
                if (!protocol.isAudioChannelOpened()) {
                    deviceState = DeviceState.CONNECTING
                    if (!protocol.openAudioChannel()) {
                        deviceState = DeviceState.IDLE
                        return@launch
                    }
                }
                protocol.sendStartListening(ListeningMode.MANUAL)
                deviceState = DeviceState.LISTENING
            } else if (deviceState == DeviceState.SPEAKING) {
                abortSpeaking(AbortReason.NONE)
                protocol.sendStartListening(ListeningMode.MANUAL)
                delay(120)
                deviceState = DeviceState.LISTENING
            }
        }
    }

    private fun reboot() {
        // Implement the reboot logic here
    }

    fun abortSpeaking(reason: AbortReason) {
        Log.i(TAG, "Abort speaking")
        aborted = true
        viewModelScope.launch {
            protocol.sendAbortSpeaking(reason)
        }
    }
    
    private fun schedule(task: suspend () -> Unit) {
        viewModelScope.launch {
            task()
        }
    }

    fun stopListening() {
        viewModelScope.launch {
            if (deviceState == DeviceState.LISTENING) {
                protocol.sendStopListening()
                deviceState = DeviceState.IDLE
            }
        }
    }

    override fun onCleared() {
        otaIntegrationService.cleanup()
        
        protocol.dispose()
        encoder?.release()
        decoder?.release()
        player?.stop()
        recorder?.stopRecording()
        super.onCleared()
    }
}

enum class DeviceState {
    UNKNOWN,
    STARTING,
    WIFI_CONFIGURING,
    IDLE,
    CONNECTING,
    LISTENING,
    SPEAKING,
    UPGRADING,
    ACTIVATING,
    FATAL_ERROR
}

class Display {
    val chatFlow = MutableStateFlow<List<Message>>(listOf())
    val emotionFlow = MutableStateFlow<String>("neutral")
    
    fun setChatMessage(sender: String, message: String) {
        chatFlow.value = chatFlow.value + Message(sender, message)
    }

    fun setEmotion(emotion: String) {
        emotionFlow.value = emotion
    }
}

val df = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())

data class Message(
    val sender: String = "",
    val message: String = "",
    val nowInString: String = df.format(System.currentTimeMillis())
)
*/ 