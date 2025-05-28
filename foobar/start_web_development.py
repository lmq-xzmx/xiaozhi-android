#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小智Web管理界面开发启动脚本
避免PowerShell问题，使用Python来管理开发环境
"""

import os
import subprocess
import sys
import json
import time
from pathlib import Path

class WebDevelopmentManager:
    def __init__(self):
        self.base_path = Path("/Users/xzmx/Downloads/my-project")
        self.web_path = self.base_path / "xiaozhi" / "main" / "manager-web"
        self.api_path = self.base_path / "xiaozhi" / "main" / "manager-api"
        
    def check_prerequisites(self):
        """检查开发环境前提条件"""
        print("🔍 检查开发环境...")
        
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                print("❌ Node.js 未安装")
                return False
        except FileNotFoundError:
            print("❌ Node.js 未找到")
            return False
            
        # 检查npm
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm: {result.stdout.strip()}")
            else:
                print("❌ npm 不可用")
                return False
        except FileNotFoundError:
            print("❌ npm 未找到")
            return False
            
        # 检查Java (用于后端API)
        try:
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Java 可用")
            else:
                print("⚠️  Java 不可用（后端API需要）")
        except FileNotFoundError:
            print("⚠️  Java 未找到（后端API需要）")
            
        return True
        
    def check_project_structure(self):
        """检查项目结构"""
        print("\n📂 检查项目结构...")
        
        if not self.web_path.exists():
            print(f"❌ Web项目目录不存在: {self.web_path}")
            return False
            
        package_json = self.web_path / "package.json"
        if not package_json.exists():
            print(f"❌ package.json不存在: {package_json}")
            return False
            
        print(f"✅ Web项目目录存在: {self.web_path}")
        print(f"✅ package.json存在")
        
        if self.api_path.exists():
            print(f"✅ API项目目录存在: {self.api_path}")
        else:
            print(f"⚠️  API项目目录不存在: {self.api_path}")
            
        return True
        
    def install_dependencies(self):
        """安装Web项目依赖"""
        print("\n📦 安装Web项目依赖...")
        
        try:
            os.chdir(self.web_path)
            print(f"📂 切换到目录: {self.web_path}")
            
            # 检查是否已安装依赖
            node_modules = self.web_path / "node_modules"
            if node_modules.exists():
                print("✅ node_modules已存在，跳过安装")
                return True
                
            print("⏳ 运行 npm install...")
            result = subprocess.run(['npm', 'install'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 依赖安装成功")
                return True
            else:
                print(f"❌ 依赖安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 安装依赖时出错: {e}")
            return False
            
    def analyze_package_json(self):
        """分析package.json配置"""
        print("\n🔍 分析项目配置...")
        
        try:
            package_json_path = self.web_path / "package.json"
            with open(package_json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            print(f"📱 项目名称: {config.get('name', 'Unknown')}")
            print(f"📝 版本: {config.get('version', 'Unknown')}")
            
            scripts = config.get('scripts', {})
            print("🛠 可用脚本:")
            for script, command in scripts.items():
                print(f"  - {script}: {command}")
                
            dependencies = config.get('dependencies', {})
            print(f"📦 生产依赖数量: {len(dependencies)}")
            
            dev_dependencies = config.get('devDependencies', {})
            print(f"🔧 开发依赖数量: {len(dev_dependencies)}")
            
        except Exception as e:
            print(f"⚠️  分析配置失败: {e}")
            
    def start_development_server(self):
        """启动开发服务器"""
        print("\n🚀 启动Web开发服务器...")
        
        try:
            os.chdir(self.web_path)
            print(f"📂 在目录中启动: {self.web_path}")
            print("⏳ 运行 npm run serve...")
            print("🌐 开发服务器将在 http://localhost:8001 启动")
            print("📝 请在浏览器中访问查看结果")
            print("⛔ 按 Ctrl+C 停止服务器")
            print("-" * 50)
            
            # 启动开发服务器
            subprocess.run(['npm', 'run', 'serve'])
            
        except KeyboardInterrupt:
            print("\n⛔ 开发服务器已停止")
        except Exception as e:
            print(f"❌ 启动服务器失败: {e}")
            
    def create_development_guide(self):
        """创建开发指南"""
        guide_path = self.base_path / "xiaozhi-android" / "foobar" / "web_dev_quick_start.md"
        
        content = """# 🚀 Web开发快速启动指南

## 当前开发状态

### ✅ 环境检查完成
- Node.js 和 npm 可用
- 项目结构正确
- 依赖安装成功

### 🌐 开发服务器
- **URL**: http://localhost:8001
- **启动命令**: `npm run serve`
- **停止**: Ctrl+C

### 📁 项目结构
```
manager-web/
├── src/
│   ├── apis/       # API接口
│   ├── components/ # Vue组件
│   ├── views/      # 页面
│   ├── router/     # 路由
│   └── store/      # 状态管理
└── package.json    # 项目配置
```

### 🔧 开发建议
1. 使用VS Code打开项目
2. 安装Vue相关插件
3. 从简单页面开始开发
4. 逐步添加功能模块

### 📋 下一步计划
1. **设备管理页面**
2. **音色管理功能** 
3. **用户权限系统**
4. **数据监控仪表板**

---
**开发环境已就绪，可以开始编码！**
"""
        
        try:
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📄 开发指南已创建: {guide_path}")
        except Exception as e:
            print(f"⚠️  创建指南失败: {e}")
            
    def run(self):
        """运行完整的启动流程"""
        print("🎯 小智Web管理界面开发启动")
        print("=" * 50)
        
        # 1. 检查前提条件
        if not self.check_prerequisites():
            print("❌ 环境检查失败，请先安装必要工具")
            return False
            
        # 2. 检查项目结构
        if not self.check_project_structure():
            print("❌ 项目结构检查失败")
            return False
            
        # 3. 分析项目配置
        self.analyze_package_json()
        
        # 4. 安装依赖
        if not self.install_dependencies():
            print("❌ 依赖安装失败")
            return False
            
        # 5. 创建开发指南
        self.create_development_guide()
        
        print("\n" + "=" * 50)
        print("🎉 Web开发环境准备完成！")
        print("🚀 是否现在启动开发服务器？")
        
        user_input = input("输入 'y' 启动，或任意键退出: ").strip().lower()
        if user_input == 'y':
            self.start_development_server()
        else:
            print("💡 稍后可以运行 'npm run serve' 启动开发服务器")
            
        return True

if __name__ == "__main__":
    manager = WebDevelopmentManager()
    manager.run() 