#!/usr/bin/env python3
"""
执行STT修复的下一步操作
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    try:
        print(f"🔄 执行: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 成功")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ 失败 (退出码: {result.returncode})")
            if result.stderr:
                print(f"错误: {result.stderr}")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"❌ 执行命令失败: {e}")
        return False, "", str(e)

def main():
    print("🚀 执行STT修复的下一步操作...")
    
    # 确定项目根目录
    project_root = Path("/Users/xzmx/Downloads/my-project/xiaozhi-android")
    if not project_root.exists():
        print(f"❌ 项目目录不存在: {project_root}")
        return False
    
    print(f"📂 项目目录: {project_root}")
    
    # 步骤1: 编译APK
    print("\n📦 步骤1: 编译Debug APK...")
    success, stdout, stderr = run_command("./gradlew app:assembleDebug", cwd=project_root)
    
    if not success:
        print("❌ APK编译失败，详细错误信息:")
        print(stderr)
        return False
    
    print("✅ APK编译成功！")
    
    # 步骤2: 检查APK文件
    apk_path = project_root / "app/build/outputs/apk/debug/app-debug.apk"
    if apk_path.exists():
        print(f"✅ APK已生成: {apk_path}")
        stat = apk_path.stat()
        print(f"   文件大小: {stat.st_size / (1024*1024):.1f} MB")
        print(f"   修改时间: {stat.st_mtime}")
    else:
        print(f"❌ APK文件未找到: {apk_path}")
        return False
    
    # 步骤3: 检查连接的Android设备
    print("\n📱 步骤3: 检查连接的Android设备...")
    success, stdout, stderr = run_command("adb devices -l")
    
    if success and stdout:
        devices = [line for line in stdout.split('\n') if line.strip() and 'device' in line and not line.startswith('List')]
        if devices:
            print(f"✅ 发现 {len(devices)} 个连接的设备:")
            for device in devices:
                print(f"   {device}")
        else:
            print("⚠️  没有发现连接的设备")
    
    # 步骤4: 验证设备绑定状态
    print("\n🔍 步骤4: 验证设备绑定状态...")
    foobar_dir = project_root / "foobar"
    if (foobar_dir / "test_your_device_id.py").exists():
        success, stdout, stderr = run_command("python3 test_your_device_id.py", cwd=foobar_dir)
        if stdout:
            print("设备绑定验证结果:")
            print(stdout)
    else:
        print("⚠️  设备ID测试脚本不存在")
    
    # 步骤5: 提供下一步指南
    print("\n🎯 下一步手动操作指南:")
    print("1. 清除应用数据（重要！）:")
    print("   - 方法A: 手机设置 → 应用管理 → VoiceBot → 存储 → 清除数据")
    print("   - 方法B: 如果设备连接，运行: adb shell pm clear info.dourok.voicebot")
    print()
    print("2. 安装更新的APK:")
    print(f"   adb install -r {apk_path}")
    print()
    print("3. 测试STT功能:")
    print("   - 启动应用")
    print("   - 点击录音按钮")
    print("   - 说话测试")
    print("   - 期望：显示转录文字！")
    
    print("\n✅ 准备工作完成！请按照上述指南进行测试。")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 