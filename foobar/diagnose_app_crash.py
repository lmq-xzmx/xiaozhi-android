#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断Android APK闪退问题
分析可能的启动流程问题和依赖注入配置问题
"""

import os
import re
import subprocess
from pathlib import Path

def analyze_app_structure():
    """分析应用结构"""
    print("🔍 分析Android应用结构")
    print("=" * 60)
    
    # 检查关键文件
    key_files = [
        "app/src/main/AndroidManifest.xml",
        "app/src/main/java/info/dourok/voicebot/VApplication.kt",
        "app/src/main/java/info/dourok/voicebot/MainActivity.kt",
        "app/src/main/java/info/dourok/voicebot/AppModule.kt",
        "app/build.gradle.kts"
    ]
    
    print("📁 关键文件检查:")
    for file_path in key_files:
        full_path = f"../{file_path}"
        if os.path.exists(full_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - 文件缺失!")
    
    return True

def check_manifest_configuration():
    """检查AndroidManifest.xml配置"""
    print("\n📋 AndroidManifest.xml配置检查:")
    
    manifest_path = "../app/src/main/AndroidManifest.xml"
    if not os.path.exists(manifest_path):
        print("  ❌ AndroidManifest.xml文件不存在")
        return False
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查Application类配置
    if 'android:name=".VApplication"' in content:
        print("  ✅ Application类配置正确")
    else:
        print("  ❌ Application类配置错误或缺失")
        return False
    
    # 检查权限
    required_permissions = [
        "android.permission.INTERNET",
        "android.permission.RECORD_AUDIO",
        "android.permission.MODIFY_AUDIO_SETTINGS"
    ]
    
    for permission in required_permissions:
        if permission in content:
            print(f"  ✅ 权限 {permission}")
        else:
            print(f"  ❌ 缺少权限 {permission}")
    
    # 检查MainActivity配置
    if 'android:name=".MainActivity"' in content:
        print("  ✅ MainActivity配置正确")
    else:
        print("  ❌ MainActivity配置错误")
        return False
    
    return True

def check_hilt_configuration():
    """检查Hilt依赖注入配置"""
    print("\n🔧 Hilt依赖注入配置检查:")
    
    # 检查VApplication
    app_path = "../app/src/main/java/info/dourok/voicebot/VApplication.kt"
    if os.path.exists(app_path):
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@HiltAndroidApp' in content:
            print("  ✅ VApplication有@HiltAndroidApp注解")
        else:
            print("  ❌ VApplication缺少@HiltAndroidApp注解")
            return False
    else:
        print("  ❌ VApplication.kt文件不存在")
        return False
    
    # 检查MainActivity
    main_path = "../app/src/main/java/info/dourok/voicebot/MainActivity.kt"
    if os.path.exists(main_path):
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@AndroidEntryPoint' in content:
            print("  ✅ MainActivity有@AndroidEntryPoint注解")
        else:
            print("  ❌ MainActivity缺少@AndroidEntryPoint注解")
            return False
    else:
        print("  ❌ MainActivity.kt文件不存在")
        return False
    
    # 检查AppModule
    module_path = "../app/src/main/java/info/dourok/voicebot/AppModule.kt"
    if os.path.exists(module_path):
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@Module' in content and '@InstallIn(SingletonComponent::class)' in content:
            print("  ✅ AppModule配置正确")
        else:
            print("  ❌ AppModule配置错误")
            return False
    else:
        print("  ❌ AppModule.kt文件不存在")
        return False
    
    return True

def check_build_configuration():
    """检查构建配置"""
    print("\n🏗️ 构建配置检查:")
    
    build_path = "../app/build.gradle.kts"
    if not os.path.exists(build_path):
        print("  ❌ build.gradle.kts文件不存在")
        return False
    
    with open(build_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查Hilt插件
    if 'id("com.google.dagger.hilt.android")' in content:
        print("  ✅ Hilt插件配置正确")
    else:
        print("  ❌ 缺少Hilt插件")
        return False
    
    # 检查kapt插件
    if 'id("kotlin-kapt")' in content:
        print("  ✅ kapt插件配置正确")
    else:
        print("  ❌ 缺少kapt插件")
        return False
    
    return True

def analyze_startup_flow():
    """分析启动流程"""
    print("\n🚀 启动流程分析:")
    
    # 检查MainActivity的onCreate
    main_path = "../app/src/main/java/info/dourok/voicebot/MainActivity.kt"
    if os.path.exists(main_path):
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有复杂的初始化逻辑
        if 'SmartAppNavigation()' in content:
            print("  ✅ 使用SmartAppNavigation组件")
        else:
            print("  ❌ 缺少导航组件")
        
        # 检查权限请求
        if 'ActivityCompat.requestPermissions' in content:
            print("  ✅ 包含权限请求逻辑")
        else:
            print("  ⚠️ 缺少权限请求逻辑")
    
    # 检查SmartBindingViewModel的初始化
    binding_vm_path = "../app/src/main/java/info/dourok/voicebot/ui/SmartBindingViewModel.kt"
    if os.path.exists(binding_vm_path):
        with open(binding_vm_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'initializeDeviceBinding()' in content:
            print("  ✅ SmartBindingViewModel有初始化方法")
        else:
            print("  ❌ SmartBindingViewModel缺少初始化方法")
    
    return True

def check_potential_crash_causes():
    """检查潜在的闪退原因"""
    print("\n💥 潜在闪退原因分析:")
    
    potential_issues = []
    
    # 1. 检查DeviceIdManager的DataStore使用
    device_id_path = "../app/src/main/java/info/dourok/voicebot/data/model/DeviceIdManager.kt"
    if os.path.exists(device_id_path):
        with open(device_id_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'dataStore.data.first()' in content:
            potential_issues.append("DeviceIdManager在主线程使用了阻塞的DataStore操作")
    
    # 2. 检查ChatViewModel的初始化
    chat_vm_path = "../app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt"
    if os.path.exists(chat_vm_path):
        with open(chat_vm_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'init {' in content and 'performInitialization()' in content:
            potential_issues.append("ChatViewModel在构造函数中执行了复杂初始化")
    
    # 3. 检查Ota类的依赖注入
    ota_path = "../app/src/main/java/info/dourok/voicebot/Ota.kt"
    if os.path.exists(ota_path):
        with open(ota_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@Inject constructor(' in content:
            # 检查是否有循环依赖
            if 'deviceConfigManager' in content and 'settingsRepository' in content:
                potential_issues.append("Ota类可能存在复杂的依赖关系")
    
    # 4. 检查SmartBindingManager的初始化
    smart_binding_path = "../app/src/main/java/info/dourok/voicebot/binding/SmartBindingManager.kt"
    if os.path.exists(smart_binding_path):
        with open(smart_binding_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'initializeDeviceBinding()' in content and 'suspend fun' in content:
            potential_issues.append("SmartBindingManager在启动时执行了suspend函数")
    
    if potential_issues:
        print("  发现潜在问题:")
        for i, issue in enumerate(potential_issues, 1):
            print(f"    {i}. {issue}")
    else:
        print("  ✅ 未发现明显的潜在问题")
    
    return potential_issues

def suggest_fixes():
    """建议修复方案"""
    print("\n🔧 建议修复方案:")
    
    fixes = [
        "1. 移除ViewModel构造函数中的复杂初始化逻辑",
        "2. 将DataStore操作移到suspend函数中",
        "3. 简化应用启动流程，延迟非关键初始化",
        "4. 添加异常捕获和日志记录",
        "5. 检查依赖注入的循环依赖问题",
        "6. 确保所有网络操作在后台线程执行"
    ]
    
    for fix in fixes:
        print(f"  💡 {fix}")
    
    print("\n🎯 立即执行的修复:")
    print("  1. 修改ChatViewModel，移除构造函数中的初始化")
    print("  2. 修改DeviceIdManager，避免在主线程阻塞")
    print("  3. 简化MainActivity的启动逻辑")
    print("  4. 添加全局异常处理")

def main():
    """主函数"""
    print("🚨 Android APK闪退诊断工具")
    print("分析启动流程和依赖注入配置问题")
    print()
    
    # 执行各项检查
    structure_ok = analyze_app_structure()
    manifest_ok = check_manifest_configuration()
    hilt_ok = check_hilt_configuration()
    build_ok = check_build_configuration()
    startup_ok = analyze_startup_flow()
    potential_issues = check_potential_crash_causes()
    
    # 总结
    print("\n📊 诊断结果总结")
    print("=" * 40)
    print(f"应用结构: {'✅' if structure_ok else '❌'}")
    print(f"Manifest配置: {'✅' if manifest_ok else '❌'}")
    print(f"Hilt配置: {'✅' if hilt_ok else '❌'}")
    print(f"构建配置: {'✅' if build_ok else '❌'}")
    print(f"启动流程: {'✅' if startup_ok else '❌'}")
    print(f"潜在问题: {len(potential_issues)}个")
    
    if all([structure_ok, manifest_ok, hilt_ok, build_ok, startup_ok]) and not potential_issues:
        print("\n🎉 配置检查通过，问题可能在运行时逻辑")
    else:
        print("\n⚠️ 发现配置问题，需要修复")
    
    suggest_fixes()
    
    print("\n🏁 诊断完成")

if __name__ == "__main__":
    main() 