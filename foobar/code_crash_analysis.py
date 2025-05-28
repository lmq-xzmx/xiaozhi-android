#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码层面闪退分析工具
不依赖ADB，专门检查可能导致启动时闪退的代码问题
"""

import os
import re
from pathlib import Path

def check_file_exists(file_path):
    """检查文件是否存在"""
    return os.path.exists(file_path)

def read_file_safe(file_path):
    """安全读取文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  ⚠️ 读取文件失败 {file_path}: {e}")
        return None

def check_manifest_issues():
    """检查AndroidManifest.xml的常见问题"""
    print("📋 检查AndroidManifest.xml...")
    
    manifest_path = "../app/src/main/AndroidManifest.xml"
    if not check_file_exists(manifest_path):
        print("  ❌ AndroidManifest.xml文件不存在")
        return False
    
    content = read_file_safe(manifest_path)
    if not content:
        return False
    
    issues = []
    
    # 检查Application类配置
    if 'android:name=".VApplication"' not in content:
        issues.append("Application类配置可能错误")
    
    # 检查MainActivity配置
    if 'android:name=".MainActivity"' not in content:
        issues.append("MainActivity配置可能错误")
    
    # 检查LAUNCHER intent
    if 'android.intent.action.MAIN' not in content or 'android.intent.category.LAUNCHER' not in content:
        issues.append("缺少LAUNCHER intent配置")
    
    # 检查必要权限
    required_permissions = [
        "android.permission.INTERNET",
        "android.permission.RECORD_AUDIO"
    ]
    
    for permission in required_permissions:
        if permission not in content:
            issues.append(f"缺少权限: {permission}")
    
    if issues:
        print("  ❌ 发现问题:")
        for issue in issues:
            print(f"    • {issue}")
        return False
    else:
        print("  ✅ AndroidManifest.xml配置正常")
        return True

def check_application_class():
    """检查Application类的问题"""
    print("🏗️ 检查VApplication类...")
    
    app_path = "../app/src/main/java/info/dourok/voicebot/VApplication.kt"
    if not check_file_exists(app_path):
        print("  ❌ VApplication.kt文件不存在")
        return False
    
    content = read_file_safe(app_path)
    if not content:
        return False
    
    issues = []
    
    # 检查@HiltAndroidApp注解
    if '@HiltAndroidApp' not in content:
        issues.append("缺少@HiltAndroidApp注解")
    
    # 检查onCreate方法
    if 'override fun onCreate()' not in content:
        issues.append("缺少onCreate方法")
    
    # 检查是否在onCreate中有阻塞操作
    oncreate_match = re.search(r'override fun onCreate\(\)\s*\{(.*?)\}', content, re.DOTALL)
    if oncreate_match:
        oncreate_content = oncreate_match.group(1)
        
        # 检查是否有同步的DataStore操作
        if '.first()' in oncreate_content and 'suspend' not in oncreate_content:
            issues.append("onCreate中可能有阻塞的DataStore操作")
        
        # 检查是否有复杂的初始化
        if len(oncreate_content.strip()) > 500:
            issues.append("onCreate方法过于复杂")
    
    # 检查依赖注入
    if '@Inject' in content and 'lateinit var' in content:
        # 检查是否在onCreate中直接使用注入的对象
        inject_vars = re.findall(r'@Inject\s+lateinit var (\w+):', content)
        if oncreate_match:
            oncreate_content = oncreate_match.group(1)
            for var_name in inject_vars:
                if var_name in oncreate_content and 'suspend' not in oncreate_content:
                    issues.append(f"在onCreate中直接使用注入对象 {var_name}，可能导致阻塞")
    
    if issues:
        print("  ❌ 发现问题:")
        for issue in issues:
            print(f"    • {issue}")
        return False
    else:
        print("  ✅ VApplication类配置正常")
        return True

def check_main_activity():
    """检查MainActivity的问题"""
    print("🎭 检查MainActivity...")
    
    activity_path = "../app/src/main/java/info/dourok/voicebot/MainActivity.kt"
    if not check_file_exists(activity_path):
        print("  ❌ MainActivity.kt文件不存在")
        return False
    
    content = read_file_safe(activity_path)
    if not content:
        return False
    
    issues = []
    
    # 检查@AndroidEntryPoint注解
    if '@AndroidEntryPoint' not in content:
        issues.append("缺少@AndroidEntryPoint注解")
    
    # 检查onCreate方法
    if 'override fun onCreate(' not in content:
        issues.append("缺少onCreate方法")
    
    # 检查setContent调用
    if 'setContent {' not in content:
        issues.append("缺少setContent调用")
    
    # 检查是否有try-catch包装
    oncreate_match = re.search(r'override fun onCreate\([^)]*\)\s*\{(.*?)\}', content, re.DOTALL)
    if oncreate_match:
        oncreate_content = oncreate_match.group(1)
        
        # 检查是否有异常处理
        if 'try' not in oncreate_content and 'catch' not in oncreate_content:
            issues.append("onCreate方法缺少异常处理")
        
        # 检查是否有复杂的初始化
        if 'hiltViewModel()' in oncreate_content:
            issues.append("在onCreate中直接调用hiltViewModel()可能有问题")
    
    if issues:
        print("  ❌ 发现问题:")
        for issue in issues:
            print(f"    • {issue}")
        return False
    else:
        print("  ✅ MainActivity配置正常")
        return True

def check_device_id_manager():
    """检查DeviceIdManager的问题"""
    print("💾 检查DeviceIdManager...")
    
    manager_path = "../app/src/main/java/info/dourok/voicebot/data/model/DeviceIdManager.kt"
    if not check_file_exists(manager_path):
        print("  ❌ DeviceIdManager.kt文件不存在")
        return False
    
    content = read_file_safe(manager_path)
    if not content:
        return False
    
    issues = []
    
    # 检查@Singleton注解
    if '@Singleton' not in content:
        issues.append("缺少@Singleton注解")
    
    # 检查@Inject构造函数
    if '@Inject constructor' not in content:
        issues.append("缺少@Inject构造函数")
    
    # 检查是否有阻塞的DataStore调用
    functions = re.findall(r'fun (\w+)\([^)]*\)([^{]*)\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', content, re.DOTALL)
    
    for func_name, func_signature, func_body in functions:
        if 'suspend' not in func_signature and '.first()' in func_body:
            issues.append(f"函数 {func_name} 中有阻塞的DataStore调用")
    
    # 检查是否有init块
    if 'init {' in content:
        init_match = re.search(r'init\s*\{(.*?)\}', content, re.DOTALL)
        if init_match:
            init_content = init_match.group(1)
            if '.first()' in init_content or 'dataStore' in init_content:
                issues.append("init块中有DataStore操作")
    
    if issues:
        print("  ❌ 发现问题:")
        for issue in issues:
            print(f"    • {issue}")
        return False
    else:
        print("  ✅ DeviceIdManager配置正常")
        return True

def check_viewmodel_issues():
    """检查ViewModel的问题"""
    print("🎨 检查ViewModel...")
    
    # 检查SmartBindingViewModel
    vm_path = "../app/src/main/java/info/dourok/voicebot/ui/SmartBindingViewModel.kt"
    if not check_file_exists(vm_path):
        print("  ⚠️ SmartBindingViewModel.kt文件不存在")
        return True  # 不是必须的
    
    content = read_file_safe(vm_path)
    if not content:
        return True
    
    issues = []
    
    # 检查@HiltViewModel注解
    if '@HiltViewModel' not in content:
        issues.append("SmartBindingViewModel缺少@HiltViewModel注解")
    
    # 检查init块
    if 'init {' in content:
        init_match = re.search(r'init\s*\{(.*?)\}', content, re.DOTALL)
        if init_match:
            init_content = init_match.group(1)
            if 'viewModelScope.launch' in init_content:
                issues.append("SmartBindingViewModel在init块中启动协程")
            if 'suspend' in init_content:
                issues.append("SmartBindingViewModel在init块中有suspend操作")
    
    # 检查构造函数
    constructor_match = re.search(r'@Inject constructor\s*\((.*?)\)', content, re.DOTALL)
    if constructor_match:
        constructor_params = constructor_match.group(1)
        if len(constructor_params.strip()) > 200:
            issues.append("SmartBindingViewModel构造函数参数过多")
    
    if issues:
        print("  ❌ 发现问题:")
        for issue in issues:
            print(f"    • {issue}")
        return False
    else:
        print("  ✅ ViewModel配置正常")
        return True

def check_hilt_configuration():
    """检查Hilt配置"""
    print("🔧 检查Hilt配置...")
    
    # 检查AppModule
    module_path = "../app/src/main/java/info/dourok/voicebot/AppModule.kt"
    if not check_file_exists(module_path):
        print("  ⚠️ AppModule.kt文件不存在，可能使用其他配置方式")
        return True
    
    content = read_file_safe(module_path)
    if not content:
        return True
    
    issues = []
    
    # 检查@Module注解
    if '@Module' not in content:
        issues.append("AppModule缺少@Module注解")
    
    # 检查@InstallIn注解
    if '@InstallIn(SingletonComponent::class)' not in content:
        issues.append("AppModule缺少@InstallIn注解")
    
    if issues:
        print("  ❌ 发现问题:")
        for issue in issues:
            print(f"    • {issue}")
        return False
    else:
        print("  ✅ Hilt配置正常")
        return True

def check_gradle_configuration():
    """检查Gradle配置"""
    print("🏗️ 检查Gradle配置...")
    
    build_path = "../app/build.gradle.kts"
    if not check_file_exists(build_path):
        print("  ❌ build.gradle.kts文件不存在")
        return False
    
    content = read_file_safe(build_path)
    if not content:
        return False
    
    issues = []
    
    # 检查必要的插件
    required_plugins = [
        'id("kotlin-kapt")',
        'id("com.google.dagger.hilt.android")'
    ]
    
    for plugin in required_plugins:
        if plugin not in content:
            issues.append(f"缺少插件: {plugin}")
    
    # 检查Hilt依赖
    if 'hilt-android' not in content:
        issues.append("缺少Hilt Android依赖")
    
    if 'hilt-android-compiler' not in content and 'hilt.android.compiler' not in content:
        issues.append("缺少Hilt编译器依赖")
    
    # 检查kapt配置
    if 'kapt {' not in content:
        issues.append("缺少kapt配置块")
    
    if issues:
        print("  ❌ 发现问题:")
        for issue in issues:
            print(f"    • {issue}")
        return False
    else:
        print("  ✅ Gradle配置正常")
        return True

def check_common_crash_patterns():
    """检查常见的崩溃模式"""
    print("🔍 检查常见崩溃模式...")
    
    # 检查是否有循环依赖
    kotlin_files = []
    app_src = "../app/src/main/java/info/dourok/voicebot"
    
    if os.path.exists(app_src):
        for root, dirs, files in os.walk(app_src):
            for file in files:
                if file.endswith('.kt'):
                    kotlin_files.append(os.path.join(root, file))
    
    issues = []
    
    # 检查每个Kotlin文件的常见问题
    for file_path in kotlin_files[:10]:  # 只检查前10个文件，避免过长
        content = read_file_safe(file_path)
        if not content:
            continue
        
        file_name = os.path.basename(file_path)
        
        # 检查是否有未处理的lateinit var
        if 'lateinit var' in content and '@Inject' in content:
            # 检查是否在构造函数或init块中使用
            if 'init {' in content:
                init_match = re.search(r'init\s*\{(.*?)\}', content, re.DOTALL)
                if init_match:
                    init_content = init_match.group(1)
                    lateinit_vars = re.findall(r'lateinit var (\w+)', content)
                    for var_name in lateinit_vars:
                        if var_name in init_content:
                            issues.append(f"{file_name}: 在init块中使用lateinit var {var_name}")
        
        # 检查是否有阻塞的协程调用
        if 'runBlocking' in content:
            issues.append(f"{file_name}: 使用了runBlocking，可能导致主线程阻塞")
        
        # 检查是否有不安全的Context使用
        if 'Context' in content and 'Application' not in file_name:
            if re.search(r'context\.\w+\(\)', content, re.IGNORECASE):
                issues.append(f"{file_name}: 可能有不安全的Context使用")
    
    if issues:
        print("  ❌ 发现潜在问题:")
        for issue in issues[:5]:  # 只显示前5个
            print(f"    • {issue}")
        if len(issues) > 5:
            print(f"    ... 还有 {len(issues) - 5} 个问题")
        return False
    else:
        print("  ✅ 未发现明显的崩溃模式")
        return True

def suggest_immediate_fixes():
    """建议立即修复方案"""
    print("\n🔧 立即修复建议:")
    print("=" * 50)
    
    print("1. 🚨 最可能的原因:")
    print("   • Application类初始化失败")
    print("   • MainActivity onCreate异常")
    print("   • Hilt依赖注入问题")
    print("   • DataStore在主线程使用")
    
    print("\n2. 🔍 快速检查步骤:")
    print("   • 检查VApplication.onCreate是否有异常")
    print("   • 检查MainActivity.onCreate是否有try-catch")
    print("   • 确认所有@Inject字段都正确初始化")
    print("   • 检查是否有阻塞的DataStore操作")
    
    print("\n3. 🛠️ 紧急修复方案:")
    print("   • 在VApplication.onCreate中添加try-catch")
    print("   • 在MainActivity.onCreate中添加异常处理")
    print("   • 移除所有init块中的复杂操作")
    print("   • 确保DataStore操作都在suspend函数中")
    
    print("\n4. 📱 测试方法:")
    print("   • 重新构建APK")
    print("   • 在模拟器上测试")
    print("   • 使用adb logcat查看详细日志")

def main():
    """主函数"""
    print("🚨 代码层面闪退分析工具")
    print("专门检查可能导致启动时闪退的代码问题")
    print("=" * 60)
    
    # 执行各项检查
    results = {
        "AndroidManifest配置": check_manifest_issues(),
        "VApplication类": check_application_class(),
        "MainActivity": check_main_activity(),
        "DeviceIdManager": check_device_id_manager(),
        "ViewModel配置": check_viewmodel_issues(),
        "Hilt配置": check_hilt_configuration(),
        "Gradle配置": check_gradle_configuration(),
        "常见崩溃模式": check_common_crash_patterns()
    }
    
    # 总结结果
    print(f"\n📊 代码分析结果:")
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
        
        print(f"\n🎯 优先修复顺序:")
        priority_order = [
            "VApplication类",
            "MainActivity", 
            "Hilt配置",
            "DeviceIdManager",
            "AndroidManifest配置"
        ]
        
        for priority in priority_order:
            if priority in failed_checks:
                print(f"   1️⃣ {priority} (高优先级)")
                break
    else:
        print("\n🎉 代码层面检查都通过了！")
        print("问题可能在运行时环境或设备兼容性")
    
    suggest_immediate_fixes()
    
    print("\n🏁 分析完成")

if __name__ == "__main__":
    main() 