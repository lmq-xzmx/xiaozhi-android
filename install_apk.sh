#!/bin/bash
echo "检查APK文件..."
ls -la app/build/outputs/apk/debug/

echo "检查连接的设备..."
adb devices

echo "安装APK到设备..."
adb install -r app/build/outputs/apk/debug/app-debug.apk

echo "安装完成！" 