package info.dourok.voicebot.data.model

import androidx.compose.ui.text.toLowerCase
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale
import java.util.UUID
import kotlin.random.Random

data class ChipInfo(
    val model: Int,
    val cores: Int,
    val revision: Int,
    val features: Int
)

data class Application(
    val name: String,
    val version: String,
    val compile_time: String,
    val idf_version: String,
    val elf_sha256: String
)

data class Partition(
    val label: String,
    val type: Int,
    val subtype: Int,
    val address: Int,
    val size: Int
)

data class OTA(val label: String)

data class Board(
    val name: String,
    val revision: String,
    val features: List<String>,
    val manufacturer: String,
    val serial_number: String
)

data class DeviceInfo(
    val version: Int,
    val flash_size: Int,
    val psram_size: Int,
    val minimum_free_heap_size: Int,
    val mac_address: String,
    val uuid: String,
    val chip_model_name: String,
    val chip_info: ChipInfo,
    val application: Application,
    val partition_table: List<Partition>,
    val ota: OTA,
    val board: Board
)

fun DeviceInfo.toJson() = JSONObject().apply {
    put("version", version)
    put("flash_size", flash_size)
    put("psram_size", psram_size)
    put("minimum_free_heap_size", minimum_free_heap_size)
    put("mac_address", mac_address)
    put("uuid", uuid)
    put("chip_model_name", chip_model_name)
    put("chip_info", JSONObject().apply {
        put("model", chip_info.model)
        put("cores", chip_info.cores)
        put("revision", chip_info.revision)
        put("features", chip_info.features)
    })
    put("application", JSONObject().apply {
        put("name", application.name)
        put("version", application.version)
        put("compile_time", application.compile_time)
        put("idf_version", application.idf_version)
        put("elf_sha256", application.elf_sha256)
    })
    put("partition_table", JSONArray(partition_table.map {
        JSONObject().apply {
            put("label", it.label)
            put("type", it.type)
            put("subtype", it.subtype)
            put("address", it.address)
            put("size", it.size)
        }
    }))
    put("ota", JSONObject().apply {
        put("label", ota.label)
    })
    put("board", JSONObject().apply {
        put("name", board.name)
        put("revision", board.revision)
        put("features", JSONArray(board.features))
        put("manufacturer", board.manufacturer)
        put("serial_number", board.serial_number)
    })
}.toString()

fun fromJsonToDeviceInfo(json: String): DeviceInfo {
    val obj = JSONObject(json)
    return DeviceInfo(
        version = obj.getInt("version"),
        flash_size = obj.getInt("flash_size"),
        psram_size = obj.getInt("psram_size"),
        minimum_free_heap_size = obj.getInt("minimum_free_heap_size"),
        mac_address = obj.getString("mac_address"),
        uuid = obj.getString("uuid"),
        chip_model_name = obj.getString("chip_model_name"),
        chip_info = ChipInfo(
            model = obj.getJSONObject("chip_info").getInt("model"),
            cores = obj.getJSONObject("chip_info").getInt("cores"),
            revision = obj.getJSONObject("chip_info").getInt("revision"),
            features = obj.getJSONObject("chip_info").getInt("features")
        ),
        application = Application(
            name = obj.getJSONObject("application").getString("name"),
            version = obj.getJSONObject("application").getString("version"),
            compile_time = obj.getJSONObject("application").getString("compile_time"),
            idf_version = obj.getJSONObject("application").getString("idf_version"),
            elf_sha256 = obj.getJSONObject("application").getString("elf_sha256")
        ),
        partition_table = obj.getJSONArray("partition_table").let { jsonArray ->
            (0 until jsonArray.length()).map { index ->
                jsonArray.getJSONObject(index).let {
                    Partition(
                        label = it.getString("label"),
                        type = it.getInt("type"),
                        subtype = it.getInt("subtype"),
                        address = it.getInt("address"),
                        size = it.getInt("size")
                    )
                }
            }
        },
        ota = OTA(obj.getJSONObject("ota").getString("label")),
        board = Board(
            name = obj.getJSONObject("board").getString("name"),
            revision = obj.getJSONObject("board").getString("revision"),
            features = (0 until obj.getJSONObject("board").getJSONArray("features").length()).map { index ->
                obj.getJSONObject("board").getJSONArray("features").getString(index)
            },
            manufacturer = obj.getJSONObject("board").getString("manufacturer"),
            serial_number = obj.getJSONObject("board").getString("serial_number")
        )
    )
}

object DummyDataGenerator {
    
    /**
     * 生成设备信息，使用DeviceIdManager获取真实设备ID
     */
    suspend fun generate(deviceIdManager: DeviceIdManager): DeviceInfo {
        return DeviceInfo(
            version = 2,
            flash_size = 8388608,
            psram_size = 4194304,
            minimum_free_heap_size = Random.nextInt(200000, 300000),
            mac_address = deviceIdManager.getStableDeviceId(), // 使用真实设备ID
            uuid = UUID.randomUUID().toString(),
            chip_model_name = "android", // 更正确的芯片型号名称
            chip_info = ChipInfo(
                model = 1000 + android.os.Build.VERSION.SDK_INT, // 基于Android版本的模型号
                cores = Runtime.getRuntime().availableProcessors(),
                revision = 1,
                features = 5
            ),
            application = Application(
                name = "xiaozhi-android",
                version = "1.0.0",
                compile_time = "2025-02-28T12:34:56Z",
                idf_version = "android-${android.os.Build.VERSION.SDK_INT}",
                elf_sha256 = generateRandomSha256()
            ),
            partition_table = listOf(
                Partition("app", 1, 2, 65536, 2097152),
                Partition("nvs", 1, 1, 32768, 65536),
                Partition("phy_init", 1, 3, 98304, 8192)
            ),
            ota = OTA("ota_1"),
            board = Board(
                name = "Android-${android.os.Build.MODEL}",
                revision = "v1.0",
                features = listOf("WiFi", "Bluetooth", "Microphone", "Speaker"),
                manufacturer = android.os.Build.MANUFACTURER,
                serial_number = "Android-${Random.nextInt(1000, 9999)}"
            )
        )
    }
    
    /**
     * 同步生成设备信息，用于依赖注入时避免阻塞
     * 使用DeviceIdManager的同步方法获取缓存的设备ID
     */
    fun generateSync(deviceIdManager: DeviceIdManager): DeviceInfo {
        // 尝试获取缓存的设备ID，如果没有则使用临时ID
        val deviceId = deviceIdManager.getStableDeviceIdSync() ?: generateMacAddress()
        
        return DeviceInfo(
            version = 2,
            flash_size = 8388608,
            psram_size = 4194304,
            minimum_free_heap_size = Random.nextInt(200000, 300000),
            mac_address = deviceId,
            uuid = UUID.randomUUID().toString(),
            chip_model_name = "android",
            chip_info = ChipInfo(
                model = 1000 + android.os.Build.VERSION.SDK_INT,
                cores = Runtime.getRuntime().availableProcessors(),
                revision = 1,
                features = 5
            ),
            application = Application(
                name = "xiaozhi-android",
                version = "1.0.0",
                compile_time = "2025-02-28T12:34:56Z",
                idf_version = "android-${android.os.Build.VERSION.SDK_INT}",
                elf_sha256 = generateRandomSha256()
            ),
            partition_table = listOf(
                Partition("app", 1, 2, 65536, 2097152),
                Partition("nvs", 1, 1, 32768, 65536),
                Partition("phy_init", 1, 3, 98304, 8192)
            ),
            ota = OTA("ota_1"),
            board = Board(
                name = "Android-${android.os.Build.MODEL}",
                revision = "v1.0",
                features = listOf("WiFi", "Bluetooth", "Microphone", "Speaker"),
                manufacturer = android.os.Build.MANUFACTURER,
                serial_number = "Android-${Random.nextInt(1000, 9999)}"
            )
        )
    }
    
    /**
     * 生成设备信息的兼容方法（向后兼容）
     * @deprecated 建议使用带DeviceIdManager参数的版本
     */
    @Deprecated("建议使用带DeviceIdManager参数的generate方法")
    fun generate(): DeviceInfo {
        return DeviceInfo(
            version = 2,
            flash_size = 8388608,
            psram_size = 4194304,
            minimum_free_heap_size = Random.nextInt(200000, 300000),
            mac_address = generateMacAddress(),
            uuid = UUID.randomUUID().toString(),
            chip_model_name = "android",
            chip_info = ChipInfo(
                model = 1000 + android.os.Build.VERSION.SDK_INT,
                cores = Runtime.getRuntime().availableProcessors(),
                revision = 1,
                features = 5
            ),
            application = Application(
                name = "xiaozhi-android",
                version = "1.0.0",
                compile_time = "2025-02-28T12:34:56Z",
                idf_version = "android-${android.os.Build.VERSION.SDK_INT}",
                elf_sha256 = generateRandomSha256()
            ),
            partition_table = listOf(
                Partition("app", 1, 2, 65536, 2097152),
                Partition("nvs", 1, 1, 32768, 65536),
                Partition("phy_init", 1, 3, 98304, 8192)
            ),
            ota = OTA("ota_1"),
            board = Board(
                name = "Android-${android.os.Build.MODEL}",
                revision = "v1.0",
                features = listOf("WiFi", "Bluetooth", "Microphone", "Speaker"),
                manufacturer = android.os.Build.MANUFACTURER,
                serial_number = "Android-${Random.nextInt(1000, 9999)}"
            )
        )
    }

    private fun generateMacAddress(): String {
        // 警告：这是临时兼容方案，应该使用DeviceIdManager
        android.util.Log.w("DummyDataGenerator", "使用固定MAC地址，建议升级到DeviceIdManager")
        return "00:11:22:33:44:55" // 保持向后兼容，但这将被DeviceIdManager管理
    }

    private fun generateRandomSha256(): String {
        val chars = "0123456789abcdef"
        return (1..64).map { chars.random() }.joinToString("")
    }
}

