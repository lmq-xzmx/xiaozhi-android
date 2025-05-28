package info.dourok.voicebot.ui.config

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeviceConfigScreen(
    viewModel: DeviceConfigViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current
    
    // 监听事件
    LaunchedEffect(viewModel) {
        viewModel.events.collect { event ->
            when (event) {
                is DeviceConfigEvent.ShowMessage -> {
                    // 这里可以显示Snackbar或Toast
                }
                is DeviceConfigEvent.ShowError -> {
                    // 这里可以显示错误对话框
                }
                is DeviceConfigEvent.ShowManualBindDialog -> {
                    // 这里可以显示手动绑定对话框
                }
            }
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "设备配置",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 24.dp)
        )
        
        // 设备ID配置卡片
        DeviceIdConfigCard(
            deviceId = uiState.deviceId,
            onDeviceIdChange = viewModel::updateDeviceId,
            onSave = viewModel::saveDeviceId
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // 服务器地址配置卡片
        ServerUrlConfigCard(
            serverUrl = uiState.serverUrl,
            onServerUrlChange = viewModel::updateServerUrl,
            onSave = viewModel::saveServerUrl
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // 绑定状态卡片
        BindingStatusCard(
            bindingStatus = uiState.bindingStatus,
            lastCheckTime = viewModel.getFormattedLastCheckTime(),
            isChecking = uiState.isChecking,
            onRefresh = viewModel::checkBindingStatus,
            onManualBind = viewModel::showManualBindDialog
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // 激活码显示（如果需要绑定）
        if (uiState.activationCode != null) {
            ActivationCodeCard(
                activationCode = uiState.activationCode!!,
                onCopyCode = viewModel::copyActivationCode,
                onOpenManagement = viewModel::openManagementPanel
            )
            
            Spacer(modifier = Modifier.height(16.dp))
        }
        
        // WebSocket URL显示（如果已绑定）
        if (uiState.websocketUrl != null) {
            WebSocketInfoCard(
                websocketUrl = uiState.websocketUrl!!,
                serverUrl = uiState.serverUrl,
                deviceId = uiState.deviceId
            )
            
            Spacer(modifier = Modifier.height(16.dp))
        }
        
        // Android端OTA和WebSocket完整信息卡片
        AndroidConnectionInfoCard(
            deviceId = uiState.deviceId,
            serverUrl = uiState.serverUrl,
            websocketUrl = uiState.websocketUrl,
            bindingStatus = uiState.bindingStatus
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // 操作按钮
        ActionButtonsCard(
            onClearConfig = viewModel::clearAllConfig
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeviceIdConfigCard(
    deviceId: String,
    onDeviceIdChange: (String) -> Unit,
    onSave: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 12.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.PhoneAndroid,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "设备ID配置",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
            }
            
            OutlinedTextField(
                value = deviceId,
                onValueChange = onDeviceIdChange,
                label = { Text("设备ID (MAC地址格式)") },
                placeholder = { Text("例如: 00:11:22:33:44:55") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Button(
                onClick = onSave,
                modifier = Modifier.align(Alignment.End)
            ) {
                Icon(
                    imageVector = Icons.Default.Save,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text("保存")
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ServerUrlConfigCard(
    serverUrl: String,
    onServerUrlChange: (String) -> Unit,
    onSave: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 12.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Cloud,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "服务器地址",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
            }
            
            OutlinedTextField(
                value = serverUrl,
                onValueChange = onServerUrlChange,
                label = { Text("服务器URL") },
                placeholder = { Text("例如: http://192.168.31.164:8080") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Button(
                onClick = onSave,
                modifier = Modifier.align(Alignment.End)
            ) {
                Icon(
                    imageVector = Icons.Default.Save,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text("保存")
            }
        }
    }
}

@Composable
fun BindingStatusCard(
    bindingStatus: BindingStatus,
    lastCheckTime: String,
    isChecking: Boolean,
    onRefresh: () -> Unit,
    onManualBind: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 12.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Link,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "绑定状态",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
            }
            
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 8.dp)
            ) {
                val (statusText, statusColor, statusIcon) = when (bindingStatus) {
                    BindingStatus.Bound -> Triple("已绑定", Color.Green, Icons.Default.CheckCircle)
                    BindingStatus.Unbound -> Triple("未绑定", Color(0xFFFFA500), Icons.Default.Warning)
                    BindingStatus.Error -> Triple("检查失败", Color.Red, Icons.Default.Error)
                    BindingStatus.Unknown -> Triple("未知", Color.Gray, Icons.Default.Help)
                }
                
                Icon(
                    imageVector = statusIcon,
                    contentDescription = null,
                    tint = statusColor,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = statusText,
                    color = statusColor,
                    fontWeight = FontWeight.Medium
                )
            }
            
            Text(
                text = "最后检查: $lastCheckTime",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onRefresh,
                    enabled = !isChecking
                ) {
                    if (isChecking) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(if (isChecking) "检查中..." else "刷新状态")
                }
                
                OutlinedButton(
                    onClick = onManualBind
                ) {
                    Icon(
                        imageVector = Icons.Default.Settings,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("手动绑定")
                }
            }
        }
    }
}

@Composable
fun ActivationCodeCard(
    activationCode: String,
    onCopyCode: () -> Unit,
    onOpenManagement: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 12.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Key,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.secondary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "激活码",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
            }
            
            Text(
                text = "请使用以下激活码在管理面板中绑定设备：",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(bottom = 8.dp)
            )
            
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            ) {
                Text(
                    text = activationCode,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(16.dp)
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onCopyCode
                ) {
                    Icon(
                        imageVector = Icons.Default.ContentCopy,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("复制激活码")
                }
                
                OutlinedButton(
                    onClick = onOpenManagement
                ) {
                    Icon(
                        imageVector = Icons.Default.OpenInBrowser,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("打开管理面板")
                }
            }
        }
    }
}

@Composable
fun WebSocketInfoCard(
    websocketUrl: String,
    serverUrl: String,
    deviceId: String
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 12.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Cable,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "WebSocket连接",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
            }
            
            Text(
                text = "设备已成功绑定，WebSocket URL：",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(bottom = 8.dp)
            )
            
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            ) {
                Text(
                    text = websocketUrl,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(12.dp)
                )
            }
        }
    }
}

@Composable
fun AndroidConnectionInfoCard(
    deviceId: String,
    serverUrl: String,
    websocketUrl: String?,
    bindingStatus: BindingStatus
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 16.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Phone,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Android端连接信息",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
            }
            
            // 设备信息部分
            InfoSection(
                title = "设备信息",
                items = listOf(
                    "设备ID" to deviceId,
                    "平台" to "Android ${android.os.Build.VERSION.RELEASE}",
                    "制造商" to android.os.Build.MANUFACTURER,
                    "型号" to android.os.Build.MODEL
                )
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // OTA信息部分
            InfoSection(
                title = "OTA信息",
                items = listOf(
                    "OTA服务器" to serverUrl,
                    "OTA端点" to "${serverUrl}/xiaozhi/ota/",
                    "前端管理" to "${serverUrl}/#/home",
                    "绑定状态" to when (bindingStatus) {
                        BindingStatus.Bound -> "✅ 已绑定"
                        BindingStatus.Unbound -> "❌ 未绑定"
                        BindingStatus.Error -> "⚠️ 错误"
                        BindingStatus.Unknown -> "❓ 未知"
                    }
                )
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // WebSocket信息部分
            InfoSection(
                title = "WebSocket信息",
                items = if (websocketUrl != null) {
                    listOf(
                        "WebSocket URL" to websocketUrl,
                        "连接状态" to "✅ 可用",
                        "协议版本" to "WebSocket 13",
                        "数据格式" to "Opus音频 + JSON控制"
                    )
                } else {
                    listOf(
                        "WebSocket URL" to "❌ 未配置",
                        "连接状态" to "❌ 不可用",
                        "原因" to "设备尚未绑定"
                    )
                }
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // 端口信息部分
            InfoSection(
                title = "端口信息",
                items = listOf(
                    "HTTP端口" to "8002 (OTA服务)",
                    "WebSocket端口" to "8000 (实时通信)",
                    "管理面板端口" to "8002 (前端界面)",
                    "音频编解码" to "Opus (48kHz, 16bit)"
                )
            )
        }
    }
}

@Composable
private fun InfoSection(
    title: String,
    items: List<Pair<String, String>>
) {
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        
        items.forEach { (key, value) ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 2.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "$key:",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSecondaryContainer,
                    modifier = Modifier.weight(1f)
                )
                Text(
                    text = value,
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
fun ActionButtonsCard(
    onClearConfig: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 12.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Build,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "操作",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
            }
            
            OutlinedButton(
                onClick = onClearConfig,
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.error
                )
            ) {
                Icon(
                    imageVector = Icons.Default.DeleteForever,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text("清除所有配置")
            }
        }
    }
} 