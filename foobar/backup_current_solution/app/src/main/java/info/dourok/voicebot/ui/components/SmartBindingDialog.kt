package info.dourok.voicebot.ui.components

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import info.dourok.voicebot.binding.BindingEvent
import info.dourok.voicebot.binding.BindingState

@Composable
fun SmartBindingDialog(
    bindingState: BindingState,
    bindingEvent: BindingEvent?,
    onDismiss: () -> Unit,
    onStartBinding: (String) -> Unit,
    onStopBinding: () -> Unit,
    onManualRefresh: () -> Unit
) {
    val context = LocalContext.current
    
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(
            dismissOnBackPress = true,
            dismissOnClickOutside = false
        )
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface
            )
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp)
                    .verticalScroll(rememberScrollState()),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                when (bindingState) {
                    is BindingState.NeedsBinding -> {
                        NeedsBindingContent(
                            activationCode = bindingState.activationCode,
                            onStartBinding = onStartBinding,
                            onDismiss = onDismiss,
                            context = context
                        )
                    }
                    
                    is BindingState.BindingInProgress -> {
                        BindingInProgressContent(
                            activationCode = bindingState.activationCode,
                            bindingEvent = bindingEvent,
                            onStopBinding = onStopBinding,
                            onManualRefresh = onManualRefresh,
                            context = context
                        )
                    }
                    
                    is BindingState.Bound -> {
                        BindingSuccessContent(
                            websocketUrl = bindingState.websocketUrl,
                            onDismiss = onDismiss
                        )
                    }
                    
                    is BindingState.Error -> {
                        BindingErrorContent(
                            errorMessage = bindingState.message,
                            onRetry = onManualRefresh,
                            onDismiss = onDismiss
                        )
                    }
                    
                    is BindingState.PollingTimeout -> {
                        BindingTimeoutContent(
                            activationCode = bindingState.activationCode,
                            onRetry = onManualRefresh,
                            onDismiss = onDismiss
                        )
                    }
                    
                    else -> {
                        // 默认加载状态
                        LoadingContent()
                    }
                }
            }
        }
    }
}

@Composable
private fun NeedsBindingContent(
    activationCode: String,
    onStartBinding: (String) -> Unit,
    onDismiss: () -> Unit,
    context: Context
) {
    Icon(
        imageVector = Icons.Default.DeviceHub,
        contentDescription = null,
        modifier = Modifier.size(64.dp),
        tint = MaterialTheme.colorScheme.primary
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "设备需要绑定",
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    Text(
        text = "首次使用需要将设备绑定到您的账户",
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
        textAlign = TextAlign.Center
    )
    
    Spacer(modifier = Modifier.height(24.dp))
    
    // 激活码显示
    ActivationCodeCard(activationCode = activationCode, context = context)
    
    Spacer(modifier = Modifier.height(24.dp))
    
    // 操作按钮
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        OutlinedButton(
            onClick = onDismiss,
            modifier = Modifier.weight(1f)
        ) {
            Text("稍后绑定")
        }
        
        Button(
            onClick = { onStartBinding(activationCode) },
            modifier = Modifier.weight(1f)
        ) {
            Text("开始绑定")
        }
    }
}

@Composable
private fun BindingInProgressContent(
    activationCode: String,
    bindingEvent: BindingEvent?,
    onStopBinding: () -> Unit,
    onManualRefresh: () -> Unit,
    context: Context
) {
    Icon(
        imageVector = Icons.Default.Sync,
        contentDescription = null,
        modifier = Modifier.size(64.dp),
        tint = MaterialTheme.colorScheme.primary
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "正在检查绑定状态",
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    // 进度信息
    when (bindingEvent) {
        is BindingEvent.PollingUpdate -> {
            Text(
                text = "检查进度: ${bindingEvent.currentAttempt}/${bindingEvent.maxAttempts}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            LinearProgressIndicator(
                progress = bindingEvent.currentAttempt.toFloat() / bindingEvent.maxAttempts,
                modifier = Modifier.fillMaxWidth()
            )
        }
        
        else -> {
            CircularProgressIndicator(
                modifier = Modifier.size(32.dp)
            )
        }
    }
    
    Spacer(modifier = Modifier.height(24.dp))
    
    // 绑定指导
    BindingInstructions(activationCode = activationCode, context = context)
    
    Spacer(modifier = Modifier.height(24.dp))
    
    // 操作按钮
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        OutlinedButton(
            onClick = onStopBinding,
            modifier = Modifier.weight(1f)
        ) {
            Text("停止检查")
        }
        
        Button(
            onClick = onManualRefresh,
            modifier = Modifier.weight(1f)
        ) {
            Text("手动检查")
        }
    }
}

@Composable
private fun BindingSuccessContent(
    websocketUrl: String,
    onDismiss: () -> Unit
) {
    Icon(
        imageVector = Icons.Default.CheckCircle,
        contentDescription = null,
        modifier = Modifier.size(64.dp),
        tint = Color(0xFF4CAF50)
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "绑定成功！",
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold,
        color = Color(0xFF4CAF50)
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    Text(
        text = "设备已成功绑定到您的账户",
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
        textAlign = TextAlign.Center
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "连接地址: ${websocketUrl.take(50)}...",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
        textAlign = TextAlign.Center
    )
    
    Spacer(modifier = Modifier.height(24.dp))
    
    Button(
        onClick = onDismiss,
        modifier = Modifier.fillMaxWidth()
    ) {
        Text("开始使用")
    }
}

@Composable
private fun BindingErrorContent(
    errorMessage: String,
    onRetry: () -> Unit,
    onDismiss: () -> Unit
) {
    Icon(
        imageVector = Icons.Default.Error,
        contentDescription = null,
        modifier = Modifier.size(64.dp),
        tint = MaterialTheme.colorScheme.error
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "绑定失败",
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.error
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    Text(
        text = errorMessage,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
        textAlign = TextAlign.Center
    )
    
    Spacer(modifier = Modifier.height(24.dp))
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        OutlinedButton(
            onClick = onDismiss,
            modifier = Modifier.weight(1f)
        ) {
            Text("取消")
        }
        
        Button(
            onClick = onRetry,
            modifier = Modifier.weight(1f)
        ) {
            Text("重试")
        }
    }
}

@Composable
private fun BindingTimeoutContent(
    activationCode: String,
    onRetry: () -> Unit,
    onDismiss: () -> Unit
) {
    Icon(
        imageVector = Icons.Default.AccessTime,
        contentDescription = null,
        modifier = Modifier.size(64.dp),
        tint = MaterialTheme.colorScheme.tertiary
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "检查超时",
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    Text(
        text = "绑定状态检查超时，请确认是否已在管理面板完成绑定",
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
        textAlign = TextAlign.Center
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "激活码: $activationCode",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
    )
    
    Spacer(modifier = Modifier.height(24.dp))
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        OutlinedButton(
            onClick = onDismiss,
            modifier = Modifier.weight(1f)
        ) {
            Text("稍后再试")
        }
        
        Button(
            onClick = onRetry,
            modifier = Modifier.weight(1f)
        ) {
            Text("重新检查")
        }
    }
}

@Composable
private fun LoadingContent() {
    CircularProgressIndicator(
        modifier = Modifier.size(64.dp)
    )
    
    Spacer(modifier = Modifier.height(16.dp))
    
    Text(
        text = "正在初始化...",
        style = MaterialTheme.typography.bodyMedium
    )
}

@Composable
private fun ActivationCodeCard(
    activationCode: String,
    context: Context
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "您的激活码",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = activationCode,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
                letterSpacing = 2.sp
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            OutlinedButton(
                onClick = { copyToClipboard(context, activationCode) },
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            ) {
                Icon(
                    imageVector = Icons.Default.ContentCopy,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("复制激活码")
            }
        }
    }
}

@Composable
private fun BindingInstructions(
    activationCode: String,
    context: Context
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "绑定步骤",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            val steps = listOf(
                "1. 点击下方按钮打开管理面板",
                "2. 在管理面板点击新增设备",
                "3. 输入激活码: $activationCode",
                "4. 完成绑定，应用将自动检测"
            )
            
            steps.forEach { step ->
                Text(
                    text = step,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.8f),
                    modifier = Modifier.padding(vertical = 2.dp)
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Button(
                onClick = { openManagementPanel(context) },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.tertiary
                )
            ) {
                Icon(
                    imageVector = Icons.Default.OpenInBrowser,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("打开管理面板")
            }
        }
    }
}

private fun copyToClipboard(context: Context, text: String) {
    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    val clip = ClipData.newPlainText("激活码", text)
    clipboard.setPrimaryClip(clip)
    Toast.makeText(context, "激活码已复制: $text", Toast.LENGTH_SHORT).show()
}

private fun openManagementPanel(context: Context) {
    try {
        val managementUrl = "http://47.122.144.73:8002/#/home"
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(managementUrl))
        context.startActivity(intent)
    } catch (e: Exception) {
        Toast.makeText(context, "无法打开管理面板，请手动访问", Toast.LENGTH_SHORT).show()
    }
} 