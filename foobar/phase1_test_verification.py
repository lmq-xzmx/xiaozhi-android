#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一阶段优化成果验证脚本
用于检查已实施的功能是否正确集成到项目中
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

class Phase1Verifier:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_src = self.project_root / "app" / "src" / "main" / "java" / "info" / "dourok" / "voicebot"
        self.results = []
        
    def print_header(self, title: str):
        """打印格式化的标题"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_result(self, check_name: str, status: bool, details: str = ""):
        """打印检查结果"""
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")
        if details:
            print(f"   📋 {details}")
        self.results.append((check_name, status, details))
        
    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """检查文件是否存在"""
        exists = file_path.exists()
        size = file_path.stat().st_size if exists else 0
        details = f"文件大小: {size} 字节" if exists else "文件不存在"
        self.print_result(f"{description}", exists, details)
        return exists
        
    def check_kotlin_class(self, file_path: Path, class_name: str, expected_methods: List[str]) -> Tuple[bool, List[str]]:
        """检查Kotlin类及其方法"""
        if not file_path.exists():
            return False, []
            
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 检查类定义
            class_pattern = rf"class\s+{class_name}"
            has_class = bool(re.search(class_pattern, content))
            
            # 检查方法
            found_methods = []
            for method in expected_methods:
                method_pattern = rf"fun\s+{method}\s*\("
                if re.search(method_pattern, content):
                    found_methods.append(method)
                    
            return has_class, found_methods
            
        except Exception as e:
            print(f"   ⚠️ 读取文件错误: {e}")
            return False, []
            
    def verify_device_id_manager(self):
        """验证设备ID管理器"""
        self.print_header("验证设备ID管理器")
        
        file_path = self.app_src / "data" / "model" / "DeviceIdManager.kt"
        exists = self.check_file_exists(file_path, "DeviceIdManager.kt 文件存在")
        
        if exists:
            expected_methods = [
                "getStableDeviceId",
                "setCustomDeviceId", 
                "clearCustomDeviceId",
                "generateDeviceFingerprint",
                "generateMacFormatId"
            ]
            
            has_class, found_methods = self.check_kotlin_class(file_path, "DeviceIdManager", expected_methods)
            
            self.print_result("DeviceIdManager 类定义", has_class)
            
            for method in expected_methods:
                has_method = method in found_methods
                self.print_result(f"方法 {method}", has_method)
                
            # 检查依赖注入注解
            content = file_path.read_text(encoding='utf-8')
            has_singleton = "@Singleton" in content
            has_inject = "@Inject" in content
            
            self.print_result("使用 @Singleton 注解", has_singleton)
            self.print_result("使用 @Inject 构造函数", has_inject)
            
    def verify_error_handler(self):
        """验证错误处理器"""
        self.print_header("验证错误处理器")
        
        file_path = self.app_src / "data" / "model" / "ErrorHandler.kt"
        exists = self.check_file_exists(file_path, "ErrorHandler.kt 文件存在")
        
        if exists:
            expected_methods = [
                "translateError",
                "translateHttpError",
                "isRetryableError",
                "getErrorSeverity",
                "getActionSuggestion"
            ]
            
            has_class, found_methods = self.check_kotlin_class(file_path, "ErrorHandler", expected_methods)
            
            self.print_result("ErrorHandler 类定义", has_class)
            
            for method in expected_methods:
                has_method = method in found_methods
                self.print_result(f"方法 {method}", has_method)
                
            # 检查枚举类型
            content = file_path.read_text(encoding='utf-8')
            has_error_severity = "enum class ErrorSeverity" in content
            has_action_suggestion = "enum class ActionSuggestion" in content
            has_error_info = "data class ErrorInfo" in content
            
            self.print_result("ErrorSeverity 枚举", has_error_severity)
            self.print_result("ActionSuggestion 枚举", has_action_suggestion)
            self.print_result("ErrorInfo 数据类", has_error_info)
            
    def verify_retry_manager(self):
        """验证重试管理器"""
        self.print_header("验证自动重试管理器")
        
        file_path = self.app_src / "data" / "model" / "AutoRetryManager.kt"
        exists = self.check_file_exists(file_path, "AutoRetryManager.kt 文件存在")
        
        if exists:
            expected_methods = [
                "retryWithExponentialBackoff",
                "smartRetry",
                "conditionalRetry",
                "quickRetry",
                "getRecommendedRetryConfig",
                "retryWithRecommendedConfig"
            ]
            
            has_class, found_methods = self.check_kotlin_class(file_path, "AutoRetryManager", expected_methods)
            
            self.print_result("AutoRetryManager 类定义", has_class)
            
            for method in expected_methods:
                has_method = method in found_methods
                self.print_result(f"方法 {method}", has_method)
                
            # 检查相关类型
            content = file_path.read_text(encoding='utf-8')
            has_operation_type = "enum class OperationType" in content
            has_retry_config = "data class RetryConfig" in content
            has_retry_state = "data class RetryState" in content
            
            self.print_result("OperationType 枚举", has_operation_type)
            self.print_result("RetryConfig 数据类", has_retry_config)
            self.print_result("RetryState 数据类", has_retry_state)
            
    def verify_binding_dialog(self):
        """验证绑定指导对话框"""
        self.print_header("验证绑定指导对话框")
        
        file_path = self.app_src / "ui" / "components" / "BindingGuideDialog.kt"
        exists = self.check_file_exists(file_path, "BindingGuideDialog.kt 文件存在")
        
        if exists:
            content = file_path.read_text(encoding='utf-8')
            
            # 检查主要组件函数
            components = [
                "BindingGuideDialog",
                "DeviceInfoSection", 
                "ActivationCodeSection",
                "BindingStepsSection",
                "ActionButtonsSection"
            ]
            
            for component in components:
                has_component = f"fun {component}" in content
                self.print_result(f"组件函数 {component}", has_component)
                
            # 检查关键功能
            has_copy_function = "copyToClipboard" in content
            has_open_url = "openUrl" in content
            has_material3 = "import androidx.compose.material3.*" in content
            
            self.print_result("复制到剪贴板功能", has_copy_function)
            self.print_result("打开URL功能", has_open_url)
            self.print_result("使用 Material 3", has_material3)
            
    def verify_ota_improvements(self):
        """验证OTA改进"""
        self.print_header("验证OTA改进")
        
        file_path = self.app_src / "Ota.kt"
        exists = self.check_file_exists(file_path, "Ota.kt 文件存在")
        
        if exists:
            content = file_path.read_text(encoding='utf-8')
            
            # 检查DeviceIdManager集成
            has_device_id_manager = "DeviceIdManager" in content
            has_build_standard_request = "buildStandardOtaRequest" in content
            has_chinese_logs = "开始OTA版本检查" in content
            
            self.print_result("集成 DeviceIdManager", has_device_id_manager)
            self.print_result("标准化请求方法", has_build_standard_request)
            self.print_result("中文日志信息", has_chinese_logs)
            
            # 检查请求格式改进
            has_mac_address_camel = "macAddress" in content
            has_chip_model_camel = "chipModelName" in content
            has_board_info = '"board"' in content
            
            self.print_result("驼峰命名 macAddress", has_mac_address_camel)
            self.print_result("驼峰命名 chipModelName", has_chip_model_camel)
            self.print_result("包含 board 信息", has_board_info)
            
    def verify_integration_points(self):
        """验证集成点"""
        self.print_header("验证模块集成")
        
        # 检查AppModule.kt（如果存在）
        app_module_path = self.app_src / "AppModule.kt"
        if app_module_path.exists():
            content = app_module_path.read_text(encoding='utf-8')
            
            modules_mentioned = [
                "DeviceIdManager",
                "ErrorHandler", 
                "AutoRetryManager"
            ]
            
            for module in modules_mentioned:
                is_mentioned = module in content
                self.print_result(f"AppModule 提及 {module}", is_mentioned)
        else:
            self.print_result("AppModule.kt 文件存在", False, "文件不存在，可能需要手动配置依赖注入")
            
    def generate_summary(self):
        """生成验证摘要"""
        self.print_header("验证摘要")
        
        total_checks = len(self.results)
        passed_checks = sum(1 for _, status, _ in self.results if status)
        failed_checks = total_checks - passed_checks
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"📊 总计检查项: {total_checks}")
        print(f"✅ 通过检查: {passed_checks}")
        print(f"❌ 失败检查: {failed_checks}")
        print(f"🎯 成功率: {success_rate:.1f}%")
        
        print("\n📋 需要关注的问题:")
        for check_name, status, details in self.results:
            if not status:
                print(f"❌ {check_name}")
                if details:
                    print(f"   📋 {details}")
                    
        if success_rate >= 90:
            print("\n🎉 第一阶段实施非常成功！")
        elif success_rate >= 75:
            print("\n👍 第一阶段实施基本成功，有少量问题需要修复")
        else:
            print("\n⚠️ 第一阶段实施存在较多问题，建议重新检查")
            
    def create_next_steps_guide(self):
        """创建下一步操作指南"""
        self.print_header("下一步操作指南")
        
        print("1. 🔧 编译项目")
        print("   cd xiaozhi-android")
        print("   ./gradlew assembleDebug")
        print()
        
        print("2. 🧪 运行测试")
        print("   ./gradlew test")
        print()
        
        print("3. 📱 安装到设备")
        print("   ./gradlew installDebug")
        print()
        
        print("4. 🔍 验证功能")
        print("   - 检查设备ID生成是否稳定")
        print("   - 测试OTA请求格式是否正确")
        print("   - 验证绑定引导界面显示")
        print("   - 测试错误处理和重试机制")
        print()
        
        print("5. 📝 记录测试结果")
        print("   - 更新 Work_Framework/optimization_progress_tracker.md")
        print("   - 记录发现的问题和改进建议")
        
    def run_verification(self):
        """运行完整验证"""
        print("🚀 开始第一阶段优化成果验证")
        print(f"📁 项目路径: {self.project_root}")
        
        # 验证各个组件
        self.verify_device_id_manager()
        self.verify_error_handler() 
        self.verify_retry_manager()
        self.verify_binding_dialog()
        self.verify_ota_improvements()
        self.verify_integration_points()
        
        # 生成摘要和指南
        self.generate_summary()
        self.create_next_steps_guide()

def main():
    """主函数"""
    # 获取项目根目录
    current_dir = Path(__file__).parent.parent
    
    print("📋 第一阶段优化成果验证脚本")
    print("用于检查已实施的功能是否正确集成到项目中")
    
    verifier = Phase1Verifier(current_dir)
    verifier.run_verification()
    
    print("\n✨ 验证完成！")

if __name__ == "__main__":
    main() 