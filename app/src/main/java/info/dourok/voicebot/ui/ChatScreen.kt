package info.dourok.voicebot.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun ChatScreen(
    viewModel: ChatViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val deviceState by viewModel.deviceStateFlow.collectAsState()
    val initializationStage by viewModel.initializationStage.collectAsState()
    val chatMessages by viewModel.display.chatFlow.collectAsState()
    val emotion by viewModel.display.emotionFlow.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // 顶部状态栏
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Button(onClick = onNavigateBack) {
                Text("返回")
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = getDeviceStateText(deviceState),
                    style = MaterialTheme.typography.titleMedium,
                    color = getDeviceStateColor(deviceState)
                )
                
                if (deviceState == DeviceState.STARTING) {
                    Text(
                        text = getInitializationStageText(initializationStage),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // 状态指示器
            Box(
                modifier = Modifier
                    .size(12.dp)
                    .background(
                        color = getDeviceStateColor(deviceState),
                        shape = CircleShape
                    )
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // 根据设备状态显示不同内容
        when (deviceState) {
            DeviceState.STARTING -> {
                InitializationProgress(initializationStage)
            }
            
            DeviceState.FATAL_ERROR -> {
                ErrorDisplay(
                    onRetry = { 
                        viewModel.toggleChatState()
                    }
                )
            }
            
            DeviceState.UNKNOWN, DeviceState.WIFI_CONFIGURING, DeviceState.UPGRADING -> {
                // 其他状态显示等待界面
                InitializationProgress(initializationStage)
            }
            
            else -> {
                // 正常聊天界面
                ChatContent(
                    chatMessages = chatMessages,
                    emotion = emotion,
                    deviceState = deviceState,
                    onToggleChat = { viewModel.toggleChatState() },
                    onStartListening = { viewModel.startListening() },
                    onStopListening = { viewModel.stopListening() }
                )
            }
        }
    }
}

@Composable
fun InitializationProgress(stage: InitializationStage) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(64.dp),
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = "正在初始化系统...",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = getInitializationStageText(stage),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun ErrorDisplay(onRetry: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "❌",
            fontSize = 64.sp
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "系统初始化失败",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.error
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "请检查网络连接和服务器配置",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(onClick = onRetry) {
            Text("重试")
        }
    }
}

@Composable
fun ChatContent(
    chatMessages: List<Message>,
    emotion: String,
    deviceState: DeviceState,
    onToggleChat: () -> Unit,
    onStartListening: () -> Unit,
    onStopListening: () -> Unit
) {
    Column(modifier = Modifier.fillMaxSize()) {
        // 聊天消息列表
        LazyColumn(
            modifier = Modifier.weight(1f),
            reverseLayout = true
        ) {
            items(chatMessages.reversed()) { message ->
                ChatMessageItem(message = message)
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // 控制按钮
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            Button(
                onClick = onToggleChat,
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    when (deviceState) {
                        DeviceState.LISTENING -> "停止对话"
                        DeviceState.SPEAKING -> "中断播放"
                        else -> "开始对话"
                    }
                )
            }
        }
    }
}

@Composable
fun ChatMessageItem(message: Message) {
    val isUser = message.sender == "user"
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(0.8f),
            colors = CardDefaults.cardColors(
                containerColor = if (isUser) 
                    MaterialTheme.colorScheme.primary 
                else 
                    MaterialTheme.colorScheme.surfaceVariant
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                text = message.message,
                modifier = Modifier.padding(12.dp),
                color = if (isUser) 
                    MaterialTheme.colorScheme.onPrimary 
                else 
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

// 辅助函数
fun getDeviceStateText(state: DeviceState): String {
    return when (state) {
        DeviceState.STARTING -> "启动中"
        DeviceState.IDLE -> "空闲"
        DeviceState.LISTENING -> "监听中"
        DeviceState.SPEAKING -> "播放中"
        DeviceState.CONNECTING -> "连接中"
        DeviceState.ACTIVATING -> "激活中"
        DeviceState.FATAL_ERROR -> "错误"
        DeviceState.UNKNOWN -> "未知状态"
        DeviceState.WIFI_CONFIGURING -> "配置WiFi"
        DeviceState.UPGRADING -> "升级中"
    }
}

fun getDeviceStateColor(state: DeviceState): Color {
    return when (state) {
        DeviceState.STARTING -> Color.Blue
        DeviceState.IDLE -> Color.Gray
        DeviceState.LISTENING -> Color.Green
        DeviceState.SPEAKING -> Color.Magenta
        DeviceState.CONNECTING -> Color.Cyan
        DeviceState.ACTIVATING -> Color.Yellow
        DeviceState.FATAL_ERROR -> Color.Red
        DeviceState.UNKNOWN -> Color.Gray
        DeviceState.WIFI_CONFIGURING -> Color.Blue
        DeviceState.UPGRADING -> Color(0xFFFFA500)
    }
}

fun getInitializationStageText(stage: InitializationStage): String {
    return when (stage) {
        InitializationStage.CHECKING_PREREQUISITES -> "检查系统环境"
        InitializationStage.INITIALIZING_PROTOCOL -> "初始化网络协议"
        InitializationStage.CONNECTING_NETWORK -> "建立网络连接"
        InitializationStage.SETTING_UP_AUDIO -> "配置音频系统"
        InitializationStage.STARTING_MESSAGE_PROCESSING -> "启动消息处理"
        InitializationStage.READY -> "系统就绪"
    }
}
