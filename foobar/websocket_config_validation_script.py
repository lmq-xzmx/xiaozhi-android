#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket配置验证脚本
用于验证Android端WebSocket配置修复效果
"""

import subprocess
import time
import json
import re
from typing import Optional, Dict, Any

class WebSocketConfigValidator:
    def __init__(self, package_name: str = "info.dourok.voicebot"):
        self.package_name = package_name
        self.adb_available = self._check_adb()
        
    def _check_adb(self) -> bool:
        """检查ADB是否可用"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ ADB不可用，请确保Android SDK已安装并配置PATH")
            return False
    
    def _run_adb_command(self, command: list) -> Optional[str]:
        """执行ADB命令"""
        if not self.adb_available:
            return None
            
        try:
            result = subprocess.run(['adb'] + command, 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"⚠️ ADB命令执行失败: {' '.join(command)}")
                print(f"错误: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"⏰ ADB命令超时: {' '.join(command)}")
            return None
    
    def check_device_connected(self) -> bool:
        """检查设备连接状态"""
        print("📱 检查设备连接状态...")
        devices = self._run_adb_command(['devices'])
        if devices and 'device' in devices:
            print("✅ 设备已连接")
            return True
        else:
            print("❌ 未检测到设备，请确保设备已连接并启用USB调试")
            return False
    
    def check_app_installed(self) -> bool:
        """检查应用是否已安装"""
        print(f"📦 检查应用安装状态: {self.package_name}")
        packages = self._run_adb_command(['shell', 'pm', 'list', 'packages', self.package_name])
        if packages and self.package_name in packages:
            print("✅ 应用已安装")
            return True
        else:
            print("❌ 应用未安装")
            return False
    
    def get_shared_preferences(self) -> Optional[Dict[str, Any]]:
        """获取SharedPreferences配置"""
        print("🔍 读取SharedPreferences配置...")
        
        # 尝试读取配置文件
        prefs_path = f"/data/data/{self.package_name}/shared_prefs/xiaozhi_settings.xml"
        content = self._run_adb_command(['shell', 'cat', prefs_path])
        
        if content:
            print("✅ 成功读取配置文件")
            return self._parse_shared_preferences(content)
        else:
            print("⚠️ 无法读取配置文件，可能需要root权限或配置文件不存在")
            return None
    
    def _parse_shared_preferences(self, xml_content: str) -> Dict[str, Any]:
        """解析SharedPreferences XML内容"""
        config = {}
        
        # 提取WebSocket URL
        websocket_match = re.search(r'<string name="websocket_url">(.*?)</string>', xml_content)
        if websocket_match:
            config['websocket_url'] = websocket_match.group(1)
        
        # 提取传输类型
        transport_match = re.search(r'<string name="transport_type">(.*?)</string>', xml_content)
        if transport_match:
            config['transport_type'] = transport_match.group(1)
        
        # 提取MQTT配置
        mqtt_match = re.search(r'<string name="mqtt_config">(.*?)</string>', xml_content)
        if mqtt_match:
            config['mqtt_config'] = mqtt_match.group(1)
        
        return config
    
    def monitor_logcat(self, duration: int = 30) -> Dict[str, list]:
        """监控logcat日志"""
        print(f"📊 监控logcat日志 ({duration}秒)...")
        
        # 清除旧日志
        self._run_adb_command(['logcat', '-c'])
        
        # 启动logcat监控
        try:
            process = subprocess.Popen(
                ['adb', 'logcat', '-s', 'SettingsRepository', 'ChatViewModel', 'Ota'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logs = {
                'websocket_config': [],
                'ota_events': [],
                'errors': [],
                'success': []
            }
            
            start_time = time.time()
            while time.time() - start_time < duration:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    
                    # 分类日志
                    if 'WebSocket URL' in line:
                        logs['websocket_config'].append(line)
                    elif 'OTA' in line:
                        logs['ota_events'].append(line)
                    elif '❌' in line or 'ERROR' in line:
                        logs['errors'].append(line)
                    elif '✅' in line or 'SUCCESS' in line:
                        logs['success'].append(line)
            
            process.terminate()
            return logs
            
        except Exception as e:
            print(f"❌ logcat监控失败: {e}")
            return {}
    
    def test_app_restart_persistence(self) -> bool:
        """测试应用重启后配置持久性"""
        print("🔄 测试应用重启后配置持久性...")
        
        # 1. 强制停止应用
        print("1️⃣ 强制停止应用...")
        self._run_adb_command(['shell', 'am', 'force-stop', self.package_name])
        time.sleep(2)
        
        # 2. 启动应用
        print("2️⃣ 启动应用...")
        self._run_adb_command(['shell', 'am', 'start', '-n', f'{self.package_name}/.MainActivity'])
        time.sleep(5)
        
        # 3. 监控启动日志
        print("3️⃣ 监控启动日志...")
        logs = self.monitor_logcat(duration=15)
        
        # 4. 分析结果
        websocket_logs = logs.get('websocket_config', [])
        success_logs = logs.get('success', [])
        
        persistence_success = any('持久化WebSocket URL' in log for log in websocket_logs)
        
        if persistence_success:
            print("✅ 配置持久性测试通过")
            return True
        else:
            print("❌ 配置持久性测试失败")
            return False
    
    def run_full_validation(self) -> Dict[str, bool]:
        """运行完整验证流程"""
        print("🚀 开始WebSocket配置验证...")
        print("=" * 50)
        
        results = {}
        
        # 基础检查
        results['device_connected'] = self.check_device_connected()
        if not results['device_connected']:
            return results
        
        results['app_installed'] = self.check_app_installed()
        if not results['app_installed']:
            return results
        
        # 配置检查
        config = self.get_shared_preferences()
        results['config_readable'] = config is not None
        
        if config:
            results['websocket_url_configured'] = 'websocket_url' in config and config['websocket_url']
            print(f"📡 WebSocket URL: {config.get('websocket_url', '未配置')}")
            print(f"🚀 传输类型: {config.get('transport_type', '未配置')}")
        else:
            results['websocket_url_configured'] = False
        
        # 持久性测试
        results['persistence_test'] = self.test_app_restart_persistence()
        
        # 总结
        print("\n" + "=" * 50)
        print("📋 验证结果总结:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        overall_success = all(results.values())
        print(f"\n🎯 总体结果: {'✅ 全部通过' if overall_success else '❌ 存在问题'}")
        
        return results

def main():
    """主函数"""
    print("WebSocket配置验证脚本")
    print("用于验证Android端WebSocket配置修复效果")
    print("=" * 50)
    
    validator = WebSocketConfigValidator()
    results = validator.run_full_validation()
    
    # 根据结果提供建议
    if not all(results.values()):
        print("\n💡 修复建议:")
        
        if not results.get('device_connected', False):
            print("  - 确保Android设备已连接并启用USB调试")
        
        if not results.get('app_installed', False):
            print("  - 安装最新版本的应用APK")
        
        if not results.get('websocket_url_configured', False):
            print("  - 执行OTA配置流程，获取WebSocket URL")
        
        if not results.get('persistence_test', False):
            print("  - 应用SettingsRepository持久化修复补丁")
            print("  - 检查SharedPreferences读写权限")

if __name__ == "__main__":
    main() 