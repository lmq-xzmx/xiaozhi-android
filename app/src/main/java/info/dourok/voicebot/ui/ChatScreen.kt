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
                InitializationProgress(stage = initializationStage)
            }
            
            DeviceState.FATAL_ERROR -> {
                ErrorDisplay(
                    onRetry = { viewModel.toggleChatState() }
                )
            }
            
            else -> {
                // 主聊天界面
                ChatContent(
                    chatMessages = chatMessages,
                    deviceState = deviceState,
                    emotion = emotion,
                    onToggleChat = { viewModel.toggleChatState() }
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
            modifier = Modifier.size(80.dp),
            color = MaterialTheme.colorScheme.primary,
            strokeWidth = 6.dp
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Text(
            text = "正在初始化小智助手...",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Medium
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = getInitializationStageText(stage),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // 进度指示器
        val progress = when (stage) {
            InitializationStage.CHECKING_PREREQUISITES -> 0.2f
            InitializationStage.INITIALIZING_PROTOCOL -> 0.4f
            InitializationStage.CONNECTING_NETWORK -> 0.6f
            InitializationStage.SETTING_UP_AUDIO -> 0.8f
            InitializationStage.STARTING_MESSAGE_PROCESSING -> 0.9f
            InitializationStage.READY -> 1.0f
        }
        
        androidx.compose.material3.LinearProgressIndicator(
            progress = progress,
            modifier = Modifier
                .fillMaxWidth(0.7f)
                .height(8.dp),
            color = MaterialTheme.colorScheme.primary,
            trackColor = MaterialTheme.colorScheme.surfaceVariant
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
            text = "⚠️",
            fontSize = 80.sp,
            color = MaterialTheme.colorScheme.error
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = "连接失败",
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.error,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "请检查网络连接或服务器状态",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Button(
            onClick = onRetry,
            modifier = Modifier
                .fillMaxWidth(0.6f)
                .height(48.dp)
        ) {
            Text(
                text = "重新连接",
                style = MaterialTheme.typography.titleMedium
            )
        }
    }
}

@Composable
fun ChatContent(
    chatMessages: List<Message>,
    deviceState: DeviceState,
    emotion: String,
    onToggleChat: () -> Unit
) {
    Column(modifier = Modifier.fillMaxSize()) {
        // 情感状态显示
        if (emotion != "neutral") {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                )
            ) {
                Text(
                    text = "😊 当前情感: $emotion",
                    modifier = Modifier.padding(12.dp),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
            }
        }
        
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
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = message.message,
                    color = if (isUser) 
                        MaterialTheme.colorScheme.onPrimary 
                    else 
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Text(
                    text = message.nowInString,
                    style = MaterialTheme.typography.bodySmall,
                    color = if (isUser) 
                        MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f)
                    else 
                        MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                )
            }
        }
    }
}

// 辅助函数
fun getDeviceStateText(deviceState: DeviceState): String {
    return when (deviceState) {
        DeviceState.UNKNOWN -> "未知状态"
        DeviceState.STARTING -> "启动中"
        DeviceState.WIFI_CONFIGURING -> "配置网络"
        DeviceState.IDLE -> "空闲"
        DeviceState.CONNECTING -> "连接中"
        DeviceState.LISTENING -> "监听中"
        DeviceState.SPEAKING -> "播放中"
        DeviceState.UPGRADING -> "升级中"
        DeviceState.ACTIVATING -> "激活中"
        DeviceState.FATAL_ERROR -> "连接错误"
    }
}

fun getInitializationStageText(stage: InitializationStage): String {
    return when (stage) {
        InitializationStage.CHECKING_PREREQUISITES -> "检查前置条件..."
        InitializationStage.INITIALIZING_PROTOCOL -> "初始化协议..."
        InitializationStage.CONNECTING_NETWORK -> "连接网络..."
        InitializationStage.SETTING_UP_AUDIO -> "设置音频..."
        InitializationStage.STARTING_MESSAGE_PROCESSING -> "启动消息处理..."
        InitializationStage.READY -> "准备就绪"
    }
}

fun getDeviceStateColor(deviceState: DeviceState): Color {
    return when (deviceState) {
        DeviceState.UNKNOWN -> Color.Gray
        DeviceState.STARTING -> Color(0xFFFF9800) // Orange
        DeviceState.WIFI_CONFIGURING -> Color(0xFF2196F3) // Blue
        DeviceState.IDLE -> Color(0xFF4CAF50) // Green
        DeviceState.CONNECTING -> Color(0xFF2196F3) // Blue
        DeviceState.LISTENING -> Color(0xFFF44336) // Red
        DeviceState.SPEAKING -> Color(0xFF9C27B0) // Purple
        DeviceState.UPGRADING -> Color(0xFF00BCD4) // Cyan
        DeviceState.ACTIVATING -> Color(0xFFFF9800) // Orange
        DeviceState.FATAL_ERROR -> Color(0xFFF44336) // Red
    }
}
