# 🔬 全面STT问题诊断分析

## 📊 当前状态确认

### ✅ 客户端修改成功验证
- **协议版本**: 已从1改为3 ✅
- **帧长度**: 已从60ms改为20ms ✅
- **音频发送**: 正常，已发送数百帧 ✅
- **WebSocket连接**: 正常 ✅

### ❌ 服务器响应异常
- **服务器仍返回旧参数**: `version:1, frame_duration:60`
- **无STT响应**: 没有任何`{"type":"stt"}`消息
- **协议不匹配**: 客户端发送version 3，服务器回应version 1

## 🎯 扩大诊断范围

### 1. 服务器端配置问题

**可能原因**:
- 服务器硬编码了protocol version 1
- 服务器不支持动态音频参数协商
- WebSocket端点没有启用STT功能
- 服务器期望不同的认证方式

### 2. URL端点问题

**当前URL**: `ws://47.122.144.73:8000/xiaozhi/v1/`

**可能的问题**:
```bash
# 检查服务器是否真的在运行
curl -I http://47.122.144.73:8000/
curl -I http://47.122.144.73:8000/xiaozhi/v1/

# 检查是否有其他端点
curl http://47.122.144.73:8000/xiaozhi/v1/health
curl http://47.122.144.73:8000/xiaozhi/v1/info
```

### 3. 认证Token问题

**当前Token**: `"test-token"`

这可能是无效的测试token，导致：
- 服务器接受连接但不提供STT服务
- 服务器降级到基础功能模式
- 权限不足访问STT功能

### 4. 服务器架构差异

**推测的服务器架构**:
```
MQTT架构: MQTT Broker → UDP音频服务器 → STT引擎
WebSocket架构: WebSocket服务器 → ??? → STT引擎(可能缺失)
```

**可能性**:
- WebSocket服务器是MQTT服务器的简化版本
- WebSocket端点不包含完整的STT处理链
- 需要额外的配置或端点激活STT功能

## 🛠️ 综合诊断方案

### 诊断1: 服务器能力检查

创建一个简单的WebSocket客户端测试服务器能力：

```javascript
// 浏览器控制台测试
const ws = new WebSocket('ws://47.122.144.73:8000/xiaozhi/v1/');
ws.onopen = () => {
    console.log('✅ 连接成功');
    // 测试不同的hello消息
    ws.send('{"type":"hello","version":1,"transport":"websocket"}');
};
ws.onmessage = (e) => {
    console.log('📨 服务器响应:', e.data);
    try {
        const data = JSON.parse(e.data);
        if(data.type === 'hello') {
            // 发送测试音频数据
            ws.send('{"type":"test","message":"STT功能测试"}');
        }
    } catch(err) {
        console.log('解析错误:', err);
    }
};
ws.onerror = (e) => console.log('❌ 连接错误:', e);
ws.onclose = (e) => console.log('🔌 连接关闭:', e.code, e.reason);
```

### 诊断2: 不同认证方式测试

修改WebSocket协议尝试不同的认证：

```kotlin
// 在WebsocketProtocol.kt中尝试
val request = Request.Builder()
    .url(url)
    .addHeader("Authorization", "Bearer real-token")  // 尝试真实token
    // .addHeader("X-API-Key", "your-api-key")       // 或API Key
    // .addHeader("Token", "your-token")             // 或直接Token
    .build()
```

### 诊断3: 不同URL端点测试

尝试可能的不同端点：

```kotlin
// 可能的端点变化
val alternativeUrls = listOf(
    "ws://47.122.144.73:8000/xiaozhi/v1/",          // 当前
    "ws://47.122.144.73:8000/xiaozhi/v1/stt",       // STT专用端点
    "ws://47.122.144.73:8000/xiaozhi/v1/audio",     // 音频端点
    "ws://47.122.144.73:8000/xiaozhi/",             // 简化版本
    "ws://47.122.144.73:8000/stt",                  // 直接STT
    "ws://47.122.144.73:8001/xiaozhi/v1/",          // 不同端口
)
```

### 诊断4: 增强消息监控

捕获所有可能的服务器响应：

```kotlin
override fun onMessage(webSocket: WebSocket, text: String) {
    Log.i(TAG, "=== 服务器完整响应 START ===")
    Log.i(TAG, "原始消息: $text")
    Log.i(TAG, "消息长度: ${text.length}")
    Log.i(TAG, "时间戳: ${System.currentTimeMillis()}")
    
    // 尝试解析JSON
    try {
        val json = JSONObject(text)
        Log.i(TAG, "JSON类型: ${json.optString("type", "未知")}")
        Log.i(TAG, "JSON内容: ${json.toString(2)}")
        
        // 检查所有可能的STT相关字段
        val possibleFields = listOf("stt", "text", "transcript", "recognition", "speech")
        possibleFields.forEach { field ->
            if (json.has(field)) {
                Log.i(TAG, "🎯 发现可能的STT字段: $field = ${json.get(field)}")
            }
        }
    } catch (e: Exception) {
        Log.w(TAG, "JSON解析失败，可能是纯文本响应: ${e.message}")
    }
    
    Log.i(TAG, "=== 服务器完整响应 END ===")
    
    // 现有处理逻辑...
}
```

### 诊断5: 网络层面检查

使用网络工具检查实际的数据流：

```bash
# 使用tcpdump捕获网络包（如果有权限）
sudo tcpdump -i any host 47.122.144.73 and port 8000

# 或使用nslookup检查域名解析
nslookup 47.122.144.73

# 检查端口开放情况
nc -zv 47.122.144.73 8000
```

## 🚨 最可能的问题假设

基于分析，我认为最可能的问题是：

### 假设1: 服务器STT功能未启用
- WebSocket服务器只是一个简化的协议转换器
- 真正的STT功能可能在不同的端点或需要特殊激活

### 假设2: 认证权限不足
- "test-token"可能只允许基础连接
- STT功能需要有效的认证凭据

### 假设3: 服务器配置错误
- 服务器端STT服务可能没有正确配置
- 需要服务器管理员检查后端日志

## 🎯 立即行动计划

1. **增强客户端日志**: 捕获所有服务器响应
2. **测试不同认证**: 尝试获取真实的认证token
3. **联系服务器管理员**: 检查服务器端STT服务状态
4. **尝试替代端点**: 测试不同的URL路径
5. **对比MQTT配置**: 检查MQTT模式下的实际配置参数

**结论**: 问题很可能在服务器端，而不是客户端协议参数。需要从服务器架构层面进行诊断。 