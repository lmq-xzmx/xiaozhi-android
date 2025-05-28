package info.dourok.voicebot.ui.config

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import info.dourok.voicebot.binding.BindingCheckResult
import info.dourok.voicebot.binding.BindingStatusChecker
import info.dourok.voicebot.config.DeviceConfig
import info.dourok.voicebot.config.DeviceConfigManager
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*
import javax.inject.Inject

@HiltViewModel
class DeviceConfigViewModel @Inject constructor(
    private val deviceConfigManager: DeviceConfigManager,
    private val bindingStatusChecker: BindingStatusChecker,
    @ApplicationContext private val context: Context
) : ViewModel() {
    
    companion object {
        private const val TAG = "DeviceConfigViewModel"
    }
    
    private val _uiState = MutableStateFlow(DeviceConfigUiState())
    val uiState: StateFlow<DeviceConfigUiState> = _uiState.asStateFlow()
    
    private val _events = MutableSharedFlow<DeviceConfigEvent>()
    val events: SharedFlow<DeviceConfigEvent> = _events.asSharedFlow()
    
    init {
        // 监听设备配置变化
        viewModelScope.launch {
            deviceConfigManager.getDeviceConfigFlow().collect { config ->
                updateUiStateFromConfig(config)
            }
        }
        
        // 初始检查绑定状态
        checkBindingStatus()
    }
    
    private fun updateUiStateFromConfig(config: DeviceConfig) {
        _uiState.value = _uiState.value.copy(
            deviceId = config.deviceId,
            bindingStatus = if (config.bindingStatus) BindingStatus.Bound else BindingStatus.Unbound,
            lastCheckTime = config.lastCheckTime,
            activationCode = config.activationCode,
            serverUrl = config.serverUrl,
            websocketUrl = config.websocketUrl
        )
    }
    
    fun updateDeviceId(deviceId: String) {
        _uiState.value = _uiState.value.copy(deviceId = deviceId)
    }
    
    fun saveDeviceId() {
        viewModelScope.launch {
            try {
                val deviceId = _uiState.value.deviceId
                deviceConfigManager.setDeviceId(deviceId)
                
                _events.emit(DeviceConfigEvent.ShowMessage("设备ID已保存: $deviceId"))
                Log.d(TAG, "设备ID已保存: $deviceId")
                
                // 保存后重新检查绑定状态
                checkBindingStatus()
            } catch (e: Exception) {
                Log.e(TAG, "保存设备ID失败", e)
                _events.emit(DeviceConfigEvent.ShowError("保存设备ID失败: ${e.message}"))
            }
        }
    }
    
    fun updateServerUrl(url: String) {
        _uiState.value = _uiState.value.copy(serverUrl = url)
    }
    
    fun saveServerUrl() {
        viewModelScope.launch {
            try {
                val serverUrl = _uiState.value.serverUrl
                deviceConfigManager.setServerUrl(serverUrl)
                
                _events.emit(DeviceConfigEvent.ShowMessage("服务器地址已保存: $serverUrl"))
                Log.d(TAG, "服务器地址已保存: $serverUrl")
                
                // 保存后重新检查绑定状态
                checkBindingStatus()
            } catch (e: Exception) {
                Log.e(TAG, "保存服务器地址失败", e)
                _events.emit(DeviceConfigEvent.ShowError("保存服务器地址失败: ${e.message}"))
            }
        }
    }
    
    fun checkBindingStatus() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isChecking = true)
            
            try {
                val result = bindingStatusChecker.checkBindingStatus()
                
                when (result) {
                    is BindingCheckResult.Bound -> {
                        _uiState.value = _uiState.value.copy(
                            bindingStatus = BindingStatus.Bound,
                            websocketUrl = result.websocketUrl,
                            activationCode = null,
                            isChecking = false
                        )
                        _events.emit(DeviceConfigEvent.ShowMessage("设备已绑定"))
                    }
                    is BindingCheckResult.Unbound -> {
                        _uiState.value = _uiState.value.copy(
                            bindingStatus = BindingStatus.Unbound,
                            activationCode = result.activationCode,
                            websocketUrl = null,
                            isChecking = false
                        )
                        _events.emit(DeviceConfigEvent.ShowMessage("设备未绑定，请使用激活码进行绑定"))
                    }
                    is BindingCheckResult.Error -> {
                        _uiState.value = _uiState.value.copy(
                            bindingStatus = BindingStatus.Error,
                            isChecking = false
                        )
                        _events.emit(DeviceConfigEvent.ShowError("检查绑定状态失败: ${result.message}"))
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "检查绑定状态异常", e)
                _uiState.value = _uiState.value.copy(
                    bindingStatus = BindingStatus.Error,
                    isChecking = false
                )
                _events.emit(DeviceConfigEvent.ShowError("检查绑定状态异常: ${e.message}"))
            }
        }
    }
    
    fun copyActivationCode() {
        val activationCode = _uiState.value.activationCode
        if (activationCode != null) {
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("激活码", activationCode)
            clipboard.setPrimaryClip(clip)
            
            viewModelScope.launch {
                _events.emit(DeviceConfigEvent.ShowMessage("激活码已复制到剪贴板"))
            }
        }
    }
    
    fun openManagementPanel() {
        val serverUrl = _uiState.value.serverUrl
        val managementUrl = "$serverUrl/manager"
        
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(managementUrl)).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            Log.e(TAG, "打开管理面板失败", e)
            viewModelScope.launch {
                _events.emit(DeviceConfigEvent.ShowError("打开管理面板失败: ${e.message}"))
            }
        }
    }
    
    fun showManualBindDialog() {
        viewModelScope.launch {
            _events.emit(DeviceConfigEvent.ShowManualBindDialog)
        }
    }
    
    fun clearAllConfig() {
        viewModelScope.launch {
            try {
                deviceConfigManager.clearAllConfig()
                _events.emit(DeviceConfigEvent.ShowMessage("所有配置已清除"))
                Log.d(TAG, "所有配置已清除")
            } catch (e: Exception) {
                Log.e(TAG, "清除配置失败", e)
                _events.emit(DeviceConfigEvent.ShowError("清除配置失败: ${e.message}"))
            }
        }
    }
    
    fun getFormattedLastCheckTime(): String {
        val lastCheckTime = _uiState.value.lastCheckTime
        return if (lastCheckTime > 0) {
            val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            formatter.format(Date(lastCheckTime))
        } else {
            "从未检查"
        }
    }
}

data class DeviceConfigUiState(
    val deviceId: String = "",
    val bindingStatus: BindingStatus = BindingStatus.Unknown,
    val lastCheckTime: Long = 0L,
    val activationCode: String? = null,
    val serverUrl: String = "",
    val websocketUrl: String? = null,
    val isChecking: Boolean = false
)

enum class BindingStatus {
    Unknown,
    Bound,
    Unbound,
    Error
}

sealed class DeviceConfigEvent {
    data class ShowMessage(val message: String) : DeviceConfigEvent()
    data class ShowError(val message: String) : DeviceConfigEvent()
    object ShowManualBindDialog : DeviceConfigEvent()
} 