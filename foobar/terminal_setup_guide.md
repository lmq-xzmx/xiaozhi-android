# 🚀 macOS Android开发Terminal设置指南

## 🎯 推荐的Terminal配置

### **第一选择：macOS原生Terminal**
```bash
# 打开方式：
# 1. Cmd+Space → 输入 "Terminal"
# 2. 或：应用程序 → 实用工具 → Terminal
```

### **第二选择：iTerm2**（推荐）
```bash
# 安装iTerm2（更强大的Terminal）
brew install --cask iterm2
```

## 🔧 Terminal配置优化

### **1. 设置默认Shell为zsh**
```bash
# 检查当前shell
echo $SHELL

# 如果不是zsh，设置为默认
chsh -s /bin/zsh
```

### **2. 配置Android开发环境变量**
```bash
# 编辑.zshrc文件
nano ~/.zshrc

# 添加以下内容：
export ANDROID_HOME=/Users/$USER/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/tools/bin

# 重新加载配置
source ~/.zshrc
```

### **3. 验证环境配置**
```bash
# 验证ADB可用
adb version

# 验证Java环境
java -version

# 验证Gradle
./gradlew --version
```

## ⚠️ 严格避免使用的Terminal

### **❌ PowerShell（存在严重问题）**
- 编码兼容性问题
- ADB命令执行失败
- Gradle脚本路径问题
- 中文字符显示异常

### **❌ 其他非原生终端**
- Git Bash（可能有路径问题）
- WSL（不适用于macOS）
- 任何Windows终端模拟器

## 🎯 项目开发最佳实践

### **日常开发命令集**
```bash
# 项目目录快速导航
cd /Users/xzmx/Downloads/my-project/xiaozhi-android

# 清理编译
./gradlew clean

# 编译调试版本
./gradlew app:assembleDebug

# 设备管理
adb devices
adb shell pm clear info.dourok.voicebot
adb install -r app/build/outputs/apk/debug/app-debug.apk

# 日志查看
adb logcat | grep -E "(DeviceInfo|WS|ChatViewModel)"
```

### **问题排查工具**
```bash
# 设备绑定验证
cd foobar && python3 test_your_device_id.py

# 完整修复流程
bash foobar/fix_stt.sh

# 查看编译日志
./gradlew app:assembleDebug --info
```

## 🔍 Terminal健康检查

### **验证Terminal配置是否正确**
```bash
# 1. 检查当前shell
echo "当前Shell: $SHELL"

# 2. 检查Android环境
adb version
echo "ADB路径: $(which adb)"

# 3. 检查Java环境  
java -version

# 4. 检查Gradle
./gradlew --version

# 5. 检查Python（用于测试脚本）
python3 --version
```

### **成功配置的标志**
```
✅ Shell: /bin/zsh
✅ ADB版本正常显示
✅ Java版本正常显示  
✅ Gradle包装器可执行
✅ Python3可用
```

## 🎯 为什么这很重要

正确的Terminal环境确保：
- **🔧 编译成功率100%**
- **📱 设备调试顺畅**
- **🚀 开发效率最大化**
- **🐛 错误信息准确显示**
- **🔄 CI/CD流程兼容**

---
**记住：Android开发在macOS上，始终使用原生Terminal或iTerm2！** 