package info.dourok.voicebot

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.app.ActivityCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.android.AndroidEntryPoint
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.android.components.ActivityComponent
import info.dourok.voicebot.ui.ActivationScreen
import info.dourok.voicebot.ui.ChatScreen
import info.dourok.voicebot.ui.ServerFormScreen
import info.dourok.voicebot.ui.SmartBindingViewModel
import info.dourok.voicebot.ui.NavigationEvent
import info.dourok.voicebot.ui.config.DeviceConfigScreen
import info.dourok.voicebot.ui.components.SmartBindingDialog
import info.dourok.voicebot.ui.theme.VoicebotclientandroidTheme
import kotlinx.coroutines.flow.SharedFlow

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    companion object {
        private const val TAG = "MainActivity"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        Log.d(TAG, "🚀 MainActivity onCreate 开始")
        
        try {
            // 基本设置
            setupBasicConfiguration()
            
            // 权限检查（非阻塞）
            checkPermissions()
            
            // 设置UI
            setupUI()
            
            Log.d(TAG, "✅ MainActivity onCreate 完成")
            
        } catch (e: Exception) {
            Log.e(TAG, "💥 MainActivity onCreate 异常", e)
            
            // 即使出现异常，也尝试设置基本UI
            try {
                setupFallbackUI()
            } catch (fallbackException: Exception) {
                Log.e(TAG, "💥 连fallback UI都失败了", fallbackException)
                // 这种情况下让系统处理
                throw e
            }
        }
    }
    
    /**
     * 设置基本配置
     */
    private fun setupBasicConfiguration() {
        try {
            enableEdgeToEdge()
            Log.d(TAG, "✅ Edge-to-edge 配置完成")
        } catch (e: Exception) {
            Log.w(TAG, "⚠️ Edge-to-edge 配置失败", e)
            // 这不是关键功能，继续执行
        }
    }
    
    /**
     * 检查权限（非阻塞）
     */
    private fun checkPermissions() {
        try {
            if (ActivityCompat.checkSelfPermission(
                    this,
                    Manifest.permission.RECORD_AUDIO
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                Log.d(TAG, "🎤 请求录音权限")
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.RECORD_AUDIO),
                    0
                )
            } else {
                Log.d(TAG, "✅ 录音权限已授予")
            }
        } catch (e: Exception) {
            Log.w(TAG, "⚠️ 权限检查失败", e)
            // 权限问题不应该阻止应用启动
        }
    }
    
    /**
     * 设置主UI
     */
    private fun setupUI() {
        setContent {
            VoicebotclientandroidTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Column {
                        Spacer(modifier = Modifier.height(innerPadding.calculateTopPadding()))
                        SafeAppNavigation()
                    }
                }
            }
        }
    }
    
    /**
     * 设置备用UI（当主UI失败时使用）
     */
    private fun setupFallbackUI() {
        Log.w(TAG, "🆘 使用备用UI")
        setContent {
            VoicebotclientandroidTheme {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "应用启动中...",
                            style = MaterialTheme.typography.headlineSmall
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        CircularProgressIndicator()
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "如果长时间无响应，请重启应用",
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SafeAppNavigation() {
    var hasError by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }
    
    if (hasError) {
        // 错误状态UI
        ErrorRecoveryScreen(
            errorMessage = errorMessage,
            onRetry = { 
                hasError = false
                errorMessage = ""
            }
        )
    } else {
        // 正常导航，使用LaunchedEffect处理异常
        LaunchedEffect(Unit) {
            try {
                // 在这里可以进行一些初始化检查
                Log.d("SafeAppNavigation", "开始安全导航初始化")
            } catch (e: Exception) {
                Log.e("SafeAppNavigation", "导航初始化异常", e)
                hasError = true
                errorMessage = "导航初始化失败: ${e.message}"
            }
        }
        
        // 直接调用SmartAppNavigation，不使用try-catch包装
        SmartAppNavigation()
    }
}

@Composable
fun ErrorRecoveryScreen(
    errorMessage: String,
    onRetry: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            Icons.Default.Warning,
            contentDescription = "错误",
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.error
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "应用启动遇到问题",
            style = MaterialTheme.typography.headlineSmall,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = errorMessage,
            style = MaterialTheme.typography.bodyMedium,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(
            onClick = onRetry,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("重试")
        }
    }
}

@Composable
fun SmartAppNavigation() {
    val navController = rememberNavController()
    val activity = LocalContext.current as Activity
    val entryPoint = EntryPointAccessors.fromActivity(activity, NavigationEntryPoint::class.java)
    val navigationEvents = entryPoint.getNavigationEvents()
    
    // 智能绑定ViewModel
    val smartBindingViewModel: SmartBindingViewModel = hiltViewModel()
    val bindingState by smartBindingViewModel.bindingState.collectAsState()
    val bindingEvents by smartBindingViewModel.bindingEvents.collectAsState()
    val uiState by smartBindingViewModel.uiState.collectAsState()

    Log.d("SmartAppNavigation", "navigationEvents: $navigationEvents")

    // 监听导航事件
    LaunchedEffect(navController) {
        navigationEvents.collect { route ->
            navController.navigate(route)
        }
    }
    
    // 监听智能绑定导航事件
    LaunchedEffect(smartBindingViewModel) {
        smartBindingViewModel.navigationEvents.collect { event ->
            when (event) {
                is NavigationEvent.NavigateToChat -> {
                    Log.d("SmartAppNavigation", "导航到聊天界面")
                    navController.navigate("chat") {
                        // 清除回退栈，防止用户返回到绑定界面
                        popUpTo("device_config") { inclusive = true }
                    }
                }
                is NavigationEvent.NavigateToConfig -> {
                    Log.d("SmartAppNavigation", "导航到配置界面")
                    navController.navigate("device_config")
                }
            }
        }
    }
    
    // 应用启动时自动初始化绑定
    LaunchedEffect(Unit) {
        Log.d("SmartAppNavigation", "应用启动，开始设备绑定初始化")
        smartBindingViewModel.initializeDeviceBinding()
    }

    // 主导航
    NavHost(navController = navController, startDestination = "device_config") {
        composable("device_config") { 
            DeviceConfigWithSmartBinding(
                smartBindingViewModel = smartBindingViewModel,
                uiState = uiState,
                bindingState = bindingState,
                bindingEvents = bindingEvents
            )
        }
        composable("form") { ServerFormScreen() }
        composable("activation") { ActivationScreen() }
        composable("chat") { ChatScreen() }
    }
}

@Composable
fun DeviceConfigWithSmartBinding(
    smartBindingViewModel: SmartBindingViewModel,
    uiState: info.dourok.voicebot.ui.SmartBindingUiState,
    bindingState: info.dourok.voicebot.binding.BindingState,
    bindingEvents: info.dourok.voicebot.binding.BindingEvent?
) {
    // 显示设备配置界面
    DeviceConfigScreen()
    
    // 显示加载指示器
    if (uiState.isLoading) {
        LoadingOverlay()
    }
    
    // 显示智能绑定对话框
    if (uiState.showBindingDialog) {
        SmartBindingDialog(
            bindingState = bindingState,
            bindingEvent = bindingEvents,
            onDismiss = { smartBindingViewModel.dismissBindingDialog() },
            onStartBinding = { activationCode ->
                smartBindingViewModel.startSmartBinding(activationCode)
            },
            onStopBinding = { smartBindingViewModel.stopBinding() },
            onManualRefresh = { smartBindingViewModel.manualRefresh() }
        )
    }
}

@Composable
fun LoadingOverlay() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    color = MaterialTheme.colorScheme.surface.copy(alpha = 0.8f)
                )
        )
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            CircularProgressIndicator()
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "正在初始化设备...",
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

