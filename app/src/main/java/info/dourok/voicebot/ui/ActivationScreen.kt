package info.dourok.voicebot.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun ActivationScreen(
    viewModel: ActivationViewModel = hiltViewModel()
) {
    val activationData by viewModel.activationFlow.collectAsState(null)
    val bindingStatus by viewModel.bindingStatus.collectAsState()
    
    activationData?.let { activation ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            
            // 标题
            Text(
                text = "设备激活",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )
            
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
                modifier = Modifier.weight(1f)
            ) {
                
                // 激活码显示卡片
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    ),
                    elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(
                            imageVector = Icons.Default.Key,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(48.dp)
                        )
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        Text(
                            text = "激活码",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Text(
                            text = activation.code,
                            fontSize = 48.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary,
                            letterSpacing = 8.sp
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(32.dp))
                
                // 绑定状态卡片
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = when (bindingStatus) {
                            BindingStatus.Checking -> MaterialTheme.colorScheme.surfaceVariant
                            BindingStatus.WaitingForBinding -> MaterialTheme.colorScheme.secondaryContainer
                            BindingStatus.Bound -> Color(0xFF4CAF50).copy(alpha = 0.1f)
                            BindingStatus.CheckFailed -> MaterialTheme.colorScheme.errorContainer
                        }
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        StatusIcon(bindingStatus)
                        
                        Spacer(modifier = Modifier.height(12.dp))
                        
                        Text(
                            text = getStatusTitle(bindingStatus),
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Medium,
                            color = getStatusColor(bindingStatus)
                        )
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Text(
                            text = getStatusDescription(bindingStatus),
                            fontSize = 14.sp,
                            textAlign = TextAlign.Center,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // 操作指南
                if (bindingStatus == BindingStatus.WaitingForBinding) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.tertiaryContainer
                        )
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp)
                        ) {
                            Text(
                                text = "📋 绑定步骤",
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onTertiaryContainer
                            )
                            
                            Spacer(modifier = Modifier.height(12.dp))
                            
                            InstructionStep(
                                stepNumber = "1",
                                description = "在电脑浏览器中打开管理面板"
                            )
                            
                            InstructionStep(
                                stepNumber = "2",
                                description = "点击\"设备管理\"页面的\"新增\"按钮"
                            )
                            
                            InstructionStep(
                                stepNumber = "3",
                                description = "输入上方显示的6位激活码：${activation.code}"
                            )
                            
                            InstructionStep(
                                stepNumber = "4",
                                description = "完成绑定，应用将自动跳转到聊天页面"
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                }
                
                // 手动检查按钮
                if (bindingStatus == BindingStatus.CheckFailed) {
                    Button(
                        onClick = { viewModel.retryBindingCheck() },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("重试检查")
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                }
                
                // 手动检查按钮
                OutlinedButton(
                    onClick = { viewModel.manualCheckBinding() },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = bindingStatus != BindingStatus.Checking
                ) {
                    if (bindingStatus == BindingStatus.Checking) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("手动检查绑定状态")
                }
            }
            
            // 底部帮助信息
            Text(
                text = activation.message,
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = 16.dp)
            )
        }
    }
}

@Composable
private fun StatusIcon(status: BindingStatus) {
    val (icon, color) = when (status) {
        BindingStatus.Checking -> Icons.Default.Sync to MaterialTheme.colorScheme.primary
        BindingStatus.WaitingForBinding -> Icons.Default.HourglassEmpty to MaterialTheme.colorScheme.secondary
        BindingStatus.Bound -> Icons.Default.CheckCircle to Color(0xFF4CAF50)
        BindingStatus.CheckFailed -> Icons.Default.Error to MaterialTheme.colorScheme.error
    }
    
    Icon(
        imageVector = icon,
        contentDescription = null,
        tint = color,
        modifier = Modifier.size(32.dp)
    )
}

@Composable
private fun getStatusColor(status: BindingStatus): androidx.compose.ui.graphics.Color {
    return when (status) {
        BindingStatus.Checking -> MaterialTheme.colorScheme.primary
        BindingStatus.WaitingForBinding -> MaterialTheme.colorScheme.secondary
        BindingStatus.Bound -> Color(0xFF4CAF50)
        BindingStatus.CheckFailed -> MaterialTheme.colorScheme.error
    }
}

private fun getStatusTitle(status: BindingStatus): String {
    return when (status) {
        BindingStatus.Checking -> "正在检查绑定状态..."
        BindingStatus.WaitingForBinding -> "等待设备绑定"
        BindingStatus.Bound -> "绑定成功！"
        BindingStatus.CheckFailed -> "检查失败"
    }
}

private fun getStatusDescription(status: BindingStatus): String {
    return when (status) {
        BindingStatus.Checking -> "系统正在验证设备绑定状态，请稍候..."
        BindingStatus.WaitingForBinding -> "请按照下方步骤在管理面板中完成设备绑定"
        BindingStatus.Bound -> "设备已成功绑定，即将跳转到聊天页面开始语音交互"
        BindingStatus.CheckFailed -> "无法连接到服务器检查绑定状态，请检查网络连接"
    }
}

@Composable
private fun InstructionStep(
    stepNumber: String,
    description: String
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            modifier = Modifier.size(24.dp),
            shape = CircleShape,
            color = MaterialTheme.colorScheme.primary
        ) {
            Box(
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = stepNumber,
                    color = MaterialTheme.colorScheme.onPrimary,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Text(
            text = description,
            fontSize = 13.sp,
            modifier = Modifier.weight(1f),
            color = MaterialTheme.colorScheme.onTertiaryContainer
        )
    }
}


