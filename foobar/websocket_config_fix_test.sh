#!/bin/bash

# 🔧 WebSocket配置修复验证脚本
echo "🔧 WebSocket配置修复验证脚本"
echo "================================"
echo "目标：验证SettingsRepository配置丢失问题的修复效果"
echo ""

# 应用包名
PACKAGE_NAME="info.dourok.voicebot"
MAIN_ACTIVITY="$PACKAGE_NAME/.MainActivity"

echo "📱 应用信息："
echo "   包名: $PACKAGE_NAME"
echo "   主活动: $MAIN_ACTIVITY"
echo ""

# 第一步：检查应用是否已安装
echo "🔍 第一步：检查应用状态"
echo "========================"

if adb shell pm list packages | grep -q "$PACKAGE_NAME"; then
    echo "✅ 应用已安装"
    
    # 获取应用版本信息
    VERSION_INFO=$(adb shell dumpsys package $PACKAGE_NAME | grep versionName)
    echo "📋 $VERSION_INFO"
else
    echo "❌ 应用未安装，请先安装APK"
    echo "   命令: adb install app-debug.apk"
    exit 1
fi

echo ""

# 第二步：清除应用数据（模拟全新安装）
echo "🧹 第二步：清除应用数据"
echo "========================"

echo "📤 停止应用..."
adb shell am force-stop $PACKAGE_NAME

echo "🗑️ 清除应用数据..."
adb shell pm clear $PACKAGE_NAME

if [ $? -eq 0 ]; then
    echo "✅ 应用数据已清除"
else
    echo "❌ 清除应用数据失败"
    exit 1
fi

echo ""

# 第三步：首次启动并监控日志
echo "🚀 第三步：首次启动测试"
echo "========================"

echo "📱 启动应用..."
adb shell am start -n $MAIN_ACTIVITY

echo "📊 监控关键日志（30秒）..."
echo "   关注：ActivationManager, ChatViewModel, WebSocket相关日志"
echo ""

# 启动日志监控（后台）
timeout 30s adb logcat -s "ActivationManager:*" "ChatViewModel:*" "WS:*" "Ota:*" | while read line; do
    echo "[$(date '+%H:%M:%S')] $line"
done &

LOG_PID=$!

# 等待30秒
sleep 30

# 停止日志监控
kill $LOG_PID 2>/dev/null

echo ""
echo "⏸️ 首次启动监控完成"

# 第四步：模拟应用重启
echo ""
echo "🔄 第四步：应用重启测试"
echo "========================"

echo "📤 强制停止应用..."
adb shell am force-stop $PACKAGE_NAME

echo "⏳ 等待3秒..."
sleep 3

echo "📱 重新启动应用..."
adb shell am start -n $MAIN_ACTIVITY

echo "📊 监控重启后的日志（30秒）..."
echo "   重点关注：配置恢复、缓存检查相关日志"
echo ""

# 启动日志监控（后台）
timeout 30s adb logcat -s "ActivationManager:*" "ChatViewModel:*" "WS:*" "Ota:*" | while read line; do
    # 高亮关键信息
    if echo "$line" | grep -q "缓存.*配置\|配置.*恢复\|SettingsRepository"; then
        echo "[$(date '+%H:%M:%S')] 🔧 $line"
    elif echo "$line" | grep -q "WebSocket.*null\|配置.*空\|URL.*空"; then
        echo "[$(date '+%H:%M:%S')] ❌ $line"
    elif echo "$line" | grep -q "WebSocket.*成功\|配置.*正常\|连接.*成功"; then
        echo "[$(date '+%H:%M:%S')] ✅ $line"
    else
        echo "[$(date '+%H:%M:%S')] $line"
    fi
done &

LOG_PID=$!

# 等待30秒
sleep 30

# 停止日志监控
kill $LOG_PID 2>/dev/null

echo ""
echo "⏸️ 重启测试监控完成"

# 第五步：检查配置状态
echo ""
echo "📋 第五步：配置状态检查"
echo "========================"

echo "🔍 检查DataStore配置文件..."
adb shell "ls -la /data/data/$PACKAGE_NAME/datastore/ 2>/dev/null || echo '配置文件不存在'"

echo ""
echo "🔍 检查SharedPreferences..."
adb shell "ls -la /data/data/$PACKAGE_NAME/shared_prefs/ 2>/dev/null || echo 'SharedPreferences不存在'"

echo ""

# 第六步：总结测试结果
echo "📊 第六步：测试结果总结"
echo "========================"

echo "✅ 测试完成！请检查以上日志中的关键信息："
echo ""
echo "🔍 成功修复的标志："
echo "   1. 重启后看到 '✅ 使用缓存的WebSocket配置'"
echo "   2. 或者看到 '✅ 配置已从DeviceConfigManager恢复'"
echo "   3. 没有出现 'WebSocket URL为空' 错误"
echo ""
echo "❌ 仍有问题的标志："
echo "   1. 重启后仍然执行OTA检查"
echo "   2. 出现 'SettingsRepository中WebSocket URL为空'"
echo "   3. WebSocket连接失败"
echo ""
echo "🔧 如果仍有问题，请："
echo "   1. 检查修改的代码是否正确编译"
echo "   2. 确认使用的是修复后的APK"
echo "   3. 查看完整的应用日志：adb logcat | grep -E '(WebSocket|ActivationManager|ChatViewModel)'"
echo ""
echo "🏁 测试脚本执行完成" 