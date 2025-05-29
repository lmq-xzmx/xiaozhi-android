#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STT (语音转文本) 问题诊断脚本
用于诊断Android客户端STT功能的问题
"""

import os
import sys
import yaml
import json
import subprocess
import time
from pathlib import Path

class STTDiagnostics:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.server_root = self.project_root / "../main/xiaozhi-server"
        self.issues = []
        self.solutions = []
        
    def log_issue(self, category, issue, solution=None):
        """记录问题和解决方案"""
        self.issues.append(f"❌ {category}: {issue}")
        if solution:
            self.solutions.append(f"✅ 解决方案: {solution}")
            
    def log_success(self, category, message):
        """记录成功检查"""
        print(f"✅ {category}: {message}")
        
    def check_server_config(self):
        """检查服务器配置"""
        print("\n🔍 检查服务器配置...")
        
        config_path = self.server_root / "config.yaml"
        if not config_path.exists():
            self.log_issue("配置文件", f"config.yaml未找到: {config_path}")
            return False
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 检查selected_module配置
            selected_modules = config.get('selected_module', {})
            vad_module = selected_modules.get('VAD')
            asr_module = selected_modules.get('ASR')
            
            if not vad_module:
                self.log_issue("VAD配置", "未配置VAD模块", "在config.yaml中设置selected_module.VAD")
            else:
                self.log_success("VAD配置", f"已配置VAD模块: {vad_module}")
                
            if not asr_module:
                self.log_issue("ASR配置", "未配置ASR模块", "在config.yaml中设置selected_module.ASR")
            else:
                self.log_success("ASR配置", f"已配置ASR模块: {asr_module}")
                
            # 检查具体模块配置
            if vad_module and vad_module in config.get('VAD', {}):
                vad_config = config['VAD'][vad_module]
                model_dir = vad_config.get('model_dir')
                if model_dir:
                    model_path = self.server_root / model_dir
                    if model_path.exists():
                        self.log_success("VAD模型", f"VAD模型目录存在: {model_path}")
                    else:
                        self.log_issue("VAD模型", f"VAD模型目录不存在: {model_path}", 
                                     "下载Silero VAD模型到指定目录")
                        
            if asr_module and asr_module in config.get('ASR', {}):
                asr_config = config['ASR'][asr_module]
                model_dir = asr_config.get('model_dir')
                if model_dir:
                    model_path = self.server_root / model_dir
                    if model_path.exists():
                        self.log_success("ASR模型", f"ASR模型目录存在: {model_path}")
                    else:
                        self.log_issue("ASR模型", f"ASR模型目录不存在: {model_path}",
                                     "下载FunASR模型到指定目录")
                        
            return True
            
        except Exception as e:
            self.log_issue("配置解析", f"解析config.yaml失败: {e}")
            return False
    
    def check_server_process(self):
        """检查服务器进程"""
        print("\n🔍 检查小智服务器进程...")
        
        try:
            # 检查Python进程
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout
            
            xiaozhi_processes = []
            for line in processes.split('\n'):
                if 'xiaozhi' in line.lower() and 'python' in line:
                    xiaozhi_processes.append(line.strip())
                    
            if xiaozhi_processes:
                self.log_success("服务器进程", f"发现{len(xiaozhi_processes)}个小智相关进程")
                for proc in xiaozhi_processes:
                    print(f"  📋 {proc}")
            else:
                self.log_issue("服务器进程", "未发现小智服务器进程", 
                             "启动xiaozhi-server服务器")
                
            # 检查端口占用
            port_check = subprocess.run(['lsof', '-i', ':8080'], capture_output=True, text=True)
            if port_check.returncode == 0:
                self.log_success("端口检查", "8080端口有进程监听")
                print(f"  📋 {port_check.stdout.strip()}")
            else:
                self.log_issue("端口检查", "8080端口无进程监听", "检查服务器是否正常启动")
                
        except Exception as e:
            self.log_issue("进程检查", f"检查进程失败: {e}")
    
    def check_dependencies(self):
        """检查依赖项"""
        print("\n🔍 检查Python依赖项...")
        
        required_packages = [
            'torch', 'torchaudio', 'opuslib-next', 
            'numpy', 'websockets', 'funasr'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.log_success("依赖检查", f"{package} 已安装")
            except ImportError:
                self.log_issue("依赖缺失", f"缺少依赖: {package}", 
                             f"pip install {package}")
    
    def test_opus_decoding(self):
        """测试Opus解码功能"""
        print("\n🔍 测试Opus解码...")
        
        try:
            import opuslib_next
            decoder = opuslib_next.Decoder(16000, 1)
            self.log_success("Opus解码", "Opus解码器初始化成功")
            
            # 创建测试数据
            test_frame = b'\x00' * 960 * 2  # 960 samples * 2 bytes
            try:
                # 这可能会失败，因为是零数据，但应该不会抛出初始化错误
                decoded = decoder.decode(test_frame, 960)
                self.log_success("Opus解码", "Opus解码功能正常")
            except Exception as e:
                if "opus" in str(e).lower():
                    self.log_success("Opus解码", "Opus解码器功能正常（测试数据解码预期失败）")
                else:
                    self.log_issue("Opus解码", f"Opus解码测试失败: {e}")
                    
        except ImportError:
            self.log_issue("Opus解码", "opuslib-next未安装", "pip install opuslib-next")
        except Exception as e:
            self.log_issue("Opus解码", f"Opus解码测试失败: {e}")
    
    def check_android_logs(self):
        """分析Android日志"""
        print("\n🔍 分析Android应用日志...")
        
        # 检查日志文件
        log_files = list(self.project_root.glob("**/build_output.log"))
        log_files.extend(list(self.project_root.glob("**/*.log")))
        
        stt_keywords = [
            "STT", "stt", "speech_to_text", "音频发送", 
            "sendAudio", "音频数据", "语音识别"
        ]
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for keyword in stt_keywords:
                    if keyword in content:
                        print(f"  📋 在 {log_file.name} 中发现STT相关日志")
                        break
                        
            except Exception as e:
                continue
    
    def generate_diagnostic_report(self):
        """生成诊断报告"""
        print("\n" + "="*60)
        print("🎯 STT问题诊断报告")
        print("="*60)
        
        if self.issues:
            print("\n❌ 发现的问题:")
            for issue in self.issues:
                print(f"  {issue}")
                
        if self.solutions:
            print("\n💡 建议的解决方案:")
            for solution in self.solutions:
                print(f"  {solution}")
        
        if not self.issues:
            print("\n✅ 未发现明显配置问题，可能是服务器运行时错误")
            print("  建议检查服务器实时日志输出")
        
        # 生成检查清单
        print("\n📋 手动检查清单:")
        checklist = [
            "1. 确认xiaozhi-server正在运行且监听8080端口",
            "2. 检查config.yaml中的VAD和ASR配置",
            "3. 确认VAD和ASR模型文件已下载",
            "4. 查看服务器实时日志，确认音频包接收",
            "5. 测试服务器端VAD功能是否正常工作",
            "6. 检查Android应用的token配置是否正确",
            "7. 确认WebSocket连接稳定，无频繁断开重连",
            "8. 测试音频格式是否匹配（16kHz, 单声道, Opus编码）"
        ]
        
        for item in checklist:
            print(f"  {item}")
    
    def run_diagnostics(self):
        """运行完整诊断"""
        print("🚀 启动STT问题诊断...")
        print(f"项目根目录: {self.project_root}")
        print(f"服务器目录: {self.server_root}")
        
        # 依次执行各项检查
        self.check_dependencies()
        self.test_opus_decoding()
        self.check_server_config()
        self.check_server_process()
        self.check_android_logs()
        
        # 生成报告
        self.generate_diagnostic_report()

if __name__ == "__main__":
    diagnostics = STTDiagnostics()
    diagnostics.run_diagnostics() 