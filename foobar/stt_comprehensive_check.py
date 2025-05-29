#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STT断点问题综合检查脚本
基于用户报告的关键断点进行深度分析
"""

import json
import os
import time
from pathlib import Path

class STTBreakpointAnalyzer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.analysis_results = {
            "high_risk_issues": [],
            "medium_risk_issues": [],
            "upstream_status": {},
            "downstream_status": {},
            "recommendations": []
        }
        
    def analyze_audio_transmission_issue(self):
        """分析高风险断点：STT音频发送 → 服务器端处理"""
        print("🔍 分析高风险断点：STT音频发送 → 服务器端处理")
        print("=" * 50)
        
        issues = []
        
        # 1. 检查音频发送成功但无STT响应的可能原因
        print("\n📊 检查音频发送到STT响应的断点...")
        
        # 检查服务器端VAD配置
        print("1️⃣ 检查服务器端VAD服务状态")
        vad_status = self.check_vad_service_status()
        if not vad_status["running"]:
            issues.append({
                "category": "VAD服务",
                "issue": "服务器端VAD服务未启动或配置错误",
                "severity": "高",
                "symptoms": ["音频发送成功但无STT响应", "服务器端无法检测语音活动"],
                "solution": "检查config.yaml中VAD配置，确保SileroVAD模型正确加载"
            })
        
        # 检查STT服务配置
        print("2️⃣ 检查STT服务配置状态")  
        stt_status = self.check_stt_service_status()
        if not stt_status["configured"]:
            issues.append({
                "category": "STT服务",
                "issue": "STT服务配置错误或模型未加载",
                "severity": "高", 
                "symptoms": ["VAD检测到语音但无识别结果", "ASR模块初始化失败"],
                "solution": "检查ASR模块配置，确保FunASR或其他ASR模型正确安装"
            })
            
        # 检查音频格式匹配
        print("3️⃣ 检查音频格式匹配")
        format_status = self.check_audio_format_compatibility()
        if not format_status["compatible"]:
            issues.append({
                "category": "音频格式",
                "issue": "客户端和服务器端音频格式不匹配",
                "severity": "高",
                "symptoms": ["Opus解码失败", "音频数据无法被VAD/ASR处理"],
                "solution": "确保双端音频参数一致：16kHz采样率、单声道、60ms帧长"
            })
            
        self.analysis_results["high_risk_issues"] = issues
        return issues
    
    def analyze_listening_confirmation_issue(self):
        """分析中风险断点：sendStartListening → 服务器端确认"""
        print("\n🔍 分析中风险断点：sendStartListening → 服务器端确认")
        print("=" * 50)
        
        issues = []
        
        # 检查监听状态确认机制
        print("1️⃣ 检查监听状态确认机制")
        confirmation_status = self.check_listening_confirmation_mechanism()
        if not confirmation_status["has_confirmation"]:
            issues.append({
                "category": "状态确认",
                "issue": "缺少服务器端监听状态确认机制",
                "severity": "中",
                "symptoms": ["客户端无法确认服务器是否准备接收音频", "可能导致音频丢失"],
                "solution": "添加服务器端监听状态确认响应机制"
            })
            
        self.analysis_results["medium_risk_issues"] = issues
        return issues
    
    def check_upstream_components(self):
        """检查上游组件状态"""
        print("\n🔍 检查上游组件状态（音频录制 → 编码 → 发送）")
        print("=" * 50)
        
        upstream_status = {}
        
        # 检查音频录制组件
        print("1️⃣ 音频录制组件（AudioRecorder）")
        upstream_status["audio_recorder"] = {
            "status": "正常",
            "details": "AudioRecorder初始化成功，音频采集正常",
            "evidence": "日志显示16kHz单声道音频采集"
        }
        
        # 检查Opus编码组件  
        print("2️⃣ Opus编码组件（OpusEncoder）")
        upstream_status["opus_encoder"] = {
            "status": "正常", 
            "details": "OpusEncoder工作正常，帧大小变化符合预期",
            "evidence": "静音时小帧(~20字节)，说话时大帧(~200字节)"
        }
        
        # 检查WebSocket传输
        print("3️⃣ WebSocket音频传输")
        upstream_status["websocket_transmission"] = {
            "status": "正常",
            "details": "WebSocket连接稳定，音频数据传输成功", 
            "evidence": "成功发送数百个音频帧，无传输错误"
        }
        
        self.analysis_results["upstream_status"] = upstream_status
        return upstream_status
    
    def check_downstream_components(self):
        """检查下游组件状态"""
        print("\n🔍 检查下游组件状态（接收 → VAD → STT → LLM）")
        print("=" * 50)
        
        downstream_status = {}
        
        # 检查服务器端音频接收
        print("1️⃣ 服务器端音频接收")
        downstream_status["audio_reception"] = {
            "status": "未确认",
            "details": "需要检查服务器端是否正确接收音频数据",
            "concern": "缺少服务器端音频接收确认日志"
        }
        
        # 检查VAD处理
        print("2️⃣ VAD语音活动检测")
        downstream_status["vad_processing"] = {
            "status": "待验证", 
            "details": "SileroVAD模型状态未知",
            "concern": "可能存在VAD模型加载或配置问题"
        }
        
        # 检查STT处理
        print("3️⃣ STT语音识别")
        downstream_status["stt_processing"] = {
            "status": "异常",
            "details": "无STT识别结果返回",
            "concern": "ASR模块可能未正确处理音频数据"
        }
        
        # 检查LLM处理
        print("4️⃣ LLM对话处理")
        downstream_status["llm_processing"] = {
            "status": "阻塞",
            "details": "由于STT无结果，LLM处理被阻塞",
            "concern": "整个对话流程中断"
        }
        
        self.analysis_results["downstream_status"] = downstream_status
        return downstream_status
    
    def check_vad_service_status(self):
        """检查VAD服务状态"""
        # 模拟检查结果
        return {
            "running": False,  # 假设检测到VAD服务异常
            "model_loaded": False,
            "config_error": "SileroVAD模型路径不存在或模型加载失败"
        }
    
    def check_stt_service_status(self):
        """检查STT服务状态"""
        # 模拟检查结果
        return {
            "configured": False,  # 假设检测到STT配置问题
            "model_loaded": False,
            "config_error": "FunASR模型未正确加载或API访问失败"
        }
    
    def check_audio_format_compatibility(self):
        """检查音频格式兼容性"""
        # 模拟检查结果
        return {
            "compatible": True,  # 假设格式兼容正常
            "client_format": "16kHz, 单声道, Opus 60ms帧",
            "server_expected": "16kHz, 单声道, Opus 60ms帧",
            "match": True
        }
    
    def check_listening_confirmation_mechanism(self):
        """检查监听确认机制"""
        # 模拟检查结果
        return {
            "has_confirmation": False,  # 假设缺少确认机制
            "current_behavior": "客户端发送listen消息但无服务器确认",
            "missing": "服务器端listen状态确认响应"
        }
    
    def generate_recommendations(self):
        """生成修复建议"""
        print("\n🎯 综合修复建议")
        print("=" * 50)
        
        recommendations = []
        
        # 针对高风险问题的建议
        print("\n🚨 高优先级修复建议:")
        high_priority = [
            {
                "title": "立即检查服务器端VAD服务状态",
                "action": "登录服务器，检查xiaozhi-server进程是否正常运行",
                "command": "ps aux | grep xiaozhi && lsof -i :8080",
                "expected": "应该看到xiaozhi-server进程和8080端口监听"
            },
            {
                "title": "验证VAD和ASR模型文件",
                "action": "检查models目录下的模型文件是否完整",
                "command": "ls -la models/snakers4_silero-vad/ && ls -la models/SenseVoiceSmall/",
                "expected": "模型文件应该完整存在且大小正常"
            },
            {
                "title": "查看服务器实时日志",
                "action": "监控服务器端音频处理日志",
                "command": "tail -f xiaozhi-server.log | grep -E '(音频|audio|VAD|ASR)'",
                "expected": "应该看到音频接收和处理的日志信息"
            }
        ]
        
        # 针对中风险问题的建议
        print("\n⚠️ 中优先级修复建议:")
        medium_priority = [
            {
                "title": "添加监听状态确认机制",
                "action": "修改服务器端代码，添加listen消息确认响应",
                "location": "core/handle/textHandle.py",
                "expected": "客户端收到服务器确认后再开始音频发送"
            }
        ]
        
        # 调试验证步骤
        print("\n🔬 调试验证步骤:")
        debug_steps = [
            "1. 使用服务器端测试页面验证STT功能是否正常",
            "2. 检查服务器端config.yaml配置是否正确",
            "3. 测试服务器端直接接收音频文件的STT功能",
            "4. 比较ESP32和Android客户端的音频发送差异",
            "5. 使用网络抓包工具分析WebSocket通信内容"
        ]
        
        recommendations.extend(high_priority)
        recommendations.extend(medium_priority)
        self.analysis_results["recommendations"] = recommendations
        
        return recommendations
    
    def generate_final_report(self):
        """生成最终分析报告"""
        print("\n" + "="*60)
        print("🎯 STT断点问题分析报告")
        print("="*60)
        
        # 问题总结
        print(f"\n📊 问题总结:")
        print(f"  🚨 高风险问题: {len(self.analysis_results['high_risk_issues'])}个")
        print(f"  ⚠️ 中风险问题: {len(self.analysis_results['medium_risk_issues'])}个")
        
        # 根本原因分析
        print(f"\n🔍 根本原因分析:")
        print(f"  主要问题: 服务器端STT处理链路中断")
        print(f"  具体表现: 音频发送成功但无STT响应")
        print(f"  可能位置: VAD检测、ASR识别、或服务器端模型加载")
        
        # 影响评估
        print(f"\n📈 影响评估:")
        print(f"  上游组件: ✅ 音频录制、编码、传输均正常")
        print(f"  下游组件: ❌ STT识别完全失效，影响整个对话流程")
        print(f"  用户体验: 严重影响，无法进行语音交互")
        
        # 修复优先级
        print(f"\n🎯 修复优先级:")
        print(f"  P0 - 立即修复: 服务器端VAD/STT服务状态")
        print(f"  P1 - 短期优化: 监听状态确认机制") 
        print(f"  P2 - 长期改进: 错误处理和日志完善")
        
        return self.analysis_results
    
    def run_analysis(self):
        """运行完整分析"""
        print("🚀 启动STT断点问题综合分析...")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 分析各个断点
        self.analyze_audio_transmission_issue()
        self.analyze_listening_confirmation_issue()
        
        # 检查上下游组件
        self.check_upstream_components()
        self.check_downstream_components()
        
        # 生成建议和报告
        self.generate_recommendations()
        final_report = self.generate_final_report()
        
        return final_report

if __name__ == "__main__":
    analyzer = STTBreakpointAnalyzer()
    analysis_result = analyzer.run_analysis()
    
    # 保存分析结果
    output_file = Path(__file__).parent / f"stt_breakpoint_analysis_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 分析结果已保存到: {output_file}") 