# 🎯 小智Android应用STT问题最终解决方案

## 问题根本原因
通过深入分析三个模块的源码，确认**您的Android应用STT不工作的根本原因是：服务器端强制要求设备绑定，未绑定设备无法使用STT功能。**

## 完整绑定流程分析

### 1. 设备绑定验证链路
```
Android应用 → WebSocket连接 → xiaozhi-server → manager-api → 设备绑定检查
```

### 2. 关键代码位置

#### OTA接口验证 (manager-api)
**文件：** `OTAController.java` 第51-57行
```java
// 设备Id和Mac地址应是一致的, 并且必须需要application字段
if (!deviceId.equals(macAddress) || !macAddressValid || deviceReportReqDTO.getApplication() == null) {
    return createResponse(DeviceReportRespDTO.createError("Invalid OTA request"));
}
```

#### WebSocket连接验证 (xiaozhi-server)
**文件：** `connection.py` 第336-353行
```python
try:
    private_config = get_private_config_from_api(...)
except DeviceNotFoundException as e:
    self.need_bind = True  # 设备未找到，需要绑定
except DeviceBindException as e:
    self.need_bind = True  # 设备存在但未绑定
    self.bind_code = e.bind_code
```

#### STT阻断机制 (xiaozhi-server)
**文件：** `receiveAudioHandle.py` 第55-57行
```python
async def startToChat(conn, text):
    if conn.need_bind:
        await check_bind_device(conn)  # 阻断STT，播放绑定提示
        return
```

## 正确的OTA请求格式

基于源码分析，正确的OTA请求应该是：

### 方法1：使用驼峰命名
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

### 方法2：使用下划线命名（JsonProperty）
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: aa:bb:cc:dd:ee:ff" \
  -H "Client-Id: android-test" \
  -d '{
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "application": {
      "version": "1.0.0"
    },
    "board": {
      "type": "android"
    },
    "chip_model_name": "android"
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

## 期望的成功响应

### 未绑定设备（需要激活）
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

### 已绑定设备
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
  }
}
```

## 手动绑定步骤

### 第1步：获取激活码
使用上述curl命令之一，获取6位数字激活码。

### 第2步：管理面板绑定
1. 访问：http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30
2. 在设备绑定界面输入6位激活码
3. 完成绑定

### 第3步：验证STT功能
重新运行Android应用，测试STT功能是否恢复正常。

## 长期解决方案

### Android应用集成OTA客户端
在Android应用中实现完整的设备绑定流程：

1. **OTA客户端集成** (`OTAClient.kt`)
2. **设备激活界面** (`DeviceActivationScreen.kt`)
3. **绑定状态检查**
4. **用户引导流程**

### 实现代码已准备
在`foobar/prepare_plan_a.md`中已提供完整的实现代码，包括：
- OTA客户端
- 激活界面
- Repository修改
- 错误处理

## 调试信息

### Redis缓存键格式
- 主数据键：`ota:activation:data:aa_bb_cc_dd_ee_ff`
- 激活码键：`ota:activation:code:123456`

### 常见错误原因
1. `Device-Id`头部与`macAddress`不一致
2. `application`字段缺失
3. MAC地址格式不正确（需要符合正则：`^([0-9A-Za-z]{2}[:-]){5}([0-9A-Za-z]{2})$`）
4. 请求体JSON格式错误

## 下一步行动

1. **立即验证**：使用上述curl命令手动测试OTA接口
2. **管理面板绑定**：获取激活码后在管理面板完成绑定
3. **验证STT**：重新测试Android应用的STT功能
4. **长期实施**：集成完整的设备绑定流程到Android应用

---
**关键提醒：确保Device-Id头部和macAddress字段完全一致，这是验证失败的主要原因！** 