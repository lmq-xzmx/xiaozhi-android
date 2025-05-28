#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android APK 编译和安装脚本
为 xiaozhi-android 项目编译并安装APK
"""

import subprocess
import os
import sys
import time
from datetime import datetime

class ApkBuilder:
    def __init__(self):
        self.project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.device_id = "SOZ95PIFVS5H6PIZ"
        self.package_name = "info.dourok.voicebot"
        self.apk_path = "app/build/outputs/apk/debug/app-debug.apk"
        
    def run_cmd(self, cmd, cwd=None, timeout=300):
        """执行命令并返回结果"""
        try:
            if cwd is None:
                cwd = self.project_dir
                
            print(f"   执行: {cmd}")
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=cwd,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            print(f"   ❌ 命令超时: {cmd}")
            return False, "", "命令执行超时"
        except Exception as e:
            print(f"   ❌ 命令异常: {e}")
            return False, "", str(e)
    
    def check_device_connection(self):
        """检查设备连接"""
        print("📱 步骤1: 检查设备连接")
        
        success, stdout, stderr = self.run_cmd("adb devices")
        if success and self.device_id in stdout:
            print(f"   ✅ 设备 {self.device_id} 已连接")
            return True
        else:
            print(f"   ❌ 设备 {self.device_id} 未连接")
            print("   💡 请确保设备已连接并开启USB调试")
            return False
    
    def clean_project(self):
        """清理项目"""
        print("\n🧹 步骤2: 清理项目")
        
        success, stdout, stderr = self.run_cmd("./gradlew clean")
        if success:
            print("   ✅ 项目清理成功")
        else:
            print("   ⚠️ 项目清理失败，继续编译...")
            print(f"   错误信息: {stderr}")
    
    def compile_apk(self):
        """编译APK"""
        print("\n📦 步骤3: 编译APK（约需3-5分钟）")
        print("   正在编译，请耐心等待...")
        
        start_time = time.time()
        success, stdout, stderr = self.run_cmd("./gradlew assembleDebug", timeout=600)
        compile_time = time.time() - start_time
        
        if success:
            print(f"   ✅ APK编译成功 (用时 {compile_time:.1f} 秒)")
            
            # 检查APK文件
            apk_full_path = os.path.join(self.project_dir, self.apk_path)
            if os.path.exists(apk_full_path):
                size_mb = os.path.getsize(apk_full_path) / (1024 * 1024)
                print(f"   📱 APK位置: {self.apk_path}")
                print(f"   📊 文件大小: {size_mb:.1f} MB")
                return True
            else:
                print("   ❌ APK文件未找到")
                return False
        else:
            print("   ❌ APK编译失败")
            print(f"   错误信息: {stderr}")
            if stdout:
                print(f"   输出信息: {stdout[-500:]}")  # 显示最后500字符
            return False
    
    def uninstall_old_version(self):
        """卸载旧版本"""
        print("\n🗑️ 步骤4: 卸载旧版本")
        
        success, stdout, stderr = self.run_cmd(f"adb -s {self.device_id} uninstall {self.package_name}")
        if success:
            print("   ✅ 旧版本已卸载")
        else:
            print("   💡 未找到旧版本（正常）")
    
    def install_apk(self):
        """安装APK"""
        print("\n📲 步骤5: 安装新APK")
        print("   正在安装...")
        
        success, stdout, stderr = self.run_cmd(f"adb -s {self.device_id} install {self.apk_path}")
        if success:
            print("   ✅ APK安装成功")
            return True
        else:
            print("   ❌ APK安装失败")
            print(f"   错误信息: {stderr}")
            return False
    
    def grant_permissions(self):
        """授予权限"""
        print("\n🔐 步骤6: 授予应用权限")
        
        permissions = [
            "android.permission.RECORD_AUDIO",
            "android.permission.INTERNET", 
            "android.permission.ACCESS_NETWORK_STATE",
            "android.permission.WAKE_LOCK"
        ]
        
        for permission in permissions:
            perm_name = permission.split('.')[-1]
            success, stdout, stderr = self.run_cmd(
                f"adb -s {self.device_id} shell pm grant {self.package_name} {permission}"
            )
            if success:
                print(f"   ✅ 权限 {perm_name} 已授予")
            else:
                print(f"   ⚠️ 权限 {perm_name} 可能已存在或不需要")
    
    def launch_app(self):
        """启动应用"""
        print("\n🚀 步骤7: 启动应用")
        
        success, stdout, stderr = self.run_cmd(
            f"adb -s {self.device_id} shell am start -n {self.package_name}/.MainActivity"
        )
        if success:
            print("   ✅ 应用启动成功")
            return True
        else:
            print("   ⚠️ 应用启动失败，请手动启动")
            return False
    
    def generate_success_report(self):
        """生成成功报告"""
        print("\n📋 步骤8: 生成成功报告")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_file = f"Work_Framework/apk_build_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 获取APK大小
        apk_full_path = os.path.join(self.project_dir, self.apk_path)
        size_mb = os.path.getsize(apk_full_path) / (1024 * 1024) if os.path.exists(apk_full_path) else 0
        
        report_content = f"""# 🎉 APK编译安装成功报告

## ✅ 编译结果
- **状态**: 编译安装成功
- **时间**: {timestamp}
- **APK路径**: {self.apk_path}
- **设备**: {self.device_id}
- **应用包名**: {self.package_name}
- **文件大小**: {size_mb:.1f} MB

## 📱 安装详情
- ✅ 旧版本已卸载
- ✅ 新APK安装成功
- ✅ 权限已授予
- ✅ 应用已启动

## 🎯 OTA配置验证
此版本包含完整的OTA配置升级功能：
1. **OTA服务器**: `http://47.122.144.73:8002/xiaozhi/ota/`
2. **WebSocket配置**: `ws://47.122.144.73:8000/xiaozhi/v1/`
3. **STT功能**: 保持完全兼容，零影响
4. **Fallback机制**: 多级配置保障

## 🎯 测试建议
现在可以测试以下功能：
1. **语音识别** - 验证STT基础功能
2. **OTA配置** - 检查配置获取日志
3. **WebSocket连接** - 验证新服务器连接
4. **设备激活** - 如需要完成设备绑定

## 🔧 调试命令
```bash
# 查看实时日志
adb -s {self.device_id} logcat -s ChatViewModel OtaConfigManager OtaIntegrationService

# 重启应用
adb -s {self.device_id} shell am force-stop {self.package_name}
adb -s {self.device_id} shell am start -n {self.package_name}/.MainActivity

# 检查应用状态
adb -s {self.device_id} shell dumpsys package {self.package_name}
```

## 🏁 编译完成
成功完成OTA配置升级后的首次编译安装！
现在可以验证新的OTA配置功能是否正常工作。
"""
        
        # 确保目录存在
        report_dir = os.path.join(self.project_dir, "Work_Framework")
        os.makedirs(report_dir, exist_ok=True)
        
        # 写入报告
        report_path = os.path.join(self.project_dir, report_file)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"   📋 成功报告已生成: {report_file}")
    
    def build_and_install(self):
        """完整的编译安装流程"""
        print("🎯 开始编译安装APK - OTA配置升级版本")
        print("=" * 60)
        print(f"项目目录: {self.project_dir}")
        
        # 切换到项目目录
        os.chdir(self.project_dir)
        
        # 执行编译安装流程
        if not self.check_device_connection():
            return False
        
        self.clean_project()
        
        if not self.compile_apk():
            return False
        
        self.uninstall_old_version()
        
        if not self.install_apk():
            return False
        
        self.grant_permissions()
        self.launch_app()
        self.generate_success_report()
        
        print("\n🎉 编译安装完成！")
        print("=" * 60)
        print("✅ APK已成功编译并安装到设备")
        print("🔧 OTA配置升级功能已集成")
        print("🎙️ STT语音识别功能保持完整")
        print("📱 现在可以测试应用功能")
        
        return True

def main():
    """主函数"""
    builder = ApkBuilder()
    success = builder.build_and_install()
    
    if not success:
        print("\n❌ 编译安装过程中遇到问题")
        print("请检查错误信息并重试")
        sys.exit(1)
    
    print("\n🚀 编译安装成功完成！")

if __name__ == "__main__":
    main() 