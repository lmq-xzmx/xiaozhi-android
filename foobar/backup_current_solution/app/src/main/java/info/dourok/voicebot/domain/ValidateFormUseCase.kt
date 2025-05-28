package info.dourok.voicebot.domain

import info.dourok.voicebot.data.model.ServerFormData
import info.dourok.voicebot.data.model.ServerType
import info.dourok.voicebot.data.model.TransportType
import info.dourok.voicebot.data.model.ValidationResult
import javax.inject.Inject

// :feature:form/domain/ValidateFormUseCase.kt
class ValidateFormUseCase @Inject constructor() {
    operator fun invoke(formData: ServerFormData): ValidationResult {
        val errors = mutableMapOf<String, String>()

        when (formData.serverType) {
            ServerType.XiaoZhi -> {
                if (formData.xiaoZhiConfig.webSocketUrl.isEmpty()) {
                    errors["xiaoZhiWebSocketUrl"] = "WebSocket URL不能为空"
                }
                if (formData.xiaoZhiConfig.qtaUrl.isEmpty()) {
                    errors["xiaoZhiQtaUrl"] = "QTA URL不能为空"
                }
                
                // 验证协议类型与URL的匹配性
                val url = formData.xiaoZhiConfig.webSocketUrl
                val transportType = formData.xiaoZhiConfig.transportType
                
                when (transportType) {
                    TransportType.None -> {
                        errors["xiaoZhiConfig"] = "请选择传输类型"
                    }
                    TransportType.WebSockets -> {
                        if (!url.startsWith("ws://") && !url.startsWith("wss://")) {
                            errors["xiaoZhiConfig"] = "WebSocket传输类型需要ws://或wss://协议的URL"
                        }
                    }
                    TransportType.MQTT -> {
                        if (url.startsWith("ws://") || url.startsWith("wss://")) {
                            errors["xiaoZhiConfig"] = "MQTT传输类型不应使用WebSocket URL，请选择WebSockets传输类型"
                        }
                    }
                }
            }
            ServerType.SelfHost -> {
                if (formData.selfHostConfig.webSocketUrl.isEmpty()) {
                    errors["selfHostWebSocketUrl"] = "WebSocket URL不能为空"
                }
                
                // 验证SelfHost配置
                val url = formData.selfHostConfig.webSocketUrl
                if (!url.startsWith("ws://") && !url.startsWith("wss://")) {
                    errors["selfHostConfig"] = "自托管配置需要有效的WebSocket URL (ws://或wss://)"
                }
            }
        }

        return ValidationResult(
            isValid = errors.isEmpty(),
            errors = errors
        )
    }
}