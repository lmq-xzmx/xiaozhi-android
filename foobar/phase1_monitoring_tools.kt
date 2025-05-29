/**
 * 第一阶段架构稳定性监控工具
 * 用于渐进式迁移的Phase 1阶段
 */
package info.dourok.voicebot.foobar

import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicInteger

object Phase1MonitoringTools {
    private const val TAG = "Phase1Monitor"
    
    // 监控状态
    private val _architectureStatus = MutableStateFlow(ArchitectureStatus())
    val architectureStatus: StateFlow<ArchitectureStatus> = _architectureStatus.asStateFlow()
    
    // 性能指标
    private val audioFrameCount = AtomicLong(0)
    private val sttResponseCount = AtomicInteger(0)
    private val connectionDropCount = AtomicInteger(0)
    private var lastConnectionTime = 0L
    private var lastSttTime = 0L
    
    /**
     * 架构状态数据类
     */
    data class ArchitectureStatus(
        val otaFunctional: Boolean = false,
        val websocketConnected: Boolean = false,
        val mqttConnected: Boolean = false,
        val audioRecording: Boolean = false,
        val sttWorking: Boolean = false,
        val ttsWorking: Boolean = false,
        val overallHealth: HealthStatus = HealthStatus.UNKNOWN
    ) {
        val isStable: Boolean
            get() = (websocketConnected || mqttConnected) && 
                    audioRecording && sttWorking && 
                    overallHealth != HealthStatus.CRITICAL
                    
        val isReadyForPhase2: Boolean
            get() = isStable && otaFunctional && overallHealth == HealthStatus.HEALTHY
    }
    
    enum class HealthStatus {
        HEALTHY,    // 所有功能正常
        WARNING,    // 部分功能异常但可继续工作
        CRITICAL,   // 关键功能异常
        UNKNOWN     // 初始状态
    }
    
    /**
     * 记录OTA功能状态
     */
    fun reportOtaStatus(isWorking: Boolean, details: String = "") {
        Log.i(TAG, "【OTA状态】${if (isWorking) "✅" else "❌"} $details")
        updateStatus { it.copy(otaFunctional = isWorking) }
    }
    
    /**
     * 记录WebSocket连接状态
     */
    fun reportWebSocketStatus(isConnected: Boolean, url: String = "") {
        Log.i(TAG, "【WebSocket状态】${if (isConnected) "✅" else "❌"} $url")
        if (isConnected) {
            lastConnectionTime = System.currentTimeMillis()
        } else {
            connectionDropCount.incrementAndGet()
        }
        updateStatus { it.copy(websocketConnected = isConnected) }
    }
    
    /**
     * 记录MQTT连接状态
     */
    fun reportMqttStatus(isConnected: Boolean, broker: String = "") {
        Log.i(TAG, "【MQTT状态】${if (isConnected) "✅" else "❌"} $broker")
        if (isConnected) {
            lastConnectionTime = System.currentTimeMillis()
        } else {
            connectionDropCount.incrementAndGet()
        }
        updateStatus { it.copy(mqttConnected = isConnected) }
    }
    
    /**
     * 记录音频录制状态
     */
    fun reportAudioRecordingStatus(isRecording: Boolean, frameSize: Int = 0) {
        if (isRecording && frameSize > 0) {
            audioFrameCount.incrementAndGet()
            // 每100帧记录一次
            if (audioFrameCount.get() % 100 == 0L) {
                Log.i(TAG, "【音频录制】✅ 已处理${audioFrameCount.get()}帧，当前帧大小: ${frameSize}字节")
            }
        } else if (!isRecording) {
            Log.w(TAG, "【音频录制】❌ 录制中断")
        }
        updateStatus { it.copy(audioRecording = isRecording) }
    }
    
    /**
     * 记录STT功能状态
     */
    fun reportSttStatus(isWorking: Boolean, recognizedText: String = "", latencyMs: Long = 0) {
        if (isWorking) {
            sttResponseCount.incrementAndGet()
            lastSttTime = System.currentTimeMillis()
            Log.i(TAG, "【STT状态】✅ 识别成功: '$recognizedText' (延迟: ${latencyMs}ms)")
        } else {
            Log.w(TAG, "【STT状态】❌ 识别失败")
        }
        updateStatus { it.copy(sttWorking = isWorking) }
    }
    
    /**
     * 记录TTS功能状态
     */
    fun reportTtsStatus(isWorking: Boolean, details: String = "") {
        Log.i(TAG, "【TTS状态】${if (isWorking) "✅" else "❌"} $details")
        updateStatus { it.copy(ttsWorking = isWorking) }
    }
    
    /**
     * 获取性能统计报告
     */
    fun getPerformanceReport(): PerformanceReport {
        val currentTime = System.currentTimeMillis()
        val connectionUptime = if (lastConnectionTime > 0) currentTime - lastConnectionTime else 0
        val sttAvgLatency = if (lastSttTime > 0) currentTime - lastSttTime else 0
        
        return PerformanceReport(
            audioFramesProcessed = audioFrameCount.get(),
            sttResponseCount = sttResponseCount.get(),
            connectionDrops = connectionDropCount.get(),
            connectionUptimeMs = connectionUptime,
            lastSttLatencyMs = sttAvgLatency
        )
    }
    
    data class PerformanceReport(
        val audioFramesProcessed: Long,
        val sttResponseCount: Int,
        val connectionDrops: Int,
        val connectionUptimeMs: Long,
        val lastSttLatencyMs: Long
    ) {
        fun toReadableString(): String {
            return """
                🎵 音频帧数: $audioFramesProcessed
                🎤 STT响应次数: $sttResponseCount
                📡 连接中断次数: $connectionDrops
                ⏱️ 连接持续时间: ${connectionUptimeMs / 1000}秒
                ⚡ 最后STT延迟: ${lastSttLatencyMs}ms
            """.trimIndent()
        }
    }
    
    /**
     * 更新架构状态并计算整体健康度
     */
    private fun updateStatus(update: (ArchitectureStatus) -> ArchitectureStatus) {
        val newStatus = update(_architectureStatus.value)
        val healthStatus = calculateHealthStatus(newStatus)
        _architectureStatus.value = newStatus.copy(overallHealth = healthStatus)
        
        // 记录状态变化
        Log.d(TAG, "【架构状态更新】${healthStatus.name}: ${getStatusSummary(newStatus)}")
    }
    
    /**
     * 计算整体健康状态
     */
    private fun calculateHealthStatus(status: ArchitectureStatus): HealthStatus {
        val criticalFunctions = listOf(
            status.websocketConnected || status.mqttConnected, // 至少一种连接方式
            status.audioRecording,
            status.sttWorking
        )
        
        val optionalFunctions = listOf(
            status.otaFunctional,
            status.ttsWorking
        )
        
        return when {
            criticalFunctions.all { it } && optionalFunctions.all { it } -> HealthStatus.HEALTHY
            criticalFunctions.all { it } -> HealthStatus.WARNING
            criticalFunctions.any { !it } -> HealthStatus.CRITICAL
            else -> HealthStatus.UNKNOWN
        }
    }
    
    /**
     * 获取状态摘要
     */
    private fun getStatusSummary(status: ArchitectureStatus): String {
        return "OTA:${if (status.otaFunctional) "✅" else "❌"} " +
               "WebSocket:${if (status.websocketConnected) "✅" else "❌"} " +
               "MQTT:${if (status.mqttConnected) "✅" else "❌"} " +
               "音频:${if (status.audioRecording) "✅" else "❌"} " +
               "STT:${if (status.sttWorking) "✅" else "❌"} " +
               "TTS:${if (status.ttsWorking) "✅" else "❌"}"
    }
    
    /**
     * 生成第一阶段验收报告
     */
    fun generatePhase1Report(): String {
        val status = _architectureStatus.value
        val performance = getPerformanceReport()
        
        return """
            # 第一阶段架构稳定性报告
            
            ## 📊 整体状态
            健康度: ${status.overallHealth.name}
            是否稳定: ${if (status.isStable) "✅ 是" else "❌ 否"}
            是否准备进入第二阶段: ${if (status.isReadyForPhase2) "✅ 是" else "❌ 否"}
            
            ## 🔧 功能状态
            - OTA功能: ${if (status.otaFunctional) "✅ 正常" else "❌ 异常"}
            - WebSocket连接: ${if (status.websocketConnected) "✅ 已连接" else "❌ 未连接"}
            - MQTT连接: ${if (status.mqttConnected) "✅ 已连接" else "❌ 未连接"}
            - 音频录制: ${if (status.audioRecording) "✅ 正常" else "❌ 异常"}
            - STT识别: ${if (status.sttWorking) "✅ 正常" else "❌ 异常"}
            - TTS播放: ${if (status.ttsWorking) "✅ 正常" else "❌ 异常"}
            
            ## 📈 性能指标
            ${performance.toReadableString()}
            
            ## 🎯 验收结论
            ${if (status.isReadyForPhase2) {
                "✅ 第一阶段验收通过，可以开始第二阶段纯服务器端VAD迁移"
            } else {
                "⚠️ 第一阶段仍有问题需要解决，建议修复后再进入第二阶段"
            }}
        """.trimIndent()
    }
    
    /**
     * 重置监控数据
     */
    fun reset() {
        audioFrameCount.set(0)
        sttResponseCount.set(0)
        connectionDropCount.set(0)
        lastConnectionTime = 0L
        lastSttTime = 0L
        _architectureStatus.value = ArchitectureStatus()
        Log.i(TAG, "📊 监控数据已重置")
    }
} 