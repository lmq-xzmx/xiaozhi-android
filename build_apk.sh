#!/bin/bash
echo "开始构建APK..."
./gradlew clean assembleDebug
echo "构建完成！" 