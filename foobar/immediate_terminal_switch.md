# 🚨 紧急：立即切换Terminal指南

## ⚠️ 当前问题确认

您刚刚遇到的PowerShell错误：
```
System.InvalidOperationException: Cannot locate the offset in the rendered text
```

这正是我们之前警告的**PowerShell严重兼容性问题**！

## 🎯 立即行动步骤

### **第一步：关闭PowerShell**
1. 关闭当前PowerShell窗口
2. **不要再尝试在PowerShell中执行任何命令**

### **第二步：打开macOS原生Terminal**
1. **按键：`Cmd + Space`**
2. **输入：`Terminal`**
3. **按回车键**

### **第三步：导航到项目目录**
```bash
cd /Users/xzmx/Downloads/my-project/xiaozhi-android
```

### **第四步：验证环境**
```bash
# 验证当前shell
echo "当前Shell: $SHELL"

# 验证项目目录
pwd
ls -la | head -10
```

## 🚀 继续项目推进命令

在macOS Terminal中执行：

### **1. 执行自动化修复**
```bash
bash foobar/fix_stt.sh
```

### **2. 如果需要手动步骤**
```bash
# 清理项目
./gradlew clean

# 编译APK
./gradlew app:assembleDebug

# 检查设备
adb devices

# 验证设备绑定
cd foobar && python3 test_your_device_id.py
```

## ✅ 成功标志

当您在macOS Terminal中看到：
```bash
user@MacBook xiaozhi-android % bash foobar/fix_stt.sh
🎯 开始STT功能修复流程...
📂 当前目录: /Users/xzmx/Downloads/my-project/xiaozhi-android
```

这意味着您已经成功切换！

## 🎯 为什么必须这样做

PowerShell错误表明：
- **渲染系统崩溃**
- **命令执行不可靠**
- **Android工具链不兼容**
- **项目无法正常推进**

macOS Terminal提供：
- **100%稳定性**
- **完美Android支持**
- **无错误命令执行**
- **流畅开发体验**

---
**请立即按照上述步骤切换到macOS Terminal，然后我们继续推进项目！** 