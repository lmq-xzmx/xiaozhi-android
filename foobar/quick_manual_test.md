# 🚀 方案B：手动快速验证指南

由于终端环境问题，这里提供手动验证步骤：

## 第一步：获取Android设备的真实MAC地址

### 方法1：通过Android应用获取
在Android应用的`DeviceInfo.kt`中，确认`mac_address`字段的值。
如果是模拟值，可以临时使用：`"aa:bb:cc:dd:ee:ff"`

### 方法2：生成测试MAC地址
使用格式：`"02:42:ac:11:00:XX"` (XX为任意十六进制数字)

## 第二步：测试OTA接口

### 使用Postman或curl命令行测试

**请求URL：** `http://47.122.144.73:8002/xiaozhi/ota/`

**请求方法：** POST

**请求头：**
```
Content-Type: application/json
Device-Id: aa:bb:cc:dd:ee:ff
Client-Id: android-test-uuid
```

**请求体：**
```json
{
  "macAddress": "aa:bb:cc:dd:ee:ff",
  "application": {
    "version": "1.0.0"
  },
  "board": {
    "type": "android"
  },
  "chipModelName": "android"
}
```

## 第三步：根据响应执行操作

### 响应A：需要激活（预期响应）
```json
{
  "activation": {
    "code": "123456",
    "message": "http://47.122.144.73:8002\n123456",
    "challenge": "aa:bb:cc:dd:ee:ff"
  },
  "websocket": null,
  "server_time": {...}
}
```

**下一步操作：**
1. 记录激活码：`123456`
2. 访问管理面板：http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30
3. 使用管理员账号登录
4. 点击"新增"按钮
5. 输入激活码`123456`
6. 完成绑定

### 响应B：已绑定设备
```json
{
  "activation": null,
  "websocket": {
    "url": "ws://47.122.144.73:8000/xiaozhi/v1/"
  },
  "server_time": {...}
}
```

**说明：** 设备已绑定，可以直接使用WebSocket URL

### 响应C：错误响应
```json
{
  "error": "Invalid OTA request"
}
```

**解决方案：**
1. 检查MAC地址格式（必须符合`XX:XX:XX:XX:XX:XX`格式）
2. 确保Device-Id头和macAddress字段值完全一致
3. 尝试不同的MAC地址格式

## 第四步：验证绑定结果

### 完成绑定后，重新测试OTA接口
使用相同的请求参数再次调用OTA接口，应该返回包含`websocket`字段的响应。

### 修改Android应用配置
在Android应用中：
1. 使用从OTA接口获取的实际WebSocket URL
2. 使用相同的设备ID（MAC地址）
3. 测试STT功能是否恢复

## 方案B失败时的备选方案

### 备选1：直接在管理面板添加设备
1. 访问管理面板
2. 在设备管理页面直接添加设备
3. 使用Android设备的MAC地址作为激活码

### 备选2：联系服务器管理员
如果OTA接口持续返回错误，可能需要：
1. 确认OTA接口的正确使用方法
2. 检查服务器配置
3. 临时在数据库中手动添加设备记录

## 成功标准

✅ **验证成功的标志：**
1. OTA接口返回包含`activation`的JSON响应
2. 能够在管理面板成功绑定设备
3. 绑定后OTA接口返回`websocket` URL
4. Android应用STT功能恢复正常

## 如果方案B失败

如果以上步骤无法解决问题，我们将转向**方案A：完整设备绑定实现**，包括：
1. 在Android应用中集成OTA客户端
2. 实现设备激活UI界面
3. 完善设备绑定流程
4. 添加错误处理和重试机制

---

**下一步：** 请先尝试手动执行上述OTA接口测试，并告知结果。 