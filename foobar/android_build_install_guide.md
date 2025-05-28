# Android 小智语音应用编译和安装指南

## 编译结果
✅ **编译成功！** APK已生成在以下位置：
```
xiaozhi-android/app/build/outputs/apk/debug/app-debug.apk
```

文件大小：24MB

## 安装方法

### 方法1：使用ADB安装（推荐）

#### 准备工作
1. 确保Android设备已开启USB调试模式
2. 使用USB线连接设备到电脑
3. 在电脑上安装Android SDK Platform Tools（包含adb命令）

#### 安装命令
```bash
# 进入项目目录
cd /Users/xzmx/Downloads/my-project/xiaozhi-android

# 检查连接的设备
adb devices

# 安装到指定设备（如果有多个设备）
adb -s [设备ID] install app/build/outputs/apk/debug/app-debug.apk

# 或者安装到唯一的设备
adb install app/build/outputs/apk/debug/app-debug.apk
```

#### 实际示例
从检测结果看，您有以下设备：
- 物理设备：SOZ95PIFVS5H6PIZ
- 模拟器：emulator-5554

安装命令：
```bash
# 安装到物理设备
adb -s SOZ95PIFVS5H6PIZ install app/build/outputs/apk/debug/app-debug.apk

# 安装到模拟器
adb -s emulator-5554 install app/build/outputs/apk/debug/app-debug.apk
```

### 方法2：直接传输安装
1. 将APK文件复制到Android设备存储空间
2. 在设备上启用"未知来源"应用安装权限
3. 使用文件管理器打开APK文件进行安装

## 应用功能特点

### ESP32完全兼容模式
- ✅ 启动后自动进入语音监听状态
- ✅ 支持TTS播放期间的语音打断
- ✅ 无需手动按钮操作，完全自动化
- ✅ 与ESP32硬件设备行为完全一致

### 性能优化
- ✅ 解决了语音交互卡顿问题
- ✅ 优化了内存管理和音频缓冲
- ✅ 支持长时间稳定对话

### 技术特性
- WebSocket实时通信
- Opus音频编解码
- VAD语音活动检测
- TTS文本转语音
- STT语音转文本

## 使用方法
1. 安装APK到Android设备
2. 打开"小智语音助手"应用
3. 按照激活引导完成设备绑定
4. 享受自动化语音交互体验

## 故障排除

### 安装失败
- 确保设备已开启USB调试
- 检查设备存储空间是否充足
- 尝试先卸载旧版本（如果存在）

### 运行异常
- 确保网络连接正常
- 检查麦克风和音频权限
- 查看应用日志获取详细信息

## 技术支持
如需技术支持或遇到问题，请提供：
- 设备型号和Android版本
- 错误日志信息
- 操作步骤描述

编译日期：$(date +"%Y-%m-%d %H:%M:%S")
APK版本：Debug v1.0 