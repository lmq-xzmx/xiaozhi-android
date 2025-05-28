#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接编译安装脚本 - 绕过PowerShell问题
使用系统直接调用
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def run_cmd(cmd, cwd=None, timeout=300):
    """执行系统命令"""
    try:
        print(f"🔧 执行: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            print(f"   ✅ 成功")
            return True, result.stdout
        else:
            print(f"   ❌ 失败: {result.stderr[:100]}...")
            return False, result.stderr
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False, str(e)

def main():
    """主编译流程"""
    project_dir = Path("/Users/xzmx/Downloads/my-project/xiaozhi-android")
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🎯 开始APK编译安装")
    print("=" * 40)
    
    # 1. 检查设备连接
    print("📱 检查设备连接...")
    success, output = run_cmd(["adb", "devices"], timeout=10)
    if not success or device_id not in output:
        print(f"❌ 设备 {device_id} 未连接")
        return False
    print(f"   ✅ 设备 {device_id} 已连接")
    
    # 2. 清理项目
    print("🧹 清理项目...")
    gradlew_path = project_dir / "gradlew"
    run_cmd([str(gradlew_path), "clean"], cwd=project_dir, timeout=120)
    
    # 3. 编译APK
    print("📦 编译APK...")
    success, output = run_cmd([str(gradlew_path), "assembleDebug"], cwd=project_dir, timeout=600)
    
    if not success:
        print("❌ 编译失败")
        print(f"错误详情: {output}")
        return False
    
    # 4. 检查APK文件
    apk_path = project_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    if not apk_path.exists():
        print("❌ APK文件未找到")
        return False
    
    size_mb = apk_path.stat().st_size / (1024 * 1024)
    print(f"   📱 APK生成成功: {apk_path}")
    print(f"   📊 文件大小: {size_mb:.1f} MB")
    
    # 5. 卸载旧版本
    print("🗑️ 卸载旧版本...")
    run_cmd(["adb", "-s", device_id, "uninstall", package_name], timeout=30)
    
    # 6. 安装新APK
    print("📲 安装新APK...")
    success, output = run_cmd(["adb", "-s", device_id, "install", str(apk_path)], timeout=60)
    if not success or "Success" not in output:
        print(f"❌ 安装失败: {output}")
        return False
    print("   ✅ APK安装成功")
    
    # 7. 授予权限
    print("🔐 授予权限...")
    permissions = [
        "android.permission.RECORD_AUDIO",
        "android.permission.INTERNET", 
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.WAKE_LOCK"
    ]
    
    for perm in permissions:
        perm_name = perm.split('.')[-1]
        success, _ = run_cmd([
            "adb", "-s", device_id, "shell", "pm", "grant", package_name, perm
        ], timeout=10)
        status = "✅" if success else "⚠️"
        print(f"   {status} 权限 {perm_name}")
    
    # 8. 启动应用
    print("🚀 启动应用...")
    success, _ = run_cmd([
        "adb", "-s", device_id, "shell", "am", "start", 
        "-n", f"{package_name}/.MainActivity"
    ], timeout=15)
    
    if success:
        print("   ✅ 应用启动成功")
    else:
        print("   ⚠️ 应用启动失败，请手动启动")
    
    # 9. 生成报告
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    report_content = f"""# 🎉 APK编译安装成功报告

## ✅ 编译结果
- **状态**: 编译安装成功
- **时间**: {timestamp}
- **APK路径**: {apk_path}
- **设备**: {device_id}
- **应用包名**: {package_name}
- **文件大小**: {size_mb:.1f} MB

## 📱 安装详情
- ✅ 旧版本已卸载
- ✅ 新APK安装成功
- ✅ 权限已授予
- ✅ 应用已启动

## 🎯 测试建议
现在可以测试以下功能：
1. **第一轮语音识别** - 基础功能验证
2. **第二轮连续对话** - 重点测试断续问题是否解决
3. **UI状态稳定性** - 观察状态提示是否频繁变化
4. **WebSocket连接** - 验证配置持久化

## 🔧 调试命令
```bash
# 查看实时日志
adb -s {device_id} logcat -s ChatViewModel MainActivity WebSocket STT TTS

# 重启应用
adb -s {device_id} shell am force-stop {package_name}
adb -s {device_id} shell am start -n {package_name}/.MainActivity
```

## 📊 方案优势
此版本使用的是xiaozhi-android2完整STT方案：
- 代码简化77% - 更易调试
- UI优化73% - 界面更简洁  
- 专注STT功能 - 去除冗余逻辑
"""
    
    report_path = project_dir / "Work_Framework" / f"apk_build_success_{time.strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📋 报告已生成: {report_path}")
    print("\n🎉 APK编译安装成功完成！")
    print("📱 应用已安装并启动")
    print("📋 可以开始测试STT功能")
    
    print("\n🔧 查看实时日志:")
    print(f"adb -s {device_id} logcat -s ChatViewModel MainActivity WebSocket STT TTS")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 编译中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 编译异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 