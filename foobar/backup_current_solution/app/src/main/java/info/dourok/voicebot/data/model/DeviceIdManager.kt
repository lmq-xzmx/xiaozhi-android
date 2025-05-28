package info.dourok.voicebot.data.model

import android.content.Context
import android.os.Build
import android.provider.Settings
import android.util.Log
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.security.MessageDigest
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

/**
 * 设备ID管理器
 * 
 * 负责生成和管理稳定的设备ID，格式为MAC地址样式：xx:xx:xx:xx:xx:xx
 * 
 * 优先级策略：
 * 1. 内存缓存（最快）
 * 2. 用户自定义ID（最高优先级）
 * 3. 已保存的稳定ID（中等优先级）
 * 4. 基于Android ID + 设备指纹生成的新ID（自动生成）
 */
@Singleton
class DeviceIdManager @Inject constructor(
    private val context: Context
) {
    companion object {
        private val DEVICE_ID_KEY = stringPreferencesKey("stable_device_id")
        private val CUSTOM_ID_KEY = stringPreferencesKey("custom_device_id")
        private const val TAG = "DeviceIdManager"
        
        // DataStore扩展属性
        private val Context.deviceIdDataStore: DataStore<Preferences> by preferencesDataStore(
            name = "device_id_preferences"
        )
    }
    
    private val dataStore = context.deviceIdDataStore
    private val mutex = Mutex()
    
    // 内存缓存，避免频繁的DataStore操作
    @Volatile
    private var cachedDeviceId: String? = null
    
    /**
     * 获取稳定的设备ID（非阻塞版本）
     * 
     * 这是主要的公共接口，确保返回一个稳定且唯一的设备ID
     * 使用缓存机制避免主线程阻塞
     */
    suspend fun getStableDeviceId(): String {
        // 快速路径：如果已有缓存，直接返回
        cachedDeviceId?.let { cached ->
            Log.d(TAG, "使用缓存的设备ID: $cached")
            return cached
        }
        
        // 慢速路径：需要从DataStore加载或生成新ID
        return mutex.withLock {
            // 双重检查：可能在等待锁的过程中其他线程已经设置了缓存
            cachedDeviceId?.let { return it }
            
            try {
                val deviceId = loadOrGenerateDeviceId()
                cachedDeviceId = deviceId
                Log.i(TAG, "设备ID已缓存: $deviceId")
                deviceId
            } catch (e: Exception) {
                Log.e(TAG, "获取设备ID失败，使用应急ID", e)
                generateEmergencyId()
            }
        }
    }
    
    /**
     * 从DataStore加载或生成新的设备ID
     */
    private suspend fun loadOrGenerateDeviceId(): String {
        // 一次性获取所有DataStore数据，避免多次阻塞调用
        val preferences = dataStore.data.first()
        
        // 1. 检查用户自定义ID
        val customId = preferences[CUSTOM_ID_KEY]
        if (!customId.isNullOrEmpty() && isValidMacFormat(customId)) {
            Log.d(TAG, "使用用户自定义ID: $customId")
            return customId
        }
        
        // 2. 检查已保存的ID
        val savedId = preferences[DEVICE_ID_KEY]
        if (!savedId.isNullOrEmpty() && isValidMacFormat(savedId)) {
            Log.d(TAG, "使用已保存的ID: $savedId")
            return savedId
        }
        
        // 3. 生成新的稳定ID
        val newId = generateStableId()
        
        // 保存新生成的ID
        dataStore.edit { preferences ->
            preferences[DEVICE_ID_KEY] = newId
        }
        
        Log.i(TAG, "生成并保存新的设备ID: $newId")
        return newId
    }
    
    /**
     * 生成应急ID（当所有其他方法都失败时使用）
     */
    private fun generateEmergencyId(): String {
        val emergencyId = "02:00:00:${Random.nextInt(256).toString(16).padStart(2, '0')}:${Random.nextInt(256).toString(16).padStart(2, '0')}:${Random.nextInt(256).toString(16).padStart(2, '0')}".uppercase()
        Log.w(TAG, "使用应急设备ID: $emergencyId")
        cachedDeviceId = emergencyId
        return emergencyId
    }
    
    /**
     * 获取设备ID的同步版本（仅用于非关键路径）
     * 
     * 注意：这个方法可能返回null，调用者需要处理这种情况
     */
    fun getStableDeviceIdSync(): String? {
        return cachedDeviceId
    }
    
    /**
     * 预加载设备ID到缓存（在应用启动时调用）
     */
    suspend fun preloadDeviceId() {
        try {
            getStableDeviceId() // 这会触发加载并缓存
            Log.d(TAG, "设备ID预加载完成")
        } catch (e: Exception) {
            Log.w(TAG, "设备ID预加载失败", e)
        }
    }
    
    /**
     * 基于Android ID和设备指纹生成稳定的MAC格式ID
     * 
     * 使用多个设备特征确保ID的稳定性和唯一性
     */
    private fun generateStableId(): String {
        return try {
            // 获取Android ID（最重要的标识符）
            val androidId = Settings.Secure.getString(
                context.contentResolver, 
                Settings.Secure.ANDROID_ID
            ) ?: "unknown_device"
            
            // 构建设备指纹
            val deviceFingerprint = buildString {
                append(Build.MANUFACTURER)
                append("-")
                append(Build.MODEL)
                append("-")
                append(Build.FINGERPRINT.take(20)) // 只取前20个字符避免过长
                append("-")
                append(Build.VERSION.SDK_INT)
            }
            
            // 组合标识符
            val combinedIdentifier = "$androidId-$deviceFingerprint"
            
            Log.d(TAG, "生成设备指纹: $deviceFingerprint")
            Log.d(TAG, "Android ID: $androidId")
            
            // 使用SHA-256生成稳定哈希
            val hash = MessageDigest.getInstance("SHA-256")
                .digest(combinedIdentifier.toByteArray())
            
            // 取前6个字节转换为MAC格式
            val macId = hash.take(6)
                .joinToString(":") { "%02x".format(it) }
                .uppercase()
            
            Log.d(TAG, "生成的MAC格式ID: $macId")
            macId
            
        } catch (e: Exception) {
            Log.w(TAG, "生成设备ID失败，使用fallback方案: ${e.message}")
            generateFallbackId()
        }
    }
    
    /**
     * 备用ID生成方案（当主方案失败时使用）
     */
    private fun generateFallbackId(): String {
        // 使用时间戳和随机数确保唯一性
        val timestamp = System.currentTimeMillis()
        val random = Random(timestamp)
        
        // 生成6个字节的随机MAC地址
        val bytes = ByteArray(6)
        random.nextBytes(bytes)
        
        // 确保第一个字节不是广播地址，设置局部管理位
        bytes[0] = (bytes[0].toInt() and 0xFE or 0x02).toByte()
        
        val fallbackId = bytes.joinToString(":") { "%02x".format(it) }.uppercase()
        Log.i(TAG, "使用fallback ID: $fallbackId")
        return fallbackId
    }
    
    /**
     * 设置自定义设备ID
     * 
     * @param customId 用户自定义的设备ID，必须是有效的MAC地址格式
     * @return 是否设置成功
     */
    suspend fun setCustomDeviceId(customId: String): Boolean {
        if (!isValidMacFormat(customId)) {
            Log.w(TAG, "无效的MAC格式: $customId")
            return false
        }
        
        dataStore.edit { preferences ->
            preferences[CUSTOM_ID_KEY] = customId.uppercase()
        }
        Log.i(TAG, "设置自定义设备ID: ${customId.uppercase()}")
        return true
    }
    
    /**
     * 清除自定义ID，恢复使用自动生成的ID
     */
    suspend fun clearCustomDeviceId() {
        dataStore.edit { preferences ->
            preferences.remove(CUSTOM_ID_KEY)
        }
        Log.i(TAG, "已清除自定义设备ID，将使用自动生成的ID")
    }
    
    /**
     * 强制重新生成设备ID
     * 
     * 注意：这会导致设备失去与服务器的绑定关系
     */
    suspend fun regenerateDeviceId(): String {
        val newId = generateStableId()
        
        dataStore.edit { preferences ->
            preferences[DEVICE_ID_KEY] = newId
            // 清除自定义ID，使新生成的ID生效
            preferences.remove(CUSTOM_ID_KEY)
        }
        
        Log.w(TAG, "强制重新生成设备ID: $newId")
        return newId
    }
    
    /**
     * 验证MAC地址格式
     * 
     * 支持冒号分隔的标准MAC格式：xx:xx:xx:xx:xx:xx
     */
    private fun isValidMacFormat(mac: String): Boolean {
        val macPattern = Regex("^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
        return macPattern.matches(mac)
    }
    
    /**
     * 获取设备信息摘要（用于调试和支持）
     */
    suspend fun getDeviceInfoSummary(): Map<String, String> {
        val currentId = getStableDeviceId()
        
        // 一次性获取所有DataStore数据，避免多次阻塞调用
        val preferences = dataStore.data.first()
        val customId = preferences[CUSTOM_ID_KEY]
        val savedId = preferences[DEVICE_ID_KEY]
        
        return mapOf(
            "currentDeviceId" to currentId,
            "hasCustomId" to (customId != null).toString(),
            "customId" to (customId ?: "未设置"),
            "savedId" to (savedId ?: "未保存"),
            "androidId" to (Settings.Secure.getString(
                context.contentResolver, 
                Settings.Secure.ANDROID_ID
            ) ?: "unknown"),
            "manufacturer" to Build.MANUFACTURER,
            "model" to Build.MODEL,
            "apiLevel" to Build.VERSION.SDK_INT.toString(),
            "fingerprint" to Build.FINGERPRINT.take(50) // 只显示前50个字符
        )
    }
    
    /**
     * 检查当前设备ID是否稳定
     * 
     * @return true 如果ID基于稳定的设备特征生成
     */
    suspend fun isDeviceIdStable(): Boolean {
        val androidId = Settings.Secure.getString(
            context.contentResolver, 
            Settings.Secure.ANDROID_ID
        )
        
        // Android ID存在且不是默认值，认为是稳定的
        return !androidId.isNullOrEmpty() && androidId != "9774d56d682e549c"
    }
} 