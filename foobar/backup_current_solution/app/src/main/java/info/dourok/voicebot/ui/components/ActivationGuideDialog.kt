package info.dourok.voicebot.ui.components

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import info.dourok.voicebot.config.ActivationManager
import kotlinx.coroutines.delay

@Composable
fun ActivationGuideDialog(
    activationCode: String,
    frontendUrl: String,
    activationManager: ActivationManager,
    onActivationComplete: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var isChecking by remember { mutableStateOf(false) }
    var checkAttempts by remember { mutableStateOf(0) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    
    // 自动复制激活码到剪贴板
    LaunchedEffect(activationCode) {
        copyToClipboard(context, activationCode)
    }
    
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
                // 标题图标
                Icon(
                    imageVector = Icons.Default.DeviceHub,
                    contentDescription = null,
                    modifier = Modifier.size(64.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    text = "设备激活指南",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = "请按照以下步骤完成设备绑定",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                    textAlign = TextAlign.Center
                )
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // 激活码显示卡片
                ActivationCodeCard(
                    activationCode = activationCode,
                    context = context
                )
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // 步骤指导
                StepsGuideCard(
                    activationCode = activationCode,
                    frontendUrl = frontendUrl,
                    context = context
                )
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // 错误消息
                errorMessage?.let { error ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer
                        )
                    ) {
                        Text(
                            text = error,
                            modifier = Modifier.padding(16.dp),
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }
                
                // 检查状态显示
                if (isChecking) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer
                        )
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = "正在检查绑定状态... (${checkAttempts}/10)",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }
                
                // 操作按钮
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedButton(
                        onClick = onDismiss,
                        modifier = Modifier.weight(1f),
                        enabled = !isChecking
                    ) {
                        Text("稍后绑定")
                    }
                    
                    Button(
                        onClick = {
                            checkBindingStatus(
                                activationManager = activationManager,
                                onChecking = { attempts ->
                                    isChecking = true
                                    checkAttempts = attempts
                                    errorMessage = null
                                },
                                onSuccess = { websocketUrl ->
                                    isChecking = false
                                    onActivationComplete(websocketUrl)
                                },
                                onError = { error ->
                                    isChecking = false
                                    errorMessage = error
                                }
                            )
                        },
                        modifier = Modifier.weight(1f),
                        enabled = !isChecking
                    ) {
                        if (isChecking) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                        } else {
                            Text("检查绑定状态")
                        }
                    }
                }
            }
        }
    }
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
                .padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "您的激活码",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Text(
                text = activationCode,
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
                letterSpacing = 3.sp
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            OutlinedButton(
                onClick = { copyToClipboard(context, activationCode) },
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            ) {
                Icon(
                    imageVector = Icons.Default.ContentCopy,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("复制激活码")
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "激活码已自动复制到剪贴板",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.6f)
            )
        }
    }
}

@Composable
private fun StepsGuideCard(
    activationCode: String,
    frontendUrl: String,
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
                .padding(20.dp)
        ) {
            Text(
                text = "绑定步骤",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            val steps = listOf(
                StepInfo("1", "打开管理面板", "点击下方按钮打开设备管理页面"),
                StepInfo("2", "新增设备", "在管理面板中点击新增设备按钮"),
                StepInfo("3", "输入激活码", "粘贴激活码: $activationCode"),
                StepInfo("4", "完成绑定", "保存设备信息，完成绑定流程"),
                StepInfo("5", "检查状态", "返回应用，点击检查绑定状态")
            )
            
            steps.forEach { step ->
                StepItem(step = step)
                if (step != steps.last()) {
                    Spacer(modifier = Modifier.height(12.dp))
                }
            }
            
            Spacer(modifier = Modifier.height(20.dp))
            
            Button(
                onClick = { openManagementPanel(context, frontendUrl) },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.tertiary
                )
            ) {
                Icon(
                    imageVector = Icons.Default.OpenInBrowser,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("打开管理面板")
            }
        }
    }
}

@Composable
private fun StepItem(step: StepInfo) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Top
    ) {
        // 步骤编号
        Card(
            modifier = Modifier.size(32.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primary
            ),
            shape = RoundedCornerShape(16.dp)
        ) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = step.number,
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onPrimary
                )
            }
        }
        
        Spacer(modifier = Modifier.width(12.dp))
        
        // 步骤内容
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = step.title,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = step.description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
            )
        }
    }
}

private data class StepInfo(
    val number: String,
    val title: String,
    val description: String
)

private fun copyToClipboard(context: Context, text: String) {
    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    val clip = ClipData.newPlainText("激活码", text)
    clipboard.setPrimaryClip(clip)
    Toast.makeText(context, "激活码已复制: $text", Toast.LENGTH_SHORT).show()
}

private fun openManagementPanel(context: Context, frontendUrl: String) {
    try {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(frontendUrl))
        context.startActivity(intent)
    } catch (e: Exception) {
        Toast.makeText(context, "无法打开管理面板，请手动访问: $frontendUrl", Toast.LENGTH_LONG).show()
    }
}

private fun checkBindingStatus(
    activationManager: ActivationManager,
    onChecking: (Int) -> Unit,
    onSuccess: (String) -> Unit,
    onError: (String) -> Unit
) {
    // 这里应该启动一个协程来检查绑定状态
    // 由于需要访问ActivationManager的suspend函数，这里简化处理
    // 实际实现中应该在ViewModel中处理
    onError("请在ViewModel中实现绑定状态检查逻辑")
} 