package info.dourok.voicebot.data

import info.dourok.voicebot.ApplicationScope
import info.dourok.voicebot.Ota
import info.dourok.voicebot.data.model.OtaResult
import info.dourok.voicebot.data.model.ServerFormData
import info.dourok.voicebot.data.model.ServerType
import info.dourok.voicebot.data.model.TransportType
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject
import javax.inject.Singleton

sealed class FormResult{
    object SelfHostResult : FormResult()
    class XiaoZhiResult(val otaResult: OtaResult?) : FormResult()
}

// :feature:form/data/FormRepository.kt
interface FormRepository {
    suspend fun submitForm(formData: ServerFormData)

    val resultFlow : StateFlow<FormResult?>
}




@Singleton
class FormRepositoryImpl @Inject constructor(
    private val ota: Ota,
    private val settingsRepository: SettingsRepository,
    @ApplicationScope private val coroutineScope: CoroutineScope,
) : FormRepository {

    override suspend fun submitForm(formData: ServerFormData) {
        if(formData.serverType == ServerType.XiaoZhi) {
            settingsRepository.transportType = formData.xiaoZhiConfig.transportType
            settingsRepository.webSocketUrl = formData.xiaoZhiConfig.webSocketUrl
            
            // 根据传输类型决定是否需要OTA检查
            if (formData.xiaoZhiConfig.transportType == TransportType.MQTT) {
                // MQTT模式需要OTA检查来获取MQTT配置
                ota.checkVersion(formData.xiaoZhiConfig.qtaUrl)
                settingsRepository.mqttConfig = ota.otaResult?.mqttConfig
                resultFlow.value = FormResult.XiaoZhiResult(ota.otaResult)
            } else {
                // WebSockets模式下不需要OTA检查，直接使用WebSocket URL
                settingsRepository.mqttConfig = null
                resultFlow.value = FormResult.XiaoZhiResult(null)
            }
        } else {
            settingsRepository.transportType = formData.selfHostConfig.transportType
            settingsRepository.webSocketUrl = formData.selfHostConfig.webSocketUrl
            settingsRepository.mqttConfig = null  // SelfHost模式固定为WebSockets，清除MQTT配置
            resultFlow.value = FormResult.SelfHostResult
        }
        print(ota.deviceInfo)
    }

    override val resultFlow: MutableStateFlow<FormResult?> = MutableStateFlow(null)
}
