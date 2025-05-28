#!/usr/bin/env python3
"""
诊断和修复Gradle配置问题
"""

import subprocess
import os
from pathlib import Path

def run_command_with_output(cmd, cwd=None):
    """执行命令并返回详细输出"""
    try:
        print(f"🔄 执行: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=300)
        
        print(f"退出码: {result.returncode}")
        if result.stdout:
            print("标准输出:")
            print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
            
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print("❌ 命令执行超时")
        return False, "", "超时"
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False, "", str(e)

def main():
    print("🔧 诊断Gradle配置问题...")
    
    project_root = Path("/Users/xzmx/Downloads/my-project/xiaozhi-android")
    if not project_root.exists():
        print(f"❌ 项目目录不存在: {project_root}")
        return False
    
    os.chdir(project_root)
    print(f"📂 工作目录: {project_root}")
    
    # 1. 检查Gradle wrapper版本
    print("\n📋 步骤1: 检查Gradle版本...")
    wrapper_props = project_root / "gradle/wrapper/gradle-wrapper.properties"
    if wrapper_props.exists():
        with open(wrapper_props, 'r') as f:
            content = f.read()
            print("Gradle wrapper配置:")
            print(content)
    
    # 2. 检查libs.versions.toml
    print("\n📋 步骤2: 检查版本配置...")
    versions_file = project_root / "gradle/libs.versions.toml"
    if versions_file.exists():
        with open(versions_file, 'r') as f:
            lines = f.readlines()[:10]  # 只显示前10行
            print("版本配置文件开头:")
            for i, line in enumerate(lines, 1):
                print(f"{i:2d}: {line.rstrip()}")
    
    # 3. 尝试Gradle版本检查
    print("\n📋 步骤3: 检查Gradle可执行性...")
    success, stdout, stderr = run_command_with_output("./gradlew --version")
    
    if not success:
        print("❌ Gradle无法执行，可能的原因:")
        print("1. AGP版本不兼容")
        print("2. 依赖解析问题")
        print("3. 配置文件语法错误")
        
        # 尝试修复AGP版本
        print("\n🔧 尝试修复AGP版本...")
        try:
            # 读取当前版本配置
            with open(versions_file, 'r') as f:
                content = f.read()
            
            # 替换为更稳定的版本
            if 'agp = "8.6.1"' in content:
                new_content = content.replace('agp = "8.6.1"', 'agp = "8.5.2"')
                with open(versions_file, 'w') as f:
                    f.write(new_content)
                print("✅ AGP版本已修改为8.5.2")
                
                # 重新测试
                print("\n🔄 重新测试Gradle...")
                success, stdout, stderr = run_command_with_output("./gradlew --version")
                
        except Exception as e:
            print(f"❌ 修复失败: {e}")
    
    if success:
        print("✅ Gradle配置正常！")
        
        # 尝试清理项目
        print("\n🧹 尝试清理项目...")
        success, stdout, stderr = run_command_with_output("./gradlew clean")
        
        if success:
            print("✅ 项目清理成功！")
            
            # 尝试编译
            print("\n📦 尝试编译APK...")
            success, stdout, stderr = run_command_with_output("./gradlew app:assembleDebug")
            
            if success:
                print("🎉 APK编译成功！")
                return True
    
    print("\n💡 建议的解决方案:")
    print("1. 打开Android Studio，让它自动修复项目配置")
    print("2. 或者使用以下命令在Terminal中执行:")
    print("   cd /Users/xzmx/Downloads/my-project/xiaozhi-android")
    print("   ./gradlew wrapper --gradle-version 8.5")
    print("   然后修改AGP版本为8.5.2")
    
    return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 自动修复失败，需要手动操作") 