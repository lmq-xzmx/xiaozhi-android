# 🔍 小智WebSocket绑定规则完整分析

## 核心问题诊断
**您的Android应用STT不工作的根本原因是：服务器端强制要求设备绑定，未绑定设备无法使用STT功能。**

## 完整绑定流程

### 1. 设备启动阶段
```
Android应用启动 → 调用OTA接口(/xiaozhi/ota/) → 检查设备是否已绑定
```

### 2. OTA接口处理逻辑 (manager-api)
**文件位置：** `DeviceServiceImpl.java` 的 `checkDeviceActive()` 方法

```java
// 检查设备是否存在于数据库
DeviceEntity deviceById = getDeviceByMacAddress(macAddress);

if (deviceById != null) {
    // 设备已绑定 - 返回WebSocket配置
    response.setWebsocket(websocket); // 包含ws://URL
} else {
    // 设备未绑定 - 生成激活码
    DeviceReportRespDTO.Activation code = buildActivation(macAddress, deviceReport);
    response.setActivation(code); // 包含6位数字激活码
}
```

### 3. 激活码生成机制
**文件位置：** `DeviceServiceImpl.java` 的 `buildActivation()` 方法

```java
// 生成6位随机数字激活码
String newCode = RandomUtil.randomNumbers(6);

// 数据存储在Redis中
Map<String, Object> dataMap = new HashMap<>();
dataMap.put("id", deviceId);
dataMap.put("mac_address", deviceId);
dataMap.put("board", deviceReport.getBoard().getType());
dataMap.put("app_version", deviceReport.getApplication().getVersion());
dataMap.put("activation_code", newCode);

// 主数据键
String dataKey = "ota:activation:data:" + deviceId.replace(":", "_").toLowerCase();
redisUtils.set(dataKey, dataMap);

// 反查激活码键
String codeKey = "ota:activation:code:" + newCode;
redisUtils.set(codeKey, deviceId);
```

### 4. WebSocket连接验证 (xiaozhi-server)
**文件位置：** `connection.py` 的 `_initialize_private_config()` 方法

```python
try:
    # 调用manager-api获取设备配置
    private_config = get_private_config_from_api(
        self.config,
        self.headers.get("device-id"),
        self.headers.get("client-id")
    )
except DeviceNotFoundException as e:
    self.need_bind = True  # 设备未找到，需要绑定
except DeviceBindException as e:
    self.need_bind = True  # 设备存在但未绑定
    self.bind_code = e.bind_code  # 获取绑定码
```

### 5. STT阻断机制
**文件位置：** `receiveAudioHandle.py` 的 `startToChat()` 方法

```python
async def startToChat(conn, text):
    if conn.need_bind:
        await check_bind_device(conn)  # 阻断STT，播放绑定提示
        return
    # 只有绑定后才能继续STT处理...
```

### 6. 设备绑定API
**文件位置：** `DeviceServiceImpl.java` 的 `deviceActivation()` 方法

```java
public Boolean deviceActivation(String agentId, String activationCode) {
    // 验证激活码
    String deviceKey = "ota:activation:code:" + activationCode;
    Object cacheDeviceId = redisUtils.get(deviceKey);
    
    if (cacheDeviceId == null) {
        throw new RenException("激活码错误");
    }
    
    // 创建设备记录
    DeviceEntity deviceEntity = new DeviceEntity();
    deviceEntity.setId(deviceId);
    deviceEntity.setAgentId(agentId);
    deviceEntity.setUserId(user.getId());
    deviceDao.insert(deviceEntity);
    
    // 清理Redis缓存
    redisUtils.delete(cacheDeviceKey);
    redisUtils.delete(deviceKey);
}
```

## 正确的OTA请求格式

根据`DeviceServiceImpl.java`分析，正确的OTA请求应该是：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: aa:bb:cc:dd:ee:ff" \
  -H "Client-Id: android-test" \
  -d '{
    "macAddress": "aa:bb:cc:dd:ee:ff",
    "application": {
      "version": "1.0.0"
    },
    "board": {
      "type": "android"
    },
    "chipModelName": "android"
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

**期望响应（未绑定设备）：**
```json
{
  "server_time": {
    "timestamp": 1699999999999,
    "timezone_offset": 480
  },
  "firmware": {
    "version": "1.0.0",
    "url": ""
  },
  "websocket": {
    "url": "ws://47.122.144.73:8000/xiaozhi/v1/"
  },
  "activation": {
    "code": "123456",
    "message": "http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30\n123456",
    "challenge": "aa:bb:cc:dd:ee:ff"
  }
}
```

## 管理面板绑定流程

1. **获取激活码**：通过OTA接口获得6位数字激活码
2. **访问管理面板**：http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30
3. **输入激活码**：在设备管理页面输入6位激活码
4. **完成绑定**：系统调用`deviceActivation`API完成绑定

## 解决方案

### 快速验证方案（当前推荐）
1. 使用正确的OTA请求格式获取激活码
2. 在管理面板手动绑定设备
3. 重新连接WebSocket验证STT功能

### 完整解决方案（后续实施）
在Android应用中实现完整的设备绑定流程：
- OTA客户端集成
- 激活码显示界面
- 绑定状态检查
- 用户引导流程

---
**关键发现：您的OTA请求返回`{"error":"Invalid OTA request"}`说明请求格式有误，需要按照上述正确格式重新尝试。** 