# OTA请求格式修复总结

## 🐛 问题描述

用户反馈新版APK第一次绑定时出现错误："绑定出错：服务器响应格式无效"。正确的行为应该是产生一个激活码用于服务绑定，但没有发生。

## 🔍 问题分析

通过分析发现，问题出现在OTA请求的字段命名格式上：

### ❌ 错误格式（驼峰命名）
```json
{
  "application": {
    "version": "1.0.0",
    "name": "xiaozhi-android",
    "compile_time": "2025-05-27T00:00:00Z"
  },
  "macAddress": "XX:XX:XX:XX:XX:XX",      // 驼峰命名 - 错误
  "chipModelName": "android",             // 驼峰命名 - 错误
  "board": {
    "type": "android",
    "manufacturer": "Samsung",
    "model": "Galaxy S21"
  },
  "uuid": "uuid-string",
  "build_time": 1234567890
}
```

### ✅ 正确格式（下划线命名）
```json
{
  "application": {
    "version": "1.0.0"
  },
  "mac_address": "XX:XX:XX:XX:XX:XX",     // 下划线命名 - 正确
  "chip_model_name": "android",           // 下划线命名 - 正确
  "board": {
    "type": "android"
  }
}
```

## 🔧 修复方案

### 修改文件
- `xiaozhi-android/app/src/main/java/info/dourok/voicebot/binding/BindingStatusChecker.kt`

### 具体修改
1. **字段命名修正**：
   - `macAddress` → `mac_address`
   - `chipModelName` → `chip_model_name`

2. **请求体简化**：
   - 移除不必要的字段（`name`, `compile_time`, `manufacturer`, `model`, `uuid`, `build_time`）
   - 保留核心必需字段

3. **代码修改**：
```kotlin
// 修改前
put("macAddress", deviceId)
put("chipModelName", "android")

// 修改后  
put("mac_address", deviceId)
put("chip_model_name", "android")
```

## ✅ 验证结果

### 测试执行
- **测试时间**: 2025-05-27 00:50
- **测试设备ID**: `92:EE:E9:01:7E:7B`
- **测试结果**: ✅ 成功

### 服务器响应
```json
{
  "server_time": {
    "timestamp": 1748278294361,
    "timeZone": "Asia/Shanghai",
    "timezone_offset": 480
  },
  "activation": {
    "code": "040409",
    "message": "http://47.122.144.73:8002/#/home\n040409",
    "challenge": "92:EE:E9:01:7E:7B"
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

### 关键成果
- ✅ **成功获取激活码**: `040409`
- ✅ **服务器响应完整**: 包含activation、websocket、firmware等所有字段
- ✅ **请求格式正确**: 服务器正常解析并返回预期响应

## 📱 新APK信息

### 文件位置
```
/Users/xzmx/Downloads/my-project/xiaozhi-android/app/build/outputs/apk/debug/app-debug.apk
```

### 文件信息
- **大小**: 18MB
- **构建时间**: 2025-05-27 00:50
- **修复内容**: OTA请求格式修正

## 🎯 预期效果

使用修复后的APK，用户应该能够：

1. **正常获取激活码**: 应用启动时自动获取6位数字激活码
2. **显示绑定对话框**: 智能绑定对话框正常显示激活码和操作指引
3. **完成设备绑定**: 用户可以使用激活码在管理面板完成设备绑定
4. **自动检测绑定**: 绑定完成后应用自动检测并跳转到聊天界面

## 🔍 技术细节

### 根本原因
服务器端期望的是下划线命名格式（snake_case），而Android应用发送的是驼峰命名格式（camelCase），导致服务器无法正确解析请求字段。

### 修复原理
通过将请求字段名从驼峰命名改为下划线命名，确保与服务器端的字段解析逻辑一致。

### 兼容性
修复后的格式与之前成功的测试脚本格式完全一致，确保了与服务器的完全兼容性。

## 📋 后续建议

1. **测试验证**: 建议用户安装新APK并测试绑定流程
2. **错误监控**: 继续监控绑定过程中的其他潜在问题
3. **文档更新**: 更新API文档明确字段命名规范
4. **代码规范**: 建立统一的字段命名规范避免类似问题

---
**修复完成时间**: 2025-05-27 00:50  
**修复状态**: ✅ 已验证成功 