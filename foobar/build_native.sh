#!/bin/bash
cd /Users/xzmx/Downloads/my-project/xiaozhi-android
echo "🔧 开始编译Android项目..."
./gradlew clean
./gradlew assembleDebug
echo "✅ 编译完成！" 