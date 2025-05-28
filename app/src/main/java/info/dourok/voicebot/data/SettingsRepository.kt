package info.dourok.voicebot.data

import android.content.Context
import android.content.SharedPreferences
import dagger.hilt.android.qualifiers.ApplicationContext
import info.dourok.voicebot.data.model.MqttConfig
import info.dourok.voicebot.data.model.TransportType
import info.dourok.voicebot.data.model.fromJsonToMqttConfig
import info.dourok.voicebot.data.model.toJson
import org.json.JSONObject
import javax.inject.Inject
import javax.inject.Singleton

interface SettingsRepository {
    var transportType: TransportType
    var mqttConfig: MqttConfig?
    var webSocketUrl: String?
    
    // 新增OTA配置支持
    var otaUrl: String?
    var deviceId: String?
    var isUsingOtaConfig: Boolean
}

@Singleton
class SettingsRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context
) : SettingsRepository {
    
    private val sharedPrefs: SharedPreferences = 
        context.getSharedPreferences("xiaozhi_settings", Context.MODE_PRIVATE)
    
    companion object {
        private const val KEY_TRANSPORT_TYPE = "transport_type"
        private const val KEY_WEBSOCKET_URL = "websocket_url"
        private const val KEY_MQTT_CONFIG = "mqtt_config"
        private const val KEY_OTA_URL = "ota_url"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_IS_USING_OTA_CONFIG = "is_using_ota_config"
    }
    
    override var transportType: TransportType
        get() {
            val typeString = sharedPrefs.getString(KEY_TRANSPORT_TYPE, "WebSockets") ?: "WebSockets"
            return try {
                TransportType.valueOf(typeString)
            } catch (e: IllegalArgumentException) {
                TransportType.WebSockets
            }
        }
        set(value) {
            sharedPrefs.edit()
                .putString(KEY_TRANSPORT_TYPE, value.name)
                .apply()
        }
    
    override var webSocketUrl: String?
        get() = sharedPrefs.getString(KEY_WEBSOCKET_URL, null)
        set(value) {
            if (value != null) {
                sharedPrefs.edit()
                    .putString(KEY_WEBSOCKET_URL, value)
                    .apply()
                android.util.Log.i("SettingsRepository", "✅ WebSocket URL已保存到持久化存储: $value")
            } else {
                sharedPrefs.edit()
                    .remove(KEY_WEBSOCKET_URL)
                    .apply()
                android.util.Log.i("SettingsRepository", "🗑️ WebSocket URL已从持久化存储移除")
            }
        }
    
    override var mqttConfig: MqttConfig?
        get() {
            val configJson = sharedPrefs.getString(KEY_MQTT_CONFIG, null)
            return if (configJson != null) {
                try {
                    val jsonObject = JSONObject(configJson)
                    fromJsonToMqttConfig(jsonObject)
                } catch (e: Exception) {
                    android.util.Log.w("SettingsRepository", "⚠️ MQTT配置反序列化失败", e)
                    null
                }
            } else {
                null
            }
        }
        set(value) {
            if (value != null) {
                try {
                    val configJson = value.toJson()
                    sharedPrefs.edit()
                        .putString(KEY_MQTT_CONFIG, configJson)
                        .apply()
                    android.util.Log.i("SettingsRepository", "✅ MQTT配置已保存到持久化存储")
                } catch (e: Exception) {
                    android.util.Log.e("SettingsRepository", "❌ MQTT配置序列化失败", e)
                }
            } else {
                sharedPrefs.edit()
                    .remove(KEY_MQTT_CONFIG)
                    .apply()
                android.util.Log.i("SettingsRepository", "🗑️ MQTT配置已从持久化存储移除")
            }
        }
    
    // OTA配置实现
    override var otaUrl: String?
        get() = sharedPrefs.getString(KEY_OTA_URL, "http://47.122.144.73:8002/xiaozhi/ota/")
        set(value) {
            if (value != null) {
                sharedPrefs.edit()
                    .putString(KEY_OTA_URL, value)
                    .apply()
            } else {
                sharedPrefs.edit()
                    .remove(KEY_OTA_URL)
                    .apply()
            }
        }
    
    override var deviceId: String?
        get() = sharedPrefs.getString(KEY_DEVICE_ID, null)
        set(value) {
            if (value != null) {
                sharedPrefs.edit()
                    .putString(KEY_DEVICE_ID, value)
                    .apply()
            } else {
                sharedPrefs.edit()
                    .remove(KEY_DEVICE_ID)
                    .apply()
            }
        }
    
    override var isUsingOtaConfig: Boolean
        get() = sharedPrefs.getBoolean(KEY_IS_USING_OTA_CONFIG, true)
        set(value) {
            sharedPrefs.edit()
                .putBoolean(KEY_IS_USING_OTA_CONFIG, value)
                .apply()
        }
}