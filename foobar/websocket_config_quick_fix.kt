// WebSocket配置失败快速修复补丁
// 文件: app/src/main/java/info/dourok/voicebot/data/SettingsRepositoryImpl.kt

package info.dourok.voicebot.data

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import dagger.hilt.android.qualifiers.ApplicationContext
import info.dourok.voicebot.data.model.MqttConfig
import info.dourok.voicebot.data.model.TransportType
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SettingsRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context
) : SettingsRepository {
    
    private val sharedPrefs: SharedPreferences = 
        context.getSharedPreferences("xiaozhi_settings", Context.MODE_PRIVATE)
    
    private val gson = Gson()
    
    companion object {
        private const val KEY_TRANSPORT_TYPE = "transport_type"
        private const val KEY_WEBSOCKET_URL = "websocket_url"
        private const val KEY_MQTT_CONFIG = "mqtt_config"
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
                    gson.fromJson(configJson, MqttConfig::class.java)
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
                    val configJson = gson.toJson(value)
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
    
    /**
     * 调试方法：打印当前所有配置
     */
    fun debugPrintAllSettings() {
        android.util.Log.d("SettingsRepository", "=== 当前配置状态 ===")
        android.util.Log.d("SettingsRepository", "传输类型: $transportType")
        android.util.Log.d("SettingsRepository", "WebSocket URL: $webSocketUrl")
        android.util.Log.d("SettingsRepository", "MQTT配置: ${if (mqttConfig != null) "已配置" else "未配置"}")
        android.util.Log.d("SettingsRepository", "==================")
    }
    
    /**
     * 清除所有配置（用于重置）
     */
    fun clearAllSettings() {
        sharedPrefs.edit().clear().apply()
        android.util.Log.i("SettingsRepository", "🧹 所有配置已清除")
    }
} 