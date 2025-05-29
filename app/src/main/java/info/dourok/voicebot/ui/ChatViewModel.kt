package info.dourok.voicebot.ui

import android.content.Context
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
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
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Locale
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    @NavigationEvents private val navigationEvents: MutableSharedFlow<String>,
    private val deviceInfo: DeviceInfo,
    private val settings: SettingsRepository,
    private val otaIntegrationService: OtaIntegrationService
) : ViewModel() {

    companion object {
        private const val TAG = "ChatViewModel_Phase2_PureServerVAD"
    }

    // ============ 第二阶段：纯服务器端VAD驱动架构 ============
    // 移除复杂的客户端状态管理变量：
    // - 移除 keepListening: 完全依赖服务器端控制
    // - 保留 aborted: 仍需要用于TTS打断控制
    private var aborted = false

    // 音频流管理：简化为单一协程控制
    private var currentAudioJob: Job? = null

    var deviceState by mutableStateOf(DeviceState.UNKNOWN)
        private set

    private val _shouldShowBindingDialog = MutableStateFlow(false)
    val shouldShowBindingDialog: StateFlow<Boolean> = _shouldShowBindingDialog.asStateFlow()

    private val _bindingMessage = MutableStateFlow<String?>(null)
    val bindingMessage: StateFlow<String?> = _bindingMessage.asStateFlow()

    // 绑定状态流
    val bindingState: StateFlow<BindingState> = otaIntegrationService.bindingState

    // 核心组件 - 保持不变
    private lateinit var protocol: Protocol
    private var encoder: OpusEncoder? = null
    private var decoder: OpusDecoder? = null
    private var player: OpusStreamPlayer? = null
    private var recorder: AudioRecorder? = null

    val display = Display()

    init {
        Log.i(TAG, "🚀 启动第二阶段：纯服务器端VAD驱动模式（ESP32完全兼容）")
        
        // 绑定相关初始化
        setupBindingStateObserver()
        setupNavigationEventObserver()
        
        // 初始化协议
        protocol = when (settings.transportType) {
            TransportType.WebSockets -> {
                Log.i(TAG, "📡 初始化WebSocket协议")
                WebsocketProtocol(
                    deviceInfo,
                    settings.webSocketUrl ?: "ws://47.122.144.73:8000/xiaozhi/v1/",
                    settings.deviceId ?: "default-device-id"
                )
            }
            TransportType.MQTT -> {
                Log.i(TAG, "📡 初始化MQTT协议")
                MqttProtocol(context, createMqttConfig())
            }
        }

        // 初始化音频组件
        initializeAudioComponents()
        
        // ⚠️ 关键修复：观察协议消息流程 - 这是处理STT响应的核心环节
        observeProtocolMessages()

        // 启动完整的语音交互流程
        viewModelScope.launch {
            // 步骤1：启动协议（现在会自动建立WebSocket连接）
            Log.i(TAG, "🔄 步骤1：启动协议连接...")
            try {
                protocol.start()  // 现在这里会建立WebSocket连接
                deviceState = DeviceState.CONNECTING
                
                // 检查连接是否成功建立
                if (protocol.isAudioChannelOpened()) {
                    Log.i(TAG, "✅ 音频通道已建立成功")
                    
                    // 发送监听指令（与旧项目一致）
                    protocol.sendStartListening(ListeningMode.AUTO_STOP)
                    deviceState = DeviceState.LISTENING
                    
                    // 步骤2：启动音频播放流（TTS音频处理）
                    Log.i(TAG, "🔄 步骤2：启动TTS音频处理流...")
                    startTTSPlaybackFlow()
                    
                    // 步骤3：启动音频录制和传输流（STT音频发送）
                    Log.i(TAG, "🔄 步骤3：启动STT音频录制流...")
                    startAudioRecordingFlow()
                    
                    Log.i(TAG, "🎉 纯服务器端VAD模式启动完成，STT功能已就绪！")
                    
                } else {
                    Log.e(TAG, "❌ 协议启动后音频通道仍未建立")
                    Log.e(TAG, "🚫 跳过音频流程启动，避免WebSocket null错误")
                    deviceState = DeviceState.FATAL_ERROR
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "❌ 协议启动失败", e)
                deviceState = DeviceState.FATAL_ERROR
            }
        }
    }

    /**
     * 创建MQTT配置（临时方法，替代deviceInfo.toMqttConfig()）
     */
    private fun createMqttConfig(): info.dourok.voicebot.data.model.MqttConfig {
        return info.dourok.voicebot.data.model.MqttConfig(
            endpoint = "tcp://47.122.144.73:1883",
            clientId = settings.deviceId ?: "default-device-id",
            username = "xiaozhi",
            password = "password123",
            publishTopic = "xiaozhi/device/${settings.deviceId ?: "default"}/pub",
            subscribeTopic = "xiaozhi/device/${settings.deviceId ?: "default"}/sub"
        )
    }

    /**
     * 初始化音频组件 - 与ESP32端参数一致
     */
    private fun initializeAudioComponents() {
        Log.i(TAG, "🎵 初始化音频组件（ESP32兼容参数）")
        
        // 第二阶段：使用ESP32兼容的音频参数
        val sampleRate = 16000  // 16kHz
        val channels = 1        // 单声道
        val frameSizeMs = 60    // 60ms帧
        
        encoder = OpusEncoder(sampleRate, channels, frameSizeMs)
        decoder = OpusDecoder(sampleRate, channels, frameSizeMs)
        player = OpusStreamPlayer(sampleRate, channels, frameSizeMs)
        recorder = AudioRecorder(sampleRate, channels, frameSizeMs)
        
        Log.i(TAG, "✅ 音频组件初始化完成")
    }

    /**
     * 处理STT结果 - 纯展示，无状态管理
     */
    private fun handleSttMessage(json: org.json.JSONObject) {
        Log.i(TAG, "🎯 *** 开始处理STT消息 ***")
        Log.d(TAG, "STT消息完整内容: ${json.toString(2)}")
        
        // 尝试从多个可能的字段获取文本
        val possibleTextFields = listOf("text", "transcript", "result", "recognition", "data")
        var text = ""
        var foundField = ""
        
        for (field in possibleTextFields) {
            if (json.has(field)) {
                val value = json.optString(field)
                if (value.isNotEmpty()) {
                    text = value
                    foundField = field
                    Log.i(TAG, "🎯 从字段 '$field' 获取到STT文本: '$text'")
                    break
                }
            }
        }
        
        if (text.isNotEmpty()) {
            Log.i(TAG, ">> $text")  // 与旧项目保持一致的日志格式
            Log.i(TAG, "✅ STT识别成功，文本长度: ${text.length}")
            
            // 纯粹的UI展示，无状态变更
            schedule {
                Log.i(TAG, "📱 正在更新UI显示STT结果...")
                display.setChatMessage("user", text)
                Log.i(TAG, "✅ UI更新完成")
            }
            
            Log.i(TAG, "📝 STT结果已展示，等待服务器端LLM处理...")
            // 不做任何状态管理，完全依赖服务器端控制
        } else {
            Log.w(TAG, "📭 收到空的STT结果或无法识别的STT格式")
            Log.w(TAG, "可用字段: ${json.keys().asSequence().toList()}")
            Log.w(TAG, "完整JSON: ${json.toString()}")
        }
        
        Log.i(TAG, "🎯 *** STT消息处理完成 ***")
    }

    /**
     * 处理TTS消息 - 简化状态管理
     */
    private fun handleTtsMessage(json: org.json.JSONObject) {
        val state = json.optString("state")
        
        when (state) {
            "start" -> {
                Log.i(TAG, "🔊 服务器端开始TTS播放")
                schedule {
                    aborted = false
                    if (deviceState == DeviceState.IDLE || deviceState == DeviceState.LISTENING) {
                        deviceState = DeviceState.SPEAKING
                    }
                }
            }
            
            "stop" -> {
                Log.i(TAG, "🔇 服务器端TTS播放结束")
                schedule {
                    if (deviceState == DeviceState.SPEAKING) {
                        Log.i(TAG, "⏳ 等待TTS播放完成...")
                        player?.waitForPlaybackCompletion()
                        Log.i(TAG, "✅ TTS播放完成")
                        
                        // 恢复监听状态（与旧项目一致）
                        if (!aborted) {
                            Log.i(TAG, "🔄 TTS结束，恢复监听模式...")
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
                if (text.isNotEmpty()) {
                    Log.i(TAG, "<< $text")
                    schedule {
                        display.setChatMessage("assistant", text)
                    }
                }
            }
            
            else -> {
                Log.d(TAG, "🎵 TTS状态: $state")
            }
        }
    }

    /**
     * 处理监听指令 - 服务器端控制
     */
    private fun handleListenMessage(json: org.json.JSONObject) {
        val state = json.optString("state")
        
        when (state) {
            "start" -> {
                Log.i(TAG, "📡 服务器端指示开始监听")
                deviceState = DeviceState.LISTENING
            }
            
            "stop" -> {
                Log.i(TAG, "📡 服务器端指示停止监听")
                // 注意：不主动停止音频流，让服务器端完全控制
            }
            
            else -> {
                Log.d(TAG, "👂 监听状态: $state")
            }
        }
    }

    /**
     * 处理LLM消息
     */
    private fun handleLlmMessage(json: org.json.JSONObject) {
        val emotion = json.optString("emotion")
        if (emotion.isNotEmpty()) {
            schedule {
                display.setEmotion(emotion)
            }
        }
    }

    /**
     * 处理IoT消息
     */
    private fun handleIotMessage(json: org.json.JSONObject) {
        val commands = json.optJSONArray("commands")
        Log.i(TAG, "🏠 IoT commands: $commands")
        // IoT命令处理逻辑
    }

    /**
     * 处理错误消息
     */
    private fun handleErrorMessage(json: org.json.JSONObject) {
        val message = json.optString("message", "未知错误")
        Log.e(TAG, "❌ 服务器错误: $message")
        deviceState = DeviceState.FATAL_ERROR
    }

    // ============ 绑定相关方法 - 保持不变 ============
    
    private fun setupBindingStateObserver() {
        viewModelScope.launch {
            bindingState.collect { bindingState ->
                when (bindingState) {
                    is BindingState.Unknown -> {
                        Log.d(TAG, "绑定状态: 未知")
                    }
                    
                    is BindingState.NeedsBinding -> {
                        Log.i(TAG, "设备需要绑定，激活码: ${bindingState.activationCode}")
                        _shouldShowBindingDialog.value = true
                        _bindingMessage.value = "设备需要绑定，请扫描小程序二维码完成绑定"
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

    // ============ 第二阶段：简化的语音交互控制 ============

    /**
     * 切换语音交互状态 - 简化版本，主要用于开始/停止纯服务器端VAD模式
     */
    fun toggleChatState() {
        viewModelScope.launch {
            when (deviceState) {
                DeviceState.IDLE, DeviceState.UNKNOWN -> {
                    Log.i(TAG, "🔄 重新启动语音模式...")
                    // 重启应用来恢复语音功能
                    deviceState = DeviceState.STARTING
                }

                DeviceState.LISTENING -> {
                    Log.i(TAG, "🛑 停止语音模式...")
                    stopAudioFlow()
                    protocol.closeAudioChannel()
                    deviceState = DeviceState.IDLE
                }

                DeviceState.SPEAKING -> {
                    Log.i(TAG, "⏸️ 打断TTS播放...")
                    abortSpeaking(AbortReason.NONE)
                }

                else -> {
                    Log.w(TAG, "⚠️ 当前状态不支持切换: $deviceState")
                }
            }
        }
    }

    /**
     * 停止音频流
     */
    private fun stopAudioFlow() {
        currentAudioJob?.cancel()
        currentAudioJob = null
        recorder?.stopRecording()
        Log.i(TAG, "🛑 音频流已停止")
    }

    /**
     * 打断TTS播放
     */
    fun abortSpeaking(reason: AbortReason) {
        Log.i(TAG, "⏸️ 打断TTS播放")
        aborted = true
        viewModelScope.launch {
            protocol.sendAbortSpeaking(reason)
        }
    }

    /**
     * 调度任务到主线程
     */
    private fun schedule(task: suspend () -> Unit) {
        viewModelScope.launch {
            task()
        }
    }

    /**
     * 清理资源
     */
    override fun onCleared() {
        Log.i(TAG, "🧹 清理ChatViewModel资源...")
        
        // 停止音频流
        stopAudioFlow()
        
        // 清理OTA集成服务
        otaIntegrationService.cleanup()
        
        // 清理协议和音频组件
        protocol.dispose()
        encoder?.release()
        decoder?.release()
        player?.stop()
        recorder?.stopRecording()
        
        super.onCleared()
        
        Log.i(TAG, "✅ ChatViewModel资源清理完成")
    }

    // ============ 兼容性方法 - 保持接口一致性 ============
    
    @Deprecated("第二阶段已移除手动监听模式，使用toggleChatState()替代", ReplaceWith("toggleChatState()"))
    fun startListening() {
        Log.w(TAG, "⚠️ startListening()已弃用，使用纯服务器端VAD模式")
        toggleChatState()
    }

    @Deprecated("第二阶段已移除手动监听模式，使用toggleChatState()替代", ReplaceWith("toggleChatState()"))
    fun stopListening() {
        Log.w(TAG, "⚠️ stopListening()已弃用，使用纯服务器端VAD模式")
        if (deviceState == DeviceState.LISTENING) {
            toggleChatState()
        }
    }

    private fun reboot() {
        Log.i(TAG, "🔄 重启设备...")
        deviceState = DeviceState.ACTIVATING
        // 重启逻辑
    }

    // ============ 关键修复：观察协议消息流程 - 这是处理STT响应的核心环节 ============
    private fun observeProtocolMessages() {
        viewModelScope.launch {
            try {
                Log.i(TAG, "🔍 开始观察协议消息流程...")
                protocol.incomingJsonFlow.collect { json ->
                    val type = json.optString("type")
                    Log.i(TAG, "📥 收到服务器消息: type='$type'")
                    Log.d(TAG, "完整消息内容: ${json.toString(2)}")
                    
                    when (type) {
                        "stt" -> {
                            Log.i(TAG, "🎯 *** 处理STT消息 ***")
                            handleSttMessage(json)
                        }
                        "tts" -> {
                            Log.i(TAG, "🔊 处理TTS消息")
                            handleTtsMessage(json)
                        }
                        "listen" -> {
                            Log.i(TAG, "👂 处理监听指令")
                            handleListenMessage(json)
                        }
                        "llm" -> {
                            Log.i(TAG, "🤖 处理LLM消息")
                            handleLlmMessage(json)
                        }
                        "iot" -> {
                            Log.i(TAG, "🏠 处理IoT消息")
                            handleIotMessage(json)
                        }
                        "error" -> {
                            Log.e(TAG, "❌ 处理错误消息")
                            handleErrorMessage(json)
                        }
                        else -> {
                            Log.w(TAG, "🤷 未处理的消息类型: '$type'")
                            Log.w(TAG, "原始消息: ${json.toString()}")
                            
                            // 检查是否包含可能的STT数据
                            if (json.has("text") || json.has("transcript") || json.has("result")) {
                                Log.w(TAG, "🔍 可能是无类型的STT消息，尝试处理...")
                                handleSttMessage(json)
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ 观察协议消息流程失败", e)
            }
        }
    }

    /**
     * 启动TTS音频播放流程
     */
    private fun startTTSPlaybackFlow() {
        viewModelScope.launch {
            try {
                val sampleRate = 16000  // 与录制保持一致
                val channels = 1
                val frameSizeMs = 60
                player = OpusStreamPlayer(sampleRate, channels, frameSizeMs)
                decoder = OpusDecoder(sampleRate, channels, frameSizeMs)
                
                // 启动TTS音频播放流
                player?.start(protocol.incomingAudioFlow.map { audioData ->
                    Log.d(TAG, "🔊 收到TTS音频数据: ${audioData.size}字节")
                    decoder?.decode(audioData)
                })
                
                Log.i(TAG, "✅ TTS音频播放流启动完成")
            } catch (e: Exception) {
                Log.e(TAG, "❌ TTS音频播放流启动失败", e)
            }
        }
    }

    /**
     * 启动音频录制和传输流程
     */
    private fun startAudioRecordingFlow() {
        viewModelScope.launch {
            try {
                val sampleRate = 16000
                val channels = 1
                val frameSizeMs = 60
                encoder = OpusEncoder(sampleRate, channels, frameSizeMs)
                recorder = AudioRecorder(sampleRate, channels, frameSizeMs)
                
                // 启动音频录制流
                val audioFlow = recorder?.startRecording()
                val opusFlow = audioFlow?.map { pcmData ->
                    encoder?.encode(pcmData)
                }
                
                Log.i(TAG, "✅ STT音频录制流已启动，开始发送音频数据...")
                
                // 收集并发送音频数据（纯服务器端VAD模式）
                opusFlow?.collect { opusData ->
                    opusData?.let { data ->
                        // 防御性检查：确保WebSocket仍然连接
                        if (protocol.isAudioChannelOpened()) {
                            protocol.sendAudio(data)
                            // 每秒记录一次音频发送状态
                            if (System.currentTimeMillis() % 1000 < 100) {
                                Log.d(TAG, "🎤 纯服务器端VAD：持续发送音频 ${data.size}字节")
                            }
                        } else {
                            Log.w(TAG, "⚠️ WebSocket连接已断开，停止音频发送")
                            return@collect
                        }
                    }
                }
                
                Log.i(TAG, "✅ STT音频录制流启动完成")
            } catch (e: Exception) {
                Log.e(TAG, "❌ STT音频录制流启动失败", e)
            }
        }
    }
}

// ============ 数据类和枚举 - 保持不变 ============

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
