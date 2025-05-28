#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度APK闪退分析工具
分析Android应用启动时的各种潜在问题
"""

import os
import re
import subprocess
from pathlib import Path

def check_compilation_errors():
    """检查编译错误"""
    print("🔍 检查编译状态")
    print("=" * 50)
    
    try:
        # 尝试编译 - 修复路径问题
        result = subprocess.run(
            ["./gradlew", "assembleDebug", "--stacktrace"],
            cwd="..",  # 从父目录运行
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("  ✅ 编译成功")
            return True
        else:
            print("  ❌ 编译失败")
            print("  错误输出:")
            print(result.stderr)
            print("  标准输出:")
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("  ⏰ 编译超时")
        return False
    except Exception as e:
        print(f"  💥 编译检查异常: {e}")
        return False

def analyze_hilt_dependencies():
    """分析Hilt依赖注入问题"""
    print("\n🔧 分析Hilt依赖注入")
    print("=" * 50)
    
    issues = []
    
    # 检查Application类
    app_file = "../app/src/main/java/info/dourok/voicebot/VApplication.kt"
    if os.path.exists(app_file):
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@HiltAndroidApp' not in content:
            issues.append("VApplication缺少@HiltAndroidApp注解")
        
        if 'lateinit var deviceIdManager: DeviceIdManager' in content:
            if '@Inject' not in content:
                issues.append("VApplication中的deviceIdManager缺少@Inject注解")
    
    # 检查MainActivity
    main_file = "../app/src/main/java/info/dourok/voicebot/MainActivity.kt"
    if os.path.exists(main_file):
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@AndroidEntryPoint' not in content:
            issues.append("MainActivity缺少@AndroidEntryPoint注解")
    
    # 检查AppModule
    module_file = "../app/src/main/java/info/dourok/voicebot/AppModule.kt"
    if os.path.exists(module_file):
        with open(module_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@Module' not in content or '@InstallIn(SingletonComponent::class)' not in content:
            issues.append("AppModule配置不正确")
        
        # 检查DeviceIdManager的提供方法
        if 'fun provideDeviceIdManager' not in content:
            issues.append("AppModule缺少DeviceIdManager的提供方法")
    
    if issues:
        print("  发现Hilt问题:")
        for issue in issues:
            print(f"    ❌ {issue}")
        return False
    else:
        print("  ✅ Hilt配置正常")
        return True

def check_datastore_usage():
    """检查DataStore使用问题"""
    print("\n💾 检查DataStore使用")
    print("=" * 50)
    
    issues = []
    
    # 检查DeviceIdManager
    device_id_file = "../app/src/main/java/info/dourok/voicebot/data/model/DeviceIdManager.kt"
    if os.path.exists(device_id_file):
        with open(device_id_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否在构造函数中使用了DataStore
        if 'init {' in content and 'dataStore' in content:
            issues.append("DeviceIdManager在init块中使用DataStore")
        
        # 检查是否有阻塞调用
        if '.first()' in content and 'suspend' not in content.split('.first()')[0].split('\n')[-1]:
            issues.append("DeviceIdManager中可能存在非suspend函数中的阻塞调用")
    
    # 检查DeviceConfigManager
    config_file = "../app/src/main/java/info/dourok/voicebot/config/DeviceConfigManager.kt"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'dataStore.data.first()' in content:
            # 检查是否在非suspend函数中调用
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'dataStore.data.first()' in line:
                    # 向上查找函数定义
                    for j in range(i, max(0, i-10), -1):
                        if 'fun ' in lines[j] and 'suspend' not in lines[j]:
                            issues.append(f"DeviceConfigManager在非suspend函数中使用阻塞调用: {lines[j].strip()}")
                            break
    
    if issues:
        print("  发现DataStore问题:")
        for issue in issues:
            print(f"    ❌ {issue}")
        return False
    else:
        print("  ✅ DataStore使用正常")
        return True

def check_viewmodel_initialization():
    """检查ViewModel初始化问题"""
    print("\n🎭 检查ViewModel初始化")
    print("=" * 50)
    
    issues = []
    
    # 检查ChatViewModel
    chat_vm_file = "../app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt"
    if os.path.exists(chat_vm_file):
        with open(chat_vm_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查构造函数中的复杂操作
        if 'init {' in content:
            init_block = content.split('init {')[1].split('}')[0]
            if len(init_block.strip()) > 100:  # 如果init块太长
                issues.append("ChatViewModel的init块过于复杂")
            
            if 'viewModelScope.launch' in init_block:
                issues.append("ChatViewModel在init块中启动协程")
    
    # 检查SmartBindingViewModel
    binding_vm_file = "../app/src/main/java/info/dourok/voicebot/ui/SmartBindingViewModel.kt"
    if os.path.exists(binding_vm_file):
        with open(binding_vm_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'init {' in content:
            init_block = content.split('init {')[1].split('}')[0]
            if 'suspend' in init_block or 'launch' in init_block:
                issues.append("SmartBindingViewModel在init块中执行异步操作")
    
    if issues:
        print("  发现ViewModel问题:")
        for issue in issues:
            print(f"    ❌ {issue}")
        return False
    else:
        print("  ✅ ViewModel初始化正常")
        return True

def check_compose_issues():
    """检查Compose相关问题"""
    print("\n🎨 检查Compose问题")
    print("=" * 50)
    
    issues = []
    
    # 检查MainActivity
    main_file = "../app/src/main/java/info/dourok/voicebot/MainActivity.kt"
    if os.path.exists(main_file):
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查setContent调用
        if 'setContent {' not in content:
            issues.append("MainActivity缺少setContent调用")
        
        # 检查是否有循环依赖的Composable调用
        if content.count('@Composable') > 10:  # 如果有太多Composable函数
            print("  ⚠️ MainActivity中有大量Composable函数，可能存在循环依赖")
    
    # 检查是否有未处理的Composable异常
    compose_files = [
        "../app/src/main/java/info/dourok/voicebot/ui/ChatScreen.kt",
        "../app/src/main/java/info/dourok/voicebot/ui/config/DeviceConfigScreen.kt"
    ]
    
    for file_path in compose_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查hiltViewModel调用
            if 'hiltViewModel()' in content and '@Composable' in content:
                # 检查是否在LaunchedEffect中调用
                if 'LaunchedEffect' in content and 'hiltViewModel()' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'hiltViewModel()' in line:
                            # 检查前后几行是否在LaunchedEffect中
                            context_lines = lines[max(0, i-5):i+5]
                            context = '\n'.join(context_lines)
                            if 'LaunchedEffect' not in context:
                                continue  # 这个调用不在LaunchedEffect中，是正常的
    
    if issues:
        print("  发现Compose问题:")
        for issue in issues:
            print(f"    ❌ {issue}")
        return False
    else:
        print("  ✅ Compose配置正常")
        return True

def check_manifest_and_permissions():
    """检查Manifest和权限配置"""
    print("\n📋 检查Manifest和权限")
    print("=" * 50)
    
    issues = []
    
    manifest_file = "../app/src/main/AndroidManifest.xml"
    if os.path.exists(manifest_file):
        with open(manifest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查Application类配置
        if 'android:name=".VApplication"' not in content:
            issues.append("Manifest中Application类配置错误")
        
        # 检查必要权限
        required_permissions = [
            "android.permission.INTERNET",
            "android.permission.RECORD_AUDIO"
        ]
        
        for permission in required_permissions:
            if permission not in content:
                issues.append(f"缺少权限: {permission}")
        
        # 检查MainActivity配置
        if 'android:name=".MainActivity"' not in content:
            issues.append("MainActivity配置错误")
        
        # 检查是否有LAUNCHER intent
        if 'android.intent.action.MAIN' not in content or 'android.intent.category.LAUNCHER' not in content:
            issues.append("缺少LAUNCHER intent配置")
    else:
        issues.append("AndroidManifest.xml文件不存在")
    
    if issues:
        print("  发现Manifest问题:")
        for issue in issues:
            print(f"    ❌ {issue}")
        return False
    else:
        print("  ✅ Manifest配置正常")
        return True

def check_gradle_configuration():
    """检查Gradle配置"""
    print("\n🏗️ 检查Gradle配置")
    print("=" * 50)
    
    issues = []
    
    # 检查app/build.gradle.kts
    build_file = "../app/build.gradle.kts"
    if os.path.exists(build_file):
        with open(build_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查必要的插件
        required_plugins = [
            'id("com.google.dagger.hilt.android")',
            'id("kotlin-kapt")'
        ]
        
        for plugin in required_plugins:
            if plugin not in content:
                issues.append(f"缺少插件: {plugin}")
        
        # 检查Hilt依赖
        if 'implementation("com.google.dagger:hilt-android:' not in content:
            issues.append("缺少Hilt Android依赖")
        
        if 'kapt("com.google.dagger:hilt-compiler:' not in content:
            issues.append("缺少Hilt编译器依赖")
    else:
        issues.append("app/build.gradle.kts文件不存在")
    
    if issues:
        print("  发现Gradle问题:")
        for issue in issues:
            print(f"    ❌ {issue}")
        return False
    else:
        print("  ✅ Gradle配置正常")
        return True

def analyze_potential_circular_dependencies():
    """分析潜在的循环依赖"""
    print("\n🔄 分析循环依赖")
    print("=" * 50)
    
    # 构建依赖图
    dependencies = {}
    
    # 分析主要类的依赖关系
    files_to_check = [
        ("VApplication", "../app/src/main/java/info/dourok/voicebot/VApplication.kt"),
        ("MainActivity", "../app/src/main/java/info/dourok/voicebot/MainActivity.kt"),
        ("DeviceIdManager", "../app/src/main/java/info/dourok/voicebot/data/model/DeviceIdManager.kt"),
        ("DeviceConfigManager", "../app/src/main/java/info/dourok/voicebot/config/DeviceConfigManager.kt"),
        ("ChatViewModel", "../app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt"),
        ("SmartBindingViewModel", "../app/src/main/java/info/dourok/voicebot/ui/SmartBindingViewModel.kt"),
    ]
    
    for class_name, file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取@Inject构造函数的依赖
            inject_pattern = r'@Inject\s+constructor\s*\((.*?)\)'
            matches = re.findall(inject_pattern, content, re.DOTALL)
            
            if matches:
                params = matches[0]
                # 提取参数类型
                param_types = []
                for line in params.split('\n'):
                    line = line.strip()
                    if ':' in line and 'private' in line:
                        param_type = line.split(':')[1].strip().rstrip(',')
                        param_types.append(param_type)
                
                dependencies[class_name] = param_types
    
    # 检查循环依赖
    circular_deps = []
    for class_name, deps in dependencies.items():
        for dep in deps:
            if dep in dependencies and class_name in dependencies[dep]:
                circular_deps.append(f"{class_name} ↔ {dep}")
    
    if circular_deps:
        print("  发现循环依赖:")
        for dep in circular_deps:
            print(f"    ❌ {dep}")
        return False
    else:
        print("  ✅ 未发现明显的循环依赖")
        return True

def suggest_immediate_fixes():
    """建议立即修复方案"""
    print("\n🔧 立即修复建议")
    print("=" * 50)
    
    print("1. 🚨 紧急修复步骤:")
    print("   - 确保所有语法错误已修复")
    print("   - 检查Hilt注解是否正确")
    print("   - 验证DataStore不在主线程使用")
    print("   - 简化ViewModel构造函数")
    
    print("\n2. 🔍 调试方法:")
    print("   - 使用adb logcat查看崩溃日志")
    print("   - 在VApplication.onCreate中添加日志")
    print("   - 检查是否有未捕获的异常")
    
    print("\n3. 📱 测试步骤:")
    print("   - 重新编译APK")
    print("   - 安装到设备")
    print("   - 立即查看logcat输出")
    print("   - 记录崩溃堆栈信息")

def main():
    """主函数"""
    print("🚨 深度APK闪退分析工具")
    print("分析Android应用启动时的各种潜在问题")
    print()
    
    # 执行各项检查
    results = {
        "编译状态": check_compilation_errors(),
        "Hilt依赖注入": analyze_hilt_dependencies(),
        "DataStore使用": check_datastore_usage(),
        "ViewModel初始化": check_viewmodel_initialization(),
        "Compose配置": check_compose_issues(),
        "Manifest配置": check_manifest_and_permissions(),
        "Gradle配置": check_gradle_configuration(),
        "循环依赖": analyze_potential_circular_dependencies()
    }
    
    # 总结结果
    print("\n📊 深度分析结果")
    print("=" * 40)
    
    failed_checks = []
    for check_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            failed_checks.append(check_name)
    
    if failed_checks:
        print(f"\n⚠️ 发现 {len(failed_checks)} 个问题需要修复:")
        for check in failed_checks:
            print(f"   - {check}")
    else:
        print("\n🎉 所有检查都通过了！")
    
    suggest_immediate_fixes()
    
    print("\n🏁 深度分析完成")

if __name__ == "__main__":
    main() 