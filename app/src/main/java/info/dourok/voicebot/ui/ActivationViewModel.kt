package info.dourok.voicebot.ui

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import info.dourok.voicebot.NavigationEvents
import info.dourok.voicebot.Ota
import info.dourok.voicebot.data.FormRepository
import info.dourok.voicebot.data.FormResult
import info.dourok.voicebot.data.SettingsRepository
import info.dourok.voicebot.data.model.Activation
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ActivationViewModel @Inject constructor(
    private val repository: FormRepository,
    private val settingsRepository: SettingsRepository,
    private val ota: Ota,
    @NavigationEvents private val navigationEvents: MutableSharedFlow<String>
) : ViewModel() {
    
    companion object {
        private const val TAG = "ActivationViewModel"
        private const val BINDING_CHECK_INTERVAL = 5000L // 5秒检查一次
    }
    
    private val _activationFlow = MutableStateFlow<Activation?>(null)
    val activationFlow: StateFlow<Activation?> = _activationFlow
    
    private val _bindingStatus = MutableStateFlow<BindingStatus>(BindingStatus.Checking)
    val bindingStatus: StateFlow<BindingStatus> = _bindingStatus
    
    private var currentOtaUrl: String? = null
    private var isCheckingBinding = false
    
    init {
        Log.i(TAG, "ActivationViewModel 初始化开始")
        
        viewModelScope.launch {
            try {
                repository.resultFlow.collect { result ->
                    Log.d(TAG, "收到FormRepository结果: $result")
                    
                    when (result) {
                        is FormResult.XiaoZhiResult -> {
                            handleXiaoZhiResult(result)
                        }
                        is FormResult.SelfHostResult -> {
                            Log.d(TAG, "SelfHost结果，ActivationViewModel不处理")
                        }
                        null -> {
                            Log.d(TAG, "收到null结果，等待有效数据")
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "监听FormRepository结果时发生异常: ${e.message}", e)
                _bindingStatus.value = BindingStatus.CheckFailed
            }
        }
        
        Log.i(TAG, "ActivationViewModel 初始化完成")
    }
    
    private fun handleXiaoZhiResult(xiaozhiResult: FormResult.XiaoZhiResult) {
        try {
            val activation = xiaozhiResult.otaResult?.activation
            _activationFlow.value = activation
            
            if (activation != null) {
                Log.i(TAG, "发现激活信息，激活码: ${activation.code}")
                
                // 保存当前OTA URL以供后续检查使用
                saveCurrentOtaUrl()
                startBindingStatusCheck()
            } else {
                Log.d(TAG, "没有激活信息，设备可能已绑定或使用WebSocket模式")
                _bindingStatus.value = BindingStatus.Bound
            }
        } catch (e: Exception) {
            Log.e(TAG, "处理XiaoZhi结果时发生异常: ${e.message}", e)
            _bindingStatus.value = BindingStatus.CheckFailed
        }
    }
    
    private fun saveCurrentOtaUrl() {
        try {
            // 从默认配置获取OTA URL
            // 实际项目中应该从FormRepository保存的表单数据中获取
            currentOtaUrl = "http://47.122.144.73:8002/xiaozhi/ota/"
            Log.d(TAG, "保存OTA URL: $currentOtaUrl")
        } catch (e: Exception) {
            Log.e(TAG, "保存OTA URL时发生异常: ${e.message}", e)
        }
    }
    
    private fun startBindingStatusCheck() {
        if (isCheckingBinding) {
            Log.d(TAG, "绑定状态检查已在进行中")
            return
        }
        
        val otaUrl = currentOtaUrl
        if (otaUrl.isNullOrEmpty()) {
            Log.w(TAG, "OTA URL未设置，无法检查绑定状态")
            _bindingStatus.value = BindingStatus.CheckFailed
            return
        }
        
        isCheckingBinding = true
        Log.i(TAG, "开始绑定状态检查循环")
        
        viewModelScope.launch {
            try {
                while (isCheckingBinding && _bindingStatus.value != BindingStatus.Bound) {
                    checkBindingStatus()
                    if (isCheckingBinding) {
                        delay(BINDING_CHECK_INTERVAL)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "绑定状态检查循环异常: ${e.message}", e)
                _bindingStatus.value = BindingStatus.CheckFailed
            } finally {
                isCheckingBinding = false
                Log.d(TAG, "绑定状态检查循环结束")
            }
        }
    }
    
    private suspend fun checkBindingStatus() {
        try {
            _bindingStatus.value = BindingStatus.Checking
            Log.d(TAG, "检查设备绑定状态...")
            
            val otaUrl = currentOtaUrl
            if (otaUrl.isNullOrEmpty()) {
                Log.w(TAG, "OTA URL为空，检查失败")
                _bindingStatus.value = BindingStatus.CheckFailed
                return
            }
            
            val success = ota.checkVersion(otaUrl)
            
            if (success && ota.otaResult != null) {
                val activation = ota.otaResult?.activation
                
                if (activation == null) {
                    // 没有activation信息说明设备已绑定
                    Log.i(TAG, "设备绑定成功！准备跳转到聊天页面")
                    _bindingStatus.value = BindingStatus.Bound
                    
                    // 更新设置并跳转
                    handleSuccessfulBinding()
                } else {
                    Log.d(TAG, "设备仍需绑定，激活码: ${activation.code}")
                    _bindingStatus.value = BindingStatus.WaitingForBinding
                }
            } else {
                Log.w(TAG, "检查绑定状态失败: success=$success, otaResult=${ota.otaResult}")
                _bindingStatus.value = BindingStatus.CheckFailed
            }
        } catch (e: Exception) {
            Log.e(TAG, "检查绑定状态异常: ${e.message}", e)
            _bindingStatus.value = BindingStatus.CheckFailed
        }
    }
    
    private suspend fun handleSuccessfulBinding() {
        try {
            Log.i(TAG, "设备绑定成功，准备配置和跳转")
            
            // 设置MQTT配置（如果有）
            ota.otaResult?.mqttConfig?.let { mqttConfig ->
                Log.i(TAG, "保存MQTT配置")
                settingsRepository.mqttConfig = mqttConfig
                settingsRepository.transportType = info.dourok.voicebot.data.model.TransportType.MQTT
            } ?: run {
                // 如果没有MQTT配置，使用WebSocket模式
                Log.i(TAG, "使用WebSocket模式")
                settingsRepository.transportType = info.dourok.voicebot.data.model.TransportType.WebSockets
                // WebSocket URL应该已经在FormRepository中设置过了
            }
            
            // 停止绑定状态检查
            isCheckingBinding = false
            
            // 短暂延迟以显示成功状态，然后自动跳转
            delay(1500)
            
            // 跳转到聊天页面
            Log.i(TAG, "绑定完成，导航到聊天页面开始STT监听")
            navigationEvents.emit("chat")
            
        } catch (e: Exception) {
            Log.e(TAG, "处理绑定成功失败: ${e.message}", e)
            _bindingStatus.value = BindingStatus.CheckFailed
        }
    }
    
    fun manualCheckBinding() {
        viewModelScope.launch {
            try {
                checkBindingStatus()
            } catch (e: Exception) {
                Log.e(TAG, "手动检查绑定异常: ${e.message}", e)
                _bindingStatus.value = BindingStatus.CheckFailed
            }
        }
    }
    
    fun retryBindingCheck() {
        if (!isCheckingBinding) {
            Log.i(TAG, "重试绑定检查")
            startBindingStatusCheck()
        } else {
            Log.d(TAG, "绑定检查已在进行中，不重复启动")
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        isCheckingBinding = false
        Log.d(TAG, "ActivationViewModel cleared")
    }
}

enum class BindingStatus {
    Checking,           // 正在检查
    WaitingForBinding,  // 等待绑定
    Bound,              // 已绑定
    CheckFailed         // 检查失败
}