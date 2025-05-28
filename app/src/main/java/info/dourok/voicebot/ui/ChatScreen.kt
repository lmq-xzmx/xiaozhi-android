package info.dourok.voicebot.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import info.dourok.voicebot.config.ActivationState
import info.dourok.voicebot.ui.components.ActivationGuideDialog
import java.util.*

@Composable
fun ChatScreen(
    viewModel: ChatViewModel = hiltViewModel()
) {
    val messages by viewModel.display.chatFlow.collectAsState()
    val emotion by viewModel.display.emotionFlow.collectAsState()
    val deviceState by viewModel.deviceStateFlow.collectAsState()
    val initializationStatus by viewModel.initializationStatus.collectAsState()
    val activationState by viewModel.activationState.collectAsState()
    val errorMessage by viewModel.errorMessage.collectAsState()
    val isConnecting by viewModel.isConnecting.collectAsState()
    
    var showActivationDialog by remember { mutableStateOf(false) }
    var activationCode by remember { mutableStateOf("") }
    var frontendUrl by remember { mutableStateOf("") }
    
    // 自动启动初始化
    LaunchedEffect(Unit) {
        viewModel.startInitialization()
    }
    
    // 监听激活状态变化
    LaunchedEffect(activationState) {
        when (val currentState = activationState) {
            is ActivationState.NeedsActivation -> {
                activationCode = currentState.activationCode
                frontendUrl = currentState.frontendUrl ?: "http://47.122.144.73:8002/#/home"
                showActivationDialog = true
            }
            is ActivationState.Activated -> {
                showActivationDialog = false
            }
            else -> {
                // 其他状态不显示激活对话框
            }
        }
    }
    
    // 根据初始化状态显示不同内容
    when (initializationStatus) {
        is InitializationStatus.NotStarted,
        is InitializationStatus.InProgress -> {
            InitializationScreen(
                isConnecting = isConnecting,
                status = initializationStatus
            )
        }
        is InitializationStatus.Failed -> {
            ErrorScreen(
                error = (initializationStatus as InitializationStatus.Failed).error,
                onRetry = { viewModel.startInitialization() }
            )
        }
        is InitializationStatus.NeedsActivation -> {
            // 显示激活等待界面
            ActivationWaitingScreen(
                activationCode = (initializationStatus as InitializationStatus.NeedsActivation).activationCode,
                onShowDialog = { showActivationDialog = true }
            )
        }
        is InitializationStatus.Completed -> {
            ChatContent(
                messages = messages,
                emotion = emotion,
                deviceState = deviceState,
                errorMessage = errorMessage,
                viewModel = viewModel
            )
        }
    }
    
    // 激活引导对话框
    if (showActivationDialog && activationCode.isNotEmpty()) {
        ActivationGuideDialog(
            activationCode = activationCode,
            frontendUrl = frontendUrl,
            activationManager = hiltViewModel<ChatViewModel>().activationManager,
            onActivationComplete = { websocketUrl ->
                showActivationDialog = false
                viewModel.onActivationComplete(websocketUrl)
            },
            onDismiss = {
                showActivationDialog = false
            }
        )
    }
}

@Composable
fun ActivationWaitingScreen(
    activationCode: String,
    onShowDialog: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "🔗",
            style = MaterialTheme.typography.displayLarge
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = "设备需要激活",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "您的设备尚未激活，需要在管理面板中完成绑定",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer
            )
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "激活码",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = activationCode,
                    style = MaterialTheme.typography.headlineLarge,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Button(
            onClick = onShowDialog,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("开始激活")
        }
    }
}

@Composable
fun InitializationScreen(
    isConnecting: Boolean,
    status: InitializationStatus
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(64.dp),
            strokeWidth = 4.dp,
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = when (status) {
                is InitializationStatus.NotStarted -> "准备初始化..."
                is InitializationStatus.InProgress -> "正在初始化聊天功能..."
                else -> "初始化中..."
            },
            style = MaterialTheme.typography.headlineSmall,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "正在检查设备激活状态并配置语音功能\n请稍候...",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )
    }
}

@Composable
fun ErrorScreen(
    error: String,
    onRetry: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "😞",
            style = MaterialTheme.typography.displayLarge
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = "初始化失败",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.error
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = error,
            style = MaterialTheme.typography.bodyMedium,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Button(
            onClick = onRetry,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("重试")
        }
    }
}

@Composable
fun ChatContent(
    messages: List<Message>,
    emotion: String,
    deviceState: DeviceState,
    errorMessage: String?,
    viewModel: ChatViewModel
) {
    // Emotion to emoji mapping
    val emotionEmojiMap = mapOf(
        "neutral" to "😐",
        "happy" to "😊",
        "laughing" to "😂",
        "funny" to "🤡",
        "sad" to "😢",
        "angry" to "😠",
        "crying" to "😭",
        "loving" to "🥰",
        "embarrassed" to "😳",
        "surprised" to "😮",
        "shocked" to "😱",
        "thinking" to "🤔",
        "winking" to "😉",
        "cool" to "😎",
        "relaxed" to "😌",
        "delicious" to "😋",
        "kissy" to "😘",
        "confident" to "😏",
        "sleepy" to "😴",
        "silly" to "🤪",
        "confused" to "😕"
    )
    
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Emotion display at top center with bigger emoji
        Box(
            modifier = Modifier.padding(vertical = 16.dp),
            contentAlignment = Alignment.Center
        ) {
            when (deviceState) {
                DeviceState.CONNECTING, DeviceState.STARTING -> {
                    CircularProgressIndicator(
                        modifier = Modifier.size(64.dp), // 与emoji大小匹配
                        strokeWidth = 4.dp,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
                else -> {
                    Text(
                        text = emotionEmojiMap[emotion.lowercase(Locale.getDefault())] ?: "😐",
                        style = androidx.compose.ui.text.TextStyle(
                            fontSize = 64.sp,
                            lineHeight = 64.sp
                        )
                    )
                }
            }
        }

        // Device State Text
        Text(
            text = when (deviceState) {
                DeviceState.IDLE -> "✅ 就绪"
                DeviceState.LISTENING -> "🎤 监听中"
                DeviceState.SPEAKING -> "🔊 回复中"
                DeviceState.CONNECTING -> "🔗 连接中"
                DeviceState.STARTING -> "⚡ 启动中"
                DeviceState.ACTIVATING -> "🔐 激活中"
                DeviceState.FATAL_ERROR -> "❌ 错误"
                DeviceState.UPGRADING -> "📦 升级中"
                DeviceState.WIFI_CONFIGURING -> "📶 配置网络"
                DeviceState.UNKNOWN -> "❓ 未知状态"
            },
            style = MaterialTheme.typography.bodySmall,
            color = when (deviceState) {
                DeviceState.FATAL_ERROR -> MaterialTheme.colorScheme.error
                DeviceState.IDLE -> MaterialTheme.colorScheme.primary
                DeviceState.LISTENING -> MaterialTheme.colorScheme.primary
                DeviceState.SPEAKING -> MaterialTheme.colorScheme.secondary
                else -> MaterialTheme.colorScheme.onSurface
            },
            modifier = Modifier.padding(bottom = 8.dp)
        )
        
        // Error message display
        errorMessage?.let { error ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer
                )
            ) {
                Text(
                    text = error,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onErrorContainer,
                    modifier = Modifier.padding(12.dp)
                )
            }
        }

        LazyColumn(
            modifier = Modifier.weight(1f),
            reverseLayout = true,
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(messages.asReversed()) { message ->
                ChatMessageItem(message)
            }
        }
        
        // 操作按钮区域改为状态显示区域
        ChatActionButtons(
            deviceState = deviceState
        )
    }
}

@Composable
fun ChatMessageItem(message: Message) {
    val isCurrentUser = message.sender == "user"

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 8.dp),
        horizontalArrangement = if (isCurrentUser) Arrangement.End else Arrangement.Start
    ) {
        Card(
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(
                containerColor = if (isCurrentUser)
                    MaterialTheme.colorScheme.primary
                else
                    MaterialTheme.colorScheme.surfaceVariant
            ),
            modifier = Modifier.widthIn(max = 300.dp)
        ) {
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                Text(
                    text = message.sender,
                    style = MaterialTheme.typography.labelLarge,
                    color = if (isCurrentUser)
                        MaterialTheme.colorScheme.onPrimary
                    else
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = message.message,
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (isCurrentUser)
                        MaterialTheme.colorScheme.onPrimary
                    else
                        MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 4.dp)
                )
                Text(
                    text = message.nowInString,
                    style = MaterialTheme.typography.labelSmall,
                    color = if (isCurrentUser)
                        MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f)
                    else
                        MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                    modifier = Modifier
                        .padding(top = 4.dp)
                        .align(Alignment.End)
                )
            }
        }
    }
}

@Composable
fun ChatActionButtons(
    deviceState: DeviceState
) {
    // ESP32兼容：完全移除手动按钮，打断机制完全自动化
    // 只显示设备状态信息，不提供任何手动控制按钮
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        colors = CardDefaults.cardColors(
            containerColor = when (deviceState) {
                DeviceState.LISTENING -> MaterialTheme.colorScheme.primaryContainer
                DeviceState.SPEAKING -> MaterialTheme.colorScheme.secondaryContainer
                DeviceState.CONNECTING, DeviceState.STARTING -> MaterialTheme.colorScheme.tertiaryContainer
                DeviceState.FATAL_ERROR -> MaterialTheme.colorScheme.errorContainer
                else -> MaterialTheme.colorScheme.surfaceVariant
            }
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            when (deviceState) {
                DeviceState.IDLE -> {
                    Icon(
                        imageVector = Icons.Default.CheckCircle,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp),
                        tint = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "✅ 就绪 - ESP32兼容模式",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                DeviceState.CONNECTING -> {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "🔗 连接中...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                }
                DeviceState.LISTENING -> {
                    Icon(
                        imageVector = Icons.Default.Mic,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp),
                        tint = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "🎤 自动监听中 - 语音打断",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
                DeviceState.SPEAKING -> {
                    Icon(
                        imageVector = Icons.Default.VolumeUp,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp),
                        tint = MaterialTheme.colorScheme.onSecondaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "🔊 播放中 - 说话即可打断",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSecondaryContainer
                    )
                }
                DeviceState.STARTING -> {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "⚡ 正在启动...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                }
                DeviceState.ACTIVATING -> {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "🔐 设备激活中...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                }
                DeviceState.FATAL_ERROR -> {
                    Icon(
                        imageVector = Icons.Default.Error,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp),
                        tint = MaterialTheme.colorScheme.onErrorContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "❌ 系统错误",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onErrorContainer
                    )
                }
                DeviceState.UPGRADING -> {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "📦 系统升级中...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                }
                DeviceState.WIFI_CONFIGURING -> {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "📶 配置网络...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                }
                DeviceState.UNKNOWN -> {
                    Icon(
                        imageVector = Icons.Default.Help,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "❓ 未知状态",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}
