package info.dourok.voicebot.data

import info.dourok.voicebot.ApplicationScope
import info.dourok.voicebot.Ota
import info.dourok.voicebot.data.model.OtaResult
import info.dourok.voicebot.data.model.ServerFormData
import info.dourok.voicebot.data.model.ServerType
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject
import javax.inject.Singleton
import android.util.Log

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
        Log.i("FormRepository", "Submitting form data: serverType=${formData.serverType}")
        
        if(formData.serverType == ServerType.XiaoZhi) {
            Log.i("FormRepository", "Processing XiaoZhi configuration")
            settingsRepository.transportType = formData.xiaoZhiConfig.transportType
            settingsRepository.webSocketUrl = formData.xiaoZhiConfig.webSocketUrl
            
            try {
                Log.i("FormRepository", "Starting OTA check with URL: ${formData.xiaoZhiConfig.qtaUrl}")
                val otaSuccess = ota.checkVersion(formData.xiaoZhiConfig.qtaUrl)
                
                if (otaSuccess && ota.otaResult != null) {
                    Log.i("FormRepository", "OTA check successful")
                    settingsRepository.mqttConfig = ota.otaResult?.mqttConfig
                } else {
                    Log.w("FormRepository", "OTA check failed or returned null, continuing with WebSocket mode")
                    // 对于WebSocket模式，不需要MQTT配置，可以继续
                    settingsRepository.mqttConfig = null
                }
                
                resultFlow.value = FormResult.XiaoZhiResult(ota.otaResult)
                
            } catch (e: Exception) {
                Log.e("FormRepository", "OTA check failed with exception: ${e.message}", e)
                // 即使OTA检查失败，也可以使用WebSocket模式
                settingsRepository.mqttConfig = null
                resultFlow.value = FormResult.XiaoZhiResult(null)
            }
            
        } else {
            Log.i("FormRepository", "Processing SelfHost configuration")
            settingsRepository.transportType = formData.selfHostConfig.transportType
            settingsRepository.webSocketUrl = formData.selfHostConfig.webSocketUrl
            settingsRepository.mqttConfig = null
            resultFlow.value = FormResult.SelfHostResult
        }
        
        Log.i("FormRepository", "DeviceInfo: ${ota.deviceInfo}")
    }

    override val resultFlow: MutableStateFlow<FormResult?> = MutableStateFlow(null)
}
