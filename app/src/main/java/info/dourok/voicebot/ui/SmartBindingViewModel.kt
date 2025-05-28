package info.dourok.voicebot.ui

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import info.dourok.voicebot.binding.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 智能绑定ViewModel
 * 管理绑定流程的状态和用户交互
 */
@HiltViewModel
class SmartBindingViewModel @Inject constructor(
    private val smartBindingManager: SmartBindingManager
) : ViewModel() {
    
    companion object {
        private const val TAG = "SmartBindingViewModel"
    }
    
    // 绑定状态
    val bindingState = smartBindingManager.bindingState
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = BindingState.Unknown
        )
    
    // 绑定事件
    val bindingEvents = smartBindingManager.bindingEvents
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )
    
    // UI状态
    private val _uiState = MutableStateFlow(SmartBindingUiState())
    val uiState: StateFlow<SmartBindingUiState> = _uiState.asStateFlow()
    
    // 导航事件
    private val _navigationEvents = MutableSharedFlow<NavigationEvent>()
    val navigationEvents: SharedFlow<NavigationEvent> = _navigationEvents.asSharedFlow()
    
    // 是否已经开始监听绑定事件
    private var isListeningToBindingEvents = false
    
    /**
     * 开始监听绑定事件（延迟初始化）
     */
    private fun startListeningToBindingEvents() {
        if (isListeningToBindingEvents) return
        isListeningToBindingEvents = true
        
        Log.d(TAG, "开始监听绑定事件")
        
        // 监听绑定事件，处理导航
        viewModelScope.launch {
            bindingEvents.collect { event ->
                when (event) {
                    is BindingEvent.DeviceReady -> {
                        Log.i(TAG, "设备准备就绪，导航到聊天界面")
                        _navigationEvents.emit(NavigationEvent.NavigateToChat)
                    }
                    is BindingEvent.BindingCompleted -> {
                        Log.i(TAG, "绑定完成，准备导航到聊天界面")
                        // 延迟一下让用户看到成功消息
                        kotlinx.coroutines.delay(2000)
                        _navigationEvents.emit(NavigationEvent.NavigateToChat)
                    }
                    else -> {
                        // 其他事件不需要导航
                    }
                }
            }
        }
    }
    
    /**
     * 初始化设备绑定
     */
    fun initializeDeviceBinding() {
        Log.d(TAG, "开始初始化设备绑定")
        
        // 在这里启动事件监听
        startListeningToBindingEvents()
        
        _uiState.value = _uiState.value.copy(isLoading = true)
        
        viewModelScope.launch {
            try {
                when (val result = smartBindingManager.initializeDeviceBinding()) {
                    is BindingInitResult.AlreadyBound -> {
                        Log.i(TAG, "设备已绑定，直接进入聊天")
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            showBindingDialog = false
                        )
                        _navigationEvents.emit(NavigationEvent.NavigateToChat)
                    }
                    
                    is BindingInitResult.NeedsBinding -> {
                        Log.i(TAG, "设备需要绑定，显示绑定对话框")
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            showBindingDialog = true
                        )
                    }
                    
                    is BindingInitResult.Error -> {
                        Log.e(TAG, "设备绑定初始化失败: ${result.message}")
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            showBindingDialog = true,
                            errorMessage = result.message
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "初始化设备绑定异常", e)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    showBindingDialog = true,
                    errorMessage = "初始化失败: ${e.message}"
                )
            }
        }
    }
    
    /**
     * 开始智能绑定流程
     */
    fun startSmartBinding(activationCode: String) {
        Log.d(TAG, "开始智能绑定流程: $activationCode")
        
        viewModelScope.launch {
            try {
                when (val result = smartBindingManager.startSmartBinding(activationCode)) {
                    is SmartBindingResult.Success -> {
                        Log.i(TAG, "智能绑定成功")
                        _uiState.value = _uiState.value.copy(errorMessage = null)
                    }
                    
                    is SmartBindingResult.Timeout -> {
                        Log.w(TAG, "智能绑定超时")
                        _uiState.value = _uiState.value.copy(
                            errorMessage = "绑定检查超时，请手动检查或重试"
                        )
                    }
                    
                    is SmartBindingResult.Failed -> {
                        Log.e(TAG, "智能绑定失败: ${result.message}")
                        _uiState.value = _uiState.value.copy(
                            errorMessage = result.message
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "智能绑定异常", e)
                _uiState.value = _uiState.value.copy(
                    errorMessage = "绑定失败: ${e.message}"
                )
            }
        }
    }
    
    /**
     * 停止绑定流程
     */
    fun stopBinding() {
        Log.d(TAG, "停止绑定流程")
        smartBindingManager.stopBinding()
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }
    
    /**
     * 手动刷新绑定状态
     */
    fun manualRefresh() {
        Log.d(TAG, "手动刷新绑定状态")
        
        viewModelScope.launch {
            try {
                when (val result = smartBindingManager.refreshBindingStatus()) {
                    is BindingCheckResult.Bound -> {
                        Log.i(TAG, "手动刷新：设备已绑定")
                        _uiState.value = _uiState.value.copy(errorMessage = null)
                        _navigationEvents.emit(NavigationEvent.NavigateToChat)
                    }
                    
                    is BindingCheckResult.Unbound -> {
                        Log.d(TAG, "手动刷新：设备仍需绑定")
                        _uiState.value = _uiState.value.copy(errorMessage = null)
                    }
                    
                    is BindingCheckResult.Error -> {
                        Log.w(TAG, "手动刷新失败: ${result.message}")
                        _uiState.value = _uiState.value.copy(
                            errorMessage = "刷新失败: ${result.message}"
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "手动刷新异常", e)
                _uiState.value = _uiState.value.copy(
                    errorMessage = "刷新失败: ${e.message}"
                )
            }
        }
    }
    
    /**
     * 关闭绑定对话框
     */
    fun dismissBindingDialog() {
        Log.d(TAG, "关闭绑定对话框")
        _uiState.value = _uiState.value.copy(
            showBindingDialog = false,
            errorMessage = null
        )
        smartBindingManager.stopBinding()
    }
    
    /**
     * 重置绑定状态
     */
    fun resetBinding() {
        Log.d(TAG, "重置绑定状态")
        
        viewModelScope.launch {
            try {
                smartBindingManager.resetBinding()
                _uiState.value = _uiState.value.copy(
                    showBindingDialog = false,
                    errorMessage = null
                )
            } catch (e: Exception) {
                Log.e(TAG, "重置绑定异常", e)
                _uiState.value = _uiState.value.copy(
                    errorMessage = "重置失败: ${e.message}"
                )
            }
        }
    }
    
    /**
     * 清除错误消息
     */
    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }
}

/**
 * UI状态数据类
 */
data class SmartBindingUiState(
    val isLoading: Boolean = false,
    val showBindingDialog: Boolean = false,
    val errorMessage: String? = null
)

/**
 * 导航事件
 */
sealed class NavigationEvent {
    object NavigateToChat : NavigationEvent()
    object NavigateToConfig : NavigationEvent()
} 