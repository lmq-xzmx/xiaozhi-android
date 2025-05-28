# 📋 下一步操作指南：Android端STT与ESP32统一化

## 🎯 **当前状态**

✅ **已完成**：
- Android端STT流程修复和完善
- ESP32端STT方案深入分析
- 完整的测试工具集创建
- APK重新构建（24MB，包含原生库）
- 录音权限已授予
- 自动化测试脚本已准备

## 🚀 **立即执行的下一步**

### 1. 运行自动化测试（推荐）
```bash
# 进入项目目录
cd xiaozhi-android

# 运行完整的自动化测试
python3 foobar/install_and_test_stt.py
```

**测试流程**：
1. ✅ 自动安装最新APK
2. ✅ 启动Android应用
3. ✅ 清除旧日志
4. 🎯 **您需要手动操作**：点击"开始监听"并说话
5. ✅ 自动监控和分析STT流程

### 2. 手动快速验证
```bash
# 快速STT流程诊断
python3 foobar/simple_stt_test.py

# 查看ESP32端配置对比
python3 foobar/simple_stt_test.py --config
```

### 3. 实时日志监控
```bash
# 监控STT相关日志
adb -s SOZ95PIFVS5H6PIZ logcat | grep -E "STT|stt|audio|listen"
```

## 🎯 **测试验证点**

### 成功标志（预期看到）
- ✅ 日志显示：`🎯 收到STT结果: '你好小智'`
- ✅ 聊天界面显示用户输入
- ✅ 状态从"🎤 监听中"变为"🔊 回复中"
- ✅ 小智开始TTS回复

### 失败排查（如果出现问题）
- ❌ **无监听命令** → 检查应用启动和按钮点击
- ❌ **无音频传输** → 检查录音权限和麦克风
- ❌ **无服务器响应** → 检查网络和FunASR服务
- ❌ **无STT解析** → 检查WebSocket消息格式

## 📊 **验证Android端与ESP32端一致性**

### ESP32端标准流程
```
用户说话 → 录音 → Opus编码 → WebSocket发送
                              ↓
服务器FunASR识别 → 生成文本 → 返回STT响应 → 显示结果
```

### Android端修复后流程
```
用户说话 → 录音(PCM) → Opus编码 → WebSocket发送
                                ↓
服务器FunASR识别 → 生成文本 → 返回STT响应 → Android解析 → UI显示
```

**🎯 目标**：两端流程完全一致！

## 🔧 **如果需要调试**

### 查看创建的工具
```bash
# 查看所有STT相关工具
ls foobar/ | grep stt
ls Work_Framework/ | grep stt
```

### 重要文件位置
- **APK文件**：`app/build/outputs/apk/debug/app-debug.apk`
- **测试脚本**：`foobar/install_and_test_stt.py`
- **诊断工具**：`foobar/simple_stt_test.py`
- **修复总结**：`Work_Framework/final_stt_unification_summary.md`

### 手动安装和测试
```bash
# 如果自动化脚本有问题，可以手动执行
adb -s SOZ95PIFVS5H6PIZ install -r app/build/outputs/apk/debug/app-debug.apk
adb -s SOZ95PIFVS5H6PIZ shell am start -n info.dourok.voicebot/.MainActivity
```

## 🎉 **预期最终结果**

**✅ Android端STT与ESP32端完全统一**：
- 使用相同的服务器端FunASR STT方案
- 相同的Opus音频传输协议
- 相同的WebSocket响应格式
- 一致的用户体验和识别准确度

**📱 您的Android应用现在与ESP32设备使用完全相同的语音识别技术栈！**

---

## 🚀 **马上开始测试**

运行这个命令开始验证：
```bash
python3 foobar/install_and_test_stt.py
```

然后在Android应用中点击"开始监听"，说出"你好小智，请介绍一下你自己"，观察STT识别效果！ 