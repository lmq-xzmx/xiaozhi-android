#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找并替换STT完整方案
从xiaozhi-android2文件夹复制完整可用的STT方案到当前项目
"""

import os
import shutil
import subprocess
from pathlib import Path

class SttSolutionReplacer:
    def __init__(self):
        self.current_dir = Path("/Users/xzmx/Downloads/my-project/xiaozhi-android")
        self.source_dir = None
        self.backup_dir = self.current_dir / "foobar" / "backup_current_solution"
        
    def find_source_directory(self):
        """查找源STT方案目录"""
        possible_paths = [
            Path("/Users/xzmx/Downloads/my-project/xiaozhi-android2/xiaozhi-android"),
            Path("/Users/xzmx/Downloads/my-project/xiaozhi-android2"),
            Path("/Users/xzmx/Downloads/xiaozhi-android2/xiaozhi-android"),
            Path("/Users/xzmx/Downloads/xiaozhi-android2"),
            Path("/Users/xzmx/xiaozhi-android2/xiaozhi-android"),
            Path("/Users/xzmx/xiaozhi-android2")
        ]
        
        print("🔍 搜索STT完整方案源目录...")
        for path in possible_paths:
            print(f"   检查: {path}")
            if path.exists() and path.is_dir():
                # 检查是否包含Android项目结构
                if (path / "app" / "src").exists():
                    print(f"   ✅ 找到Android项目: {path}")
                    self.source_dir = path
                    return True
                else:
                    print(f"   ⚠️ 目录存在但不是Android项目")
            else:
                print(f"   ❌ 目录不存在")
        
        print("❌ 未找到STT完整方案源目录")
        return False
    
    def backup_current_solution(self):
        """备份当前方案"""
        print("💾 备份当前方案...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份关键文件和目录
        backup_items = [
            "app/src/main/java",
            "app/src/main/res", 
            "app/src/main/cpp",
            "app/build.gradle.kts",
            "build.gradle.kts",
            "settings.gradle.kts",
            "gradle.properties"
        ]
        
        for item in backup_items:
            source_path = self.current_dir / item
            if source_path.exists():
                dest_path = self.backup_dir / item
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(source_path, dest_path)
                
                print(f"   ✅ 已备份: {item}")
            else:
                print(f"   ⚠️ 未找到: {item}")
        
        print("✅ 当前方案备份完成")
    
    def compare_solutions(self):
        """比较两个方案的差异"""
        print("🔍 比较当前方案与源方案差异...")
        
        if not self.source_dir:
            print("❌ 源目录未找到，跳过比较")
            return
        
        # 比较关键文件
        compare_files = [
            "app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt",
            "app/src/main/java/info/dourok/voicebot/ui/ChatScreen.kt",
            "app/build.gradle.kts"
        ]
        
        for file_path in compare_files:
            current_file = self.current_dir / file_path
            source_file = self.source_dir / file_path
            
            if current_file.exists() and source_file.exists():
                current_size = current_file.stat().st_size
                source_size = source_file.stat().st_size
                current_mtime = current_file.stat().st_mtime
                source_mtime = source_file.stat().st_mtime
                
                print(f"📄 {file_path}:")
                print(f"   当前: {current_size} bytes, 修改时间: {current_mtime}")
                print(f"   源文件: {source_size} bytes, 修改时间: {source_mtime}")
                
                if source_mtime > current_mtime:
                    print(f"   📈 源文件更新")
                elif current_mtime > source_mtime:
                    print(f"   📈 当前文件更新")
                else:
                    print(f"   ⚖️ 修改时间相同")
            else:
                print(f"❌ 文件不存在: {file_path}")
    
    def copy_solution(self):
        """复制完整STT方案"""
        if not self.source_dir:
            print("❌ 源目录未找到，无法复制")
            return False
        
        print("📋 复制完整STT方案...")
        
        # 复制主要目录和文件
        copy_items = [
            ("app/src/main/java", "app/src/main/java"),
            ("app/src/main/res", "app/src/main/res"),
            ("app/src/main/cpp", "app/src/main/cpp"),
            ("app/build.gradle.kts", "app/build.gradle.kts"),
            ("build.gradle.kts", "build.gradle.kts"),
            ("settings.gradle.kts", "settings.gradle.kts"),
            ("gradle.properties", "gradle.properties")
        ]
        
        for source_item, dest_item in copy_items:
            source_path = self.source_dir / source_item
            dest_path = self.current_dir / dest_item
            
            if source_path.exists():
                # 删除目标文件/目录
                if dest_path.exists():
                    if dest_path.is_dir():
                        shutil.rmtree(dest_path)
                    else:
                        dest_path.unlink()
                
                # 创建父目录
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件/目录
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
                
                print(f"   ✅ 已复制: {source_item} -> {dest_item}")
            else:
                print(f"   ⚠️ 源文件不存在: {source_item}")
        
        print("✅ STT方案复制完成")
        return True
    
    def verify_solution(self):
        """验证复制后的方案完整性"""
        print("🔍 验证复制后的方案...")
        
        # 检查关键文件是否存在
        required_files = [
            "app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt",
            "app/src/main/java/info/dourok/voicebot/ui/ChatScreen.kt",
            "app/src/main/java/info/dourok/voicebot/MainActivity.kt",
            "app/build.gradle.kts",
            "build.gradle.kts"
        ]
        
        all_exist = True
        for file_path in required_files:
            file_full_path = self.current_dir / file_path
            if file_full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ 缺失: {file_path}")
                all_exist = False
        
        if all_exist:
            print("✅ 方案完整性验证通过")
        else:
            print("❌ 方案不完整，需要手动检查")
        
        return all_exist
    
    def create_rebuild_script(self):
        """创建重新编译脚本"""
        script_content = '''#!/bin/bash
# 重新编译替换后的STT方案

echo "🚀 开始编译替换后的STT方案..."

# 清理缓存
echo "🧹 清理构建缓存..."
./gradlew clean

# 检查代码语法
echo "🔍 检查Kotlin代码语法..."
./gradlew app:compileDebugKotlin

if [ $? -eq 0 ]; then
    echo "✅ 代码语法检查通过"
else
    echo "❌ 代码语法检查失败，请检查错误信息"
    exit 1
fi

# 编译APK
echo "📦 编译调试版APK..."
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo "✅ STT完整方案编译成功！"
    echo "📱 APK位置: app/build/outputs/apk/debug/app-debug.apk"
else
    echo "❌ 编译失败，请检查错误信息"
    exit 1
fi
'''
        
        script_path = self.current_dir / "foobar" / "rebuild_stt_solution.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # 添加执行权限
        script_path.chmod(0o755)
        print(f"✅ 重编译脚本创建完成: {script_path}")
    
    def run_replacement(self):
        """执行完整的替换流程"""
        print("🎯 开始STT完整方案替换流程")
        print("=" * 60)
        
        # 1. 查找源目录
        if not self.find_source_directory():
            print("❌ 替换流程终止：未找到源目录")
            return False
        
        # 2. 比较方案
        self.compare_solutions()
        
        # 3. 备份当前方案
        self.backup_current_solution()
        
        # 4. 复制新方案
        if not self.copy_solution():
            print("❌ 替换流程失败：复制错误")
            return False
        
        # 5. 验证完整性
        if not self.verify_solution():
            print("⚠️ 替换完成但方案可能不完整")
        
        # 6. 创建重编译脚本
        self.create_rebuild_script()
        
        print("\n🎉 STT完整方案替换成功！")
        print("📝 下一步操作：")
        print("   1. 运行编译脚本：./foobar/rebuild_stt_solution.sh")
        print("   2. 检查编译结果")
        print("   3. 安装测试新APK")
        print(f"   4. 如有问题，可从备份恢复：{self.backup_dir}")
        
        return True

def main():
    """主函数"""
    replacer = SttSolutionReplacer()
    
    try:
        success = replacer.run_replacement()
        if success:
            print("\n✅ 替换流程完成")
        else:
            print("\n❌ 替换流程失败")
    except Exception as e:
        print(f"\n❌ 替换过程异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 