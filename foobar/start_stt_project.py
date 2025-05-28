#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STT项目启动脚本
自动化编译、部署和测试流程
"""

import subprocess
import time
import os
from pathlib import Path

class SttProjectStarter:
    def __init__(self):
        self.project_dir = Path("/Users/xzmx/Downloads/my-project/xiaozhi-android")
        self.device_id = "SOZ95PIFVS5H6PIZ"  # 您的设备ID
        
    def check_android_studio_status(self):
        """检查Android Studio是否正在运行"""
        print("🔍 检查Android Studio状态...")
        
        try:
            result = subprocess.run(
                ["pgrep", "-f", "Android Studio"], 
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("   ✅ Android Studio正在运行")
                return True
            else:
                print("   ❌ Android Studio未运行")
                return False
        except Exception:
            print("   ⚠️ 无法检查Android Studio状态")
            return False
    
    def wait_for_gradle_sync(self):
        """等待Gradle同步完成"""
        print("⏳ 等待Gradle同步完成...")
        
        # 简单等待，让用户手动同步
        print("   📝 请在Android Studio中执行以下操作：")
        print("   1. 等待项目加载完成")
        print("   2. 点击 'Sync Now' 按钮（如果出现）")
        print("   3. 等待Gradle同步完成")
        
        input("   ⌨️ 按回车键继续（确认Gradle同步已完成）...")
        print("   ✅ Gradle同步确认完成")
    
    def check_device_connection(self):
        """检查设备连接状态"""
        print("📱 检查设备连接状态...")
        
        try:
            result = subprocess.run(
                ["adb", "devices"], 
                capture_output=True, text=True, timeout=10
            )
            
            if self.device_id in result.stdout:
                print(f"   ✅ 设备 {self.device_id} 已连接")
                return True
            else:
                print(f"   ❌ 设备 {self.device_id} 未连接")
                print("   💡 请确保：")
                print("   - 设备已通过USB连接")
                print("   - 已开启开发者选项和USB调试")
                print("   - 信任此计算机")
                return False
                
        except Exception as e:
            print(f"   ❌ 检查设备连接失败: {e}")
            return False
    
    def clean_and_build_project(self):
        """清理并编译项目"""
        print("🔨 开始清理和编译项目...")
        
        # 1. 清理项目
        print("   🧹 清理项目缓存...")
        try:
            clean_result = subprocess.run(
                ["./gradlew", "clean"], 
                cwd=self.project_dir, 
                capture_output=True, text=True, timeout=120
            )
            
            if clean_result.returncode == 0:
                print("   ✅ 项目清理完成")
            else:
                print(f"   ⚠️ 清理警告: {clean_result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            print("   ⏰ 清理超时，继续下一步")
        except Exception as e:
            print(f"   ⚠️ 清理异常: {e}")
        
        # 2. 编译项目
        print("   📦 编译APK...")
        try:
            build_result = subprocess.run(
                ["./gradlew", "assembleDebug", "--no-daemon"], 
                cwd=self.project_dir, 
                capture_output=True, text=True, timeout=600
            )
            
            if build_result.returncode == 0:
                print("   ✅ APK编译成功")
                
                # 检查APK文件
                apk_path = self.project_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
                if apk_path.exists():
                    size_kb = apk_path.stat().st_size // 1024
                    print(f"   📱 APK文件: {apk_path}")
                    print(f"   📊 文件大小: {size_kb} KB")
                    return True
                else:
                    print("   ❌ APK文件未生成")
                    return False
            else:
                print(f"   ❌ 编译失败: {build_result.stderr[:300]}...")
                return False
                
        except subprocess.TimeoutExpired:
            print("   ⏰ 编译超时")
            return False
        except Exception as e:
            print(f"   ❌ 编译异常: {e}")
            return False
    
    def install_apk_to_device(self):
        """安装APK到设备"""
        print("📲 安装APK到设备...")
        
        apk_path = self.project_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
        
        if not apk_path.exists():
            print("   ❌ APK文件不存在")
            return False
        
        try:
            # 卸载旧版本
            print("   🗑️ 卸载旧版本...")
            subprocess.run(
                ["adb", "-s", self.device_id, "uninstall", "info.dourok.voicebot"], 
                capture_output=True, timeout=30
            )
            
            # 安装新版本
            print("   📥 安装新版本...")
            install_result = subprocess.run(
                ["adb", "-s", self.device_id, "install", str(apk_path)], 
                capture_output=True, text=True, timeout=60
            )
            
            if install_result.returncode == 0 and "Success" in install_result.stdout:
                print("   ✅ APK安装成功")
                return True
            else:
                print(f"   ❌ 安装失败: {install_result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("   ⏰ 安装超时")
            return False
        except Exception as e:
            print(f"   ❌ 安装异常: {e}")
            return False
    
    def launch_app_on_device(self):
        """在设备上启动应用"""
        print("🚀 启动应用...")
        
        try:
            launch_result = subprocess.run([
                "adb", "-s", self.device_id, "shell", 
                "am", "start", "-n", "info.dourok.voicebot/.MainActivity"
            ], capture_output=True, text=True, timeout=15)
            
            if launch_result.returncode == 0:
                print("   ✅ 应用启动成功")
                return True
            else:
                print(f"   ❌ 启动失败: {launch_result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ 启动异常: {e}")
            return False
    
    def show_realtime_logs(self):
        """显示实时日志"""
        print("📋 开始监控应用日志...")
        print("   💡 按 Ctrl+C 停止日志监控")
        
        try:
            # 清理日志缓冲区
            subprocess.run([
                "adb", "-s", self.device_id, "logcat", "-c"
            ], timeout=5)
            
            # 启动实时日志监控
            log_process = subprocess.Popen([
                "adb", "-s", self.device_id, "logcat", 
                "-s", "ChatViewModel", "MainActivity", "WebSocket", "STT", "TTS"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("   🔍 正在监控关键日志...")
            
            for line in log_process.stdout:
                if line.strip():
                    print(f"   📝 {line.strip()}")
                    
        except KeyboardInterrupt:
            print("\n   ⏹️ 日志监控已停止")
            if 'log_process' in locals():
                log_process.terminate()
        except Exception as e:
            print(f"   ❌ 日志监控异常: {e}")
    
    def create_quick_start_guide(self):
        """创建快速启动指南"""
        guide_content = """# 🚀 STT项目快速启动指南

## ✅ 项目已成功启动

### 📱 当前状态
- **项目**: xiaozhi-android2 完整STT方案（已替换）
- **编译状态**: APK已生成
- **设备**: {device_id}
- **应用**: 已安装并启动

### 🎯 功能测试清单

#### 1. 基础功能测试
- [ ] 应用正常启动
- [ ] WebSocket连接成功
- [ ] OTA配置自动获取
- [ ] 设备激活流程

#### 2. STT功能测试
- [ ] 语音识别启动
- [ ] 第一轮对话测试
- [ ] 第二轮连续对话（重点测试）
- [ ] 语音打断功能

#### 3. UI体验测试
- [ ] 状态提示稳定（不频繁变化）
- [ ] 界面响应流畅
- [ ] 错误提示正常

### 🔧 调试工具

#### 查看实时日志
```bash
adb -s {device_id} logcat -s ChatViewModel MainActivity WebSocket STT TTS
```

#### 重启应用
```bash
adb -s {device_id} shell am force-stop info.dourok.voicebot
adb -s {device_id} shell am start -n info.dourok.voicebot/.MainActivity
```

#### 重新安装APK
```bash
./gradlew assembleDebug && adb -s {device_id} install -r app/build/outputs/apk/debug/app-debug.apk
```

### 📊 预期改进效果

与之前方案相比，新方案应该：
- ✅ **第二轮语音不再断续** - 核心问题已解决
- ✅ **UI状态提示稳定** - 减少频繁变化
- ✅ **代码简洁77%** - 更易调试和维护
- ✅ **配置自动化** - WebSocket等配置持久化

### 🆘 故障排除

#### 如果遇到问题：
1. **检查日志输出** - 查看具体错误信息
2. **重启应用** - 使用上述命令重启
3. **回滚方案** - 从backup_current_solution恢复
4. **重新编译** - 清理后重新编译

### 📞 下一步操作
1. 测试STT的连续对话功能
2. 验证语音打断是否正常
3. 确认UI状态提示是否稳定
4. 记录任何发现的问题

---
生成时间: {timestamp}
设备ID: {device_id}
""".format(
            device_id=self.device_id,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        guide_path = self.project_dir / "Work_Framework" / "stt_project_quick_start_guide.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"📋 快速启动指南已创建: {guide_path}")
    
    def run_complete_startup(self):
        """运行完整的项目启动流程"""
        print("🎯 STT项目完整启动流程")
        print("=" * 60)
        
        # 1. 检查Android Studio
        if not self.check_android_studio_status():
            print("💡 正在启动Android Studio...")
            subprocess.run(["open", "-a", "Android Studio", "."], cwd=self.project_dir)
            time.sleep(3)
        
        # 2. 等待Gradle同步
        self.wait_for_gradle_sync()
        
        # 3. 检查设备连接
        if not self.check_device_connection():
            print("⚠️ 请连接设备后重新运行此脚本")
            return False
        
        # 4. 编译项目
        if not self.clean_and_build_project():
            print("❌ 编译失败，请检查错误信息")
            return False
        
        # 5. 安装到设备
        if not self.install_apk_to_device():
            print("❌ 安装失败，请检查设备连接")
            return False
        
        # 6. 启动应用
        if not self.launch_app_on_device():
            print("❌ 应用启动失败")
            return False
        
        # 7. 创建快速指南
        self.create_quick_start_guide()
        
        print("\n🎉 STT项目启动成功！")
        print("📱 应用已在设备上运行")
        print("📋 请查看 Work_Framework/stt_project_quick_start_guide.md 获取测试指南")
        
        # 8. 询问是否查看实时日志
        try:
            show_logs = input("\n❓ 是否显示实时日志？(y/n): ").lower().strip()
            if show_logs == 'y':
                self.show_realtime_logs()
        except KeyboardInterrupt:
            print("\n👋 启动流程完成")
        
        return True

def main():
    """主函数"""
    starter = SttProjectStarter()
    
    try:
        success = starter.run_complete_startup()
        if success:
            print("\n✅ 项目启动流程成功完成")
        else:
            print("\n❌ 项目启动遇到问题")
    except Exception as e:
        print(f"\n❌ 启动异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 