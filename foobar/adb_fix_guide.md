# 🔧 ADB多设备问题修正指南

## 📊 当前问题分析

您遇到的错误：`adb: more than one device/emulator`

这意味着有多个Android设备或模拟器连接到您的电脑。

## 🚀 解决方案

### 方法1：在Terminal中手动执行（推荐）

1. **打开Terminal应用**（不是PowerShell）
2. **查看连接的设备**：
   ```bash
   adb devices
   ```

3. **选择目标设备并清除数据**：
   ```bash
   # 替换 DEVICE_ID 为实际设备ID
   adb -s DEVICE_ID shell pm clear info.dourok.voicebot
   ```

### 方法2：使用Android Studio

1. **打开Android Studio**
2. **在菜单中选择 Tools → Device Manager**
3. **找到目标设备**
4. **在Device Manager中右键设备 → Wipe Data**

### 方法3：手动清除（设备上操作）

1. **在Android设备上打开"设置"**
2. **进入"应用管理"或"应用"**
3. **找到"VoiceBot"应用**
4. **点击"存储"**
5. **点击"清除数据"**

## 🎯 完整验证流程

### 步骤1：清除应用数据
使用上述任一方法清除VoiceBot的应用数据

### 步骤2：验证设备绑定状态
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: 00:11:22:33:44:55" \
  -H "Client-Id: android-app" \
  -d '{
    "mac_address": "00:11:22:33:44:55",
    "application": {"version": "1.0.0"},
    "board": {"type": "android"},
    "chip_model_name": "android"
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

**期望结果**：
- 如果返回`activation`字段：需要绑定设备
- 如果返回`websocket`字段：设备已绑定，可以测试

### 步骤3：设备绑定（如果需要）
1. 访问：http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30
2. 输入激活码
3. 完成绑定

### 步骤4：重新编译和测试
1. **重新编译**Android项目
2. **安装到设备**
3. **启动应用**
4. **测试STT功能**

## 🔍 验证成功标志

### 预期日志输出：
```
Current Device-Id: 00:11:22:33:44:55
WebSocket connected successfully
```

### 预期应用行为：
- ✅ 语音识别按钮可用
- ✅ 说话后显示转录文字
- ✅ 没有"设备绑定"错误提示

## ⚡ 快速命令备忘

```bash
# 查看连接的设备
adb devices

# 清除指定设备的应用数据
adb -s YOUR_DEVICE_ID shell pm clear info.dourok.voicebot

# 测试设备绑定状态
python3 test_your_device_id.py

# 查看应用日志（测试时）
adb -s YOUR_DEVICE_ID logcat | grep -E "(DeviceInfo|WS|ChatViewModel)"
```

## 🚨 重要提醒

1. **必须清除应用数据**：这确保应用使用新的固定设备ID `00:11:22:33:44:55`
2. **必须重新编译**：确保代码修改生效
3. **检查设备绑定**：未绑定的设备STT功能会被阻止

---
**如果以上方法都不行，请在Terminal中运行 `python3 test_your_device_id.py` 来验证设备绑定状态。** 