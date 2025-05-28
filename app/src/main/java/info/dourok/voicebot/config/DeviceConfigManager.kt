package info.dourok.voicebot.config

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import info.dourok.voicebot.data.model.DeviceIdManager
import javax.inject.Inject
import javax.inject.Singleton

private val Context.deviceConfigDataStore: DataStore<Preferences> by preferencesDataStore(name = "device_config")

@Singleton
class DeviceConfigManager @Inject constructor(
    private val context: Context,
    private val deviceIdManager: DeviceIdManager
) {
    private val dataStore = context.deviceConfigDataStore
    
    companion object {
        val DEVICE_ID_KEY = stringPreferencesKey("device_id")
        val BINDING_STATUS_KEY = booleanPreferencesKey("binding_status")
        val LAST_CHECK_TIME_KEY = longPreferencesKey("last_check_time")
        val ACTIVATION_CODE_KEY = stringPreferencesKey("activation_code")
        val SERVER_URL_KEY = stringPreferencesKey("server_url")
        val WEBSOCKET_URL_KEY = stringPreferencesKey("websocket_url")
        
        const val DEFAULT_SERVER_URL = "http://47.122.144.73:8002"
    }
    
    /**
     * 获取设备ID - 优先使用用户设置的ID，否则使用DeviceIdManager生成的稳定ID
     */
    suspend fun getDeviceId(): String {
        // 首先检查用户是否手动设置了设备ID
        val userSetId = dataStore.data.first()[DEVICE_ID_KEY]
        if (!userSetId.isNullOrEmpty()) {
            return userSetId
        }
        
        // 使用DeviceIdManager获取基于设备硬件信息的稳定ID
        val stableId = deviceIdManager.getStableDeviceId()
        
        // 将第一次生成的稳定ID保存到DataStore
        dataStore.edit { prefs ->
            prefs[DEVICE_ID_KEY] = stableId
        }
        
        return stableId
    }
    
    suspend fun setDeviceId(deviceId: String) {
        dataStore.edit { prefs ->
            prefs[DEVICE_ID_KEY] = deviceId
        }
    }
    
    suspend fun getBindingStatus(): Boolean {
        return dataStore.data.first()[BINDING_STATUS_KEY] ?: false
    }
    
    suspend fun updateBindingStatus(isBound: Boolean) {
        dataStore.edit { prefs ->
            prefs[BINDING_STATUS_KEY] = isBound
            prefs[LAST_CHECK_TIME_KEY] = System.currentTimeMillis()
        }
    }
    
    suspend fun getLastCheckTime(): Long {
        return dataStore.data.first()[LAST_CHECK_TIME_KEY] ?: 0L
    }
    
    suspend fun getActivationCode(): String? {
        return dataStore.data.first()[ACTIVATION_CODE_KEY]
    }
    
    suspend fun setActivationCode(code: String?) {
        dataStore.edit { prefs ->
            if (code != null) {
                prefs[ACTIVATION_CODE_KEY] = code
            } else {
                prefs.remove(ACTIVATION_CODE_KEY)
            }
        }
    }
    
    suspend fun getServerUrl(): String {
        return dataStore.data.first()[SERVER_URL_KEY] ?: DEFAULT_SERVER_URL
    }
    
    suspend fun setServerUrl(url: String) {
        dataStore.edit { prefs ->
            prefs[SERVER_URL_KEY] = url
        }
    }
    
    suspend fun getWebsocketUrl(): String? {
        return dataStore.data.first()[WEBSOCKET_URL_KEY]
    }
    
    suspend fun setWebsocketUrl(url: String?) {
        dataStore.edit { prefs ->
            if (url != null) {
                prefs[WEBSOCKET_URL_KEY] = url
            } else {
                prefs.remove(WEBSOCKET_URL_KEY)
            }
        }
    }
    
    // 获取设备配置流，用于UI观察
    fun getDeviceConfigFlow() = dataStore.data.map { prefs ->
        DeviceConfig(
            deviceId = prefs[DEVICE_ID_KEY] ?: "00:00:00:00:00:00", // 临时默认值，实际使用时会通过getDeviceId()获取
            bindingStatus = prefs[BINDING_STATUS_KEY] ?: false,
            lastCheckTime = prefs[LAST_CHECK_TIME_KEY] ?: 0L,
            activationCode = prefs[ACTIVATION_CODE_KEY],
            serverUrl = prefs[SERVER_URL_KEY] ?: DEFAULT_SERVER_URL,
            websocketUrl = prefs[WEBSOCKET_URL_KEY]
        )
    }
    
    suspend fun clearAllConfig() {
        dataStore.edit { prefs ->
            prefs.clear()
        }
    }
}

data class DeviceConfig(
    val deviceId: String,
    val bindingStatus: Boolean,
    val lastCheckTime: Long,
    val activationCode: String?,
    val serverUrl: String,
    val websocketUrl: String?
) 