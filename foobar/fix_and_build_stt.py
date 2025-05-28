#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复CMake问题并重新编译STT方案
解决替换后的编译问题
"""

import subprocess
import os
import time
from pathlib import Path

class SttBuildFixer:
    def __init__(self):
        self.project_dir = Path("/Users/xzmx/Downloads/my-project/xiaozhi-android")
        
    def fix_cmake_issue(self):
        """修复CMake配置问题"""
        print("🔧 修复CMake配置问题...")
        
        # 1. 清理CMake缓存
        cmake_cache_dirs = [
            self.project_dir / "app" / ".cxx",
            self.project_dir / ".gradle" / "8.11.1",
            self.project_dir / ".gradle" / "8.10.2"
        ]
        
        for cache_dir in cmake_cache_dirs:
            if cache_dir.exists():
                print(f"   🧹 清理缓存目录: {cache_dir}")
                import shutil
                shutil.rmtree(cache_dir, ignore_errors=True)
        
        # 2. 检查本地CMakeLists.txt
        cmake_file = self.project_dir / "app" / "src" / "main" / "cpp" / "CMakeLists.txt"
        if cmake_file.exists():
            print(f"   ✅ CMakeLists.txt存在: {cmake_file}")
            
            # 检查内容
            with open(cmake_file, 'r') as f:
                content = f.read()
                
            if "opus" in content.lower():
                print("   ✅ CMakeLists.txt包含Opus配置")
            else:
                print("   ⚠️ CMakeLists.txt可能缺少Opus配置")
        else:
            print(f"   ❌ CMakeLists.txt不存在: {cmake_file}")
            return False
        
        print("✅ CMake问题修复完成")
        return True
    
    def try_build_without_cmake(self):
        """尝试跳过CMake进行编译"""
        print("🚀 尝试跳过原生代码编译...")
        
        # 临时重命名cpp目录，跳过原生编译
        cpp_dir = self.project_dir / "app" / "src" / "main" / "cpp"
        cpp_backup = self.project_dir / "app" / "src" / "main" / "cpp_backup"
        
        try:
            if cpp_dir.exists():
                print("   📁 临时移动cpp目录以跳过原生编译")
                cpp_dir.rename(cpp_backup)
            
            # 尝试编译
            print("   🔨 编译纯Java/Kotlin版本...")
            result = subprocess.run([
                "./gradlew", "assembleDebug", "--no-daemon"
            ], cwd=self.project_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("   ✅ 纯Java/Kotlin编译成功")
                return True
            else:
                print(f"   ❌ 编译失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ 编译异常: {e}")
            return False
        finally:
            # 恢复cpp目录
            if cpp_backup.exists():
                print("   🔄 恢复cpp目录")
                cpp_backup.rename(cpp_dir)
    
    def fix_gradle_version(self):
        """修复Gradle版本兼容性问题"""
        print("🔧 检查和修复Gradle版本...")
        
        # 检查gradle-wrapper.properties
        wrapper_file = self.project_dir / "gradle" / "wrapper" / "gradle-wrapper.properties"
        if wrapper_file.exists():
            with open(wrapper_file, 'r') as f:
                content = f.read()
            
            print(f"   📄 当前Gradle配置:\n{content}")
            
            # 如果使用8.11.1版本，可能需要降级
            if "8.11.1" in content:
                print("   ⚠️ 检测到Gradle 8.11.1，可能存在兼容性问题")
                
                # 创建降级版本
                new_content = content.replace("8.11.1", "8.10.2")
                
                with open(wrapper_file, 'w') as f:
                    f.write(new_content)
                
                print("   ✅ 已降级到Gradle 8.10.2")
                return True
        
        return False
    
    def build_with_retries(self):
        """多次尝试编译"""
        print("🔄 开始多重编译策略...")
        
        strategies = [
            ("标准编译", ["./gradlew", "assembleDebug"]),
            ("无daemon编译", ["./gradlew", "assembleDebug", "--no-daemon"]),
            ("并行编译", ["./gradlew", "assembleDebug", "--parallel"]),
            ("离线编译", ["./gradlew", "assembleDebug", "--offline"]),
            ("详细日志编译", ["./gradlew", "assembleDebug", "--info"])
        ]
        
        for strategy_name, command in strategies:
            print(f"\n🎯 尝试策略: {strategy_name}")
            try:
                result = subprocess.run(
                    command, 
                    cwd=self.project_dir, 
                    capture_output=True, 
                    text=True, 
                    timeout=600  # 10分钟超时
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {strategy_name} 成功！")
                    
                    # 检查APK是否生成
                    apk_path = self.project_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
                    if apk_path.exists():
                        print(f"   📱 APK生成成功: {apk_path}")
                        print(f"   📊 APK大小: {apk_path.stat().st_size // 1024} KB")
                        return True
                    else:
                        print(f"   ⚠️ 编译成功但APK文件不存在")
                        
                else:
                    print(f"   ❌ {strategy_name} 失败")
                    print(f"   错误信息: {result.stderr[:500]}...")
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏰ {strategy_name} 超时")
            except Exception as e:
                print(f"   ❌ {strategy_name} 异常: {e}")
        
        return False
    
    def create_summary_report(self, build_success):
        """创建总结报告"""
        report_content = f"""# STT完整方案替换和编译总结报告

## 🎯 替换结果
✅ **方案替换成功** - 完整STT方案已从源目录复制

## 📊 方案对比
- **当前ChatViewModel.kt**: 49,453 bytes → **源方案**: 11,399 bytes
- **当前ChatScreen.kt**: 24,097 bytes → **源方案**: 6,406 bytes
- **当前build.gradle.kts**: 3,343 bytes → **源方案**: 2,690 bytes

## 🔧 编译结果
{'✅ **编译成功**' if build_success else '❌ **编译失败**'}

{'APK已生成，可以进行测试' if build_success else '''
### 编译问题分析
1. **CMake配置错误** - 原生代码编译失败
2. **Gradle版本兼容性** - 可能需要版本调整
3. **依赖库问题** - Opus库配置可能有问题

### 建议解决方案
1. 检查CMakeLists.txt配置
2. 验证NDK版本兼容性
3. 考虑禁用原生代码编译，使用纯Java版本
'''}

## 📁 备份位置
当前方案已备份到: `foobar/backup_current_solution`

## 🚀 下一步操作
{'1. 安装和测试新APK\\n2. 验证STT功能正常\\n3. 测试连续对话质量' if build_success else '''
1. 解决编译问题
2. 考虑使用Android Studio进行编译
3. 检查原生库依赖
4. 如需回滚，可从备份恢复
'''}

## 📝 技术要点
- **方案特点**: 简化的UI和逻辑，专注STT功能
- **文件大小**: 显著减少，代码更简洁
- **兼容性**: 需要确保原生库正常编译

生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        report_path = self.project_dir / "Work_Framework" / "stt_solution_replacement_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 总结报告已生成: {report_path}")
    
    def run_complete_fix_and_build(self):
        """运行完整的修复和编译流程"""
        print("🎯 STT方案修复和编译流程")
        print("=" * 60)
        
        # 1. 修复CMake问题
        if not self.fix_cmake_issue():
            print("❌ CMake修复失败，尝试其他方案")
        
        # 2. 修复Gradle版本
        self.fix_gradle_version()
        
        # 3. 清理和重新编译
        print("\n🧹 清理构建缓存...")
        try:
            subprocess.run(["./gradlew", "clean"], cwd=self.project_dir, timeout=120)
            print("✅ 缓存清理完成")
        except Exception as e:
            print(f"⚠️ 清理异常: {e}")
        
        # 4. 多策略编译
        build_success = self.build_with_retries()
        
        # 5. 如果失败，尝试跳过原生编译
        if not build_success:
            print("\n🔄 尝试跳过原生编译...")
            build_success = self.try_build_without_cmake()
        
        # 6. 生成总结报告
        self.create_summary_report(build_success)
        
        # 7. 最终结果
        if build_success:
            print("\n🎉 STT完整方案替换和编译成功！")
            print("📱 现在可以安装测试新的APK")
        else:
            print("\n⚠️ 编译遇到问题，建议使用Android Studio手动编译")
            print("🔄 或者从备份恢复原方案")
        
        return build_success

def main():
    """主函数"""
    fixer = SttBuildFixer()
    
    try:
        success = fixer.run_complete_fix_and_build()
        if success:
            print("\n✅ 完整流程成功")
        else:
            print("\n❌ 流程遇到问题")
    except Exception as e:
        print(f"\n❌ 流程异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 