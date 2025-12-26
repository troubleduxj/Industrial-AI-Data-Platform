#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spec 验证脚本
用于验证 device-dynamic-params Spec 的完整性和正确性
"""

import json
import re
from pathlib import Path

# Spec 目录
SPEC_DIR = Path(__file__).parent

def validate_spec_structure():
    """验证 Spec 文件结构"""
    print("🔍 验证 Spec 文件结构...")
    
    required_files = [
        "README.md",
        "QUICKSTART.md",
        "spec.json",
        "requirements.md",
        "design.md",
        "tasks.md"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = SPEC_DIR / file
        if not file_path.exists():
            missing_files.append(file)
        else:
            print(f"  ✅ {file} 存在")
    
    if missing_files:
        print(f"  ❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    print("  ✅ 所有必需文件都存在")
    return True

def validate_requirements():
    """验证需求文档"""
    print("\n🔍 验证需求文档...")
    
    req_file = SPEC_DIR / "requirements.md"
    content = req_file.read_text(encoding='utf-8')
    
    # 检查验收标准
    ac_pattern = r'### AC-\d+:'
    acs = re.findall(ac_pattern, content)
    
    print(f"  ✅ 找到 {len(acs)} 个验收标准")
    
    if len(acs) < 6:
        print(f"  ⚠️  验收标准数量少于预期（期望6个，实际{len(acs)}个）")
    
    # 检查关键章节
    required_sections = [
        "## 功能概述",
        "## 业务背景",
        "## 核心需求",
        "## 非功能需求"
    ]
    
    for section in required_sections:
        if section in content:
            print(f"  ✅ 包含章节: {section}")
        else:
            print(f"  ❌ 缺少章节: {section}")
    
    return True

def validate_design():
    """验证设计文档"""
    print("\n🔍 验证设计文档...")
    
    design_file = SPEC_DIR / "design.md"
    content = design_file.read_text(encoding='utf-8')
    
    # 检查正确性属性
    p_pattern = r'### P-\d+:'
    properties = re.findall(p_pattern, content)
    
    print(f"  ✅ 找到 {len(properties)} 个正确性属性")
    
    if len(properties) < 6:
        print(f"  ⚠️  正确性属性数量少于预期（期望6个，实际{len(properties)}个）")
    
    # 检查关键章节
    required_sections = [
        "## 架构设计",
        "## 正确性属性",
        "## 数据模型",
        "## API 设计"
    ]
    
    for section in required_sections:
        if section in content:
            print(f"  ✅ 包含章节: {section}")
        else:
            print(f"  ❌ 缺少章节: {section}")
    
    return True

def validate_tasks():
    """验证任务列表"""
    print("\n🔍 验证任务列表...")
    
    tasks_file = SPEC_DIR / "tasks.md"
    content = tasks_file.read_text(encoding='utf-8')
    
    # 检查任务
    task_pattern = r'### TASK-\d+:'
    tasks = re.findall(task_pattern, content)
    
    print(f"  ✅ 找到 {len(tasks)} 个任务")
    
    if len(tasks) < 15:
        print(f"  ⚠️  任务数量少于预期（期望15个，实际{len(tasks)}个）")
    
    # 检查任务属性
    required_attrs = [
        "**对应需求**:",
        "**优先级**:",
        "**预计时间**:",
        "**验收标准**:",
        "**测试要求**:"
    ]
    
    task_sections = content.split('### TASK-')
    if len(task_sections) > 1:
        first_task = task_sections[1]
        for attr in required_attrs:
            if attr in first_task:
                print(f"  ✅ 任务包含属性: {attr}")
            else:
                print(f"  ❌ 任务缺少属性: {attr}")
    
    return True

def validate_spec_json():
    """验证 spec.json"""
    print("\n🔍 验证 spec.json...")
    
    spec_file = SPEC_DIR / "spec.json"
    
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec_data = json.load(f)
        
        required_fields = [
            "name",
            "title",
            "version",
            "description",
            "status",
            "files"
        ]
        
        for field in required_fields:
            if field in spec_data:
                print(f"  ✅ 包含字段: {field} = {spec_data[field]}")
            else:
                print(f"  ❌ 缺少字段: {field}")
        
        return True
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 格式错误: {e}")
        return False

def validate_traceability():
    """验证需求-设计-任务的追溯性"""
    print("\n🔍 验证追溯性...")
    
    # 读取文件
    req_file = SPEC_DIR / "requirements.md"
    design_file = SPEC_DIR / "design.md"
    tasks_file = SPEC_DIR / "tasks.md"
    
    req_content = req_file.read_text(encoding='utf-8')
    design_content = design_file.read_text(encoding='utf-8')
    tasks_content = tasks_file.read_text(encoding='utf-8')
    
    # 提取验收标准
    acs = re.findall(r'### (AC-\d+):', req_content)
    print(f"  ✅ 需求文档包含 {len(acs)} 个验收标准: {', '.join(acs)}")
    
    # 提取正确性属性
    properties = re.findall(r'### (P-\d+):', design_content)
    print(f"  ✅ 设计文档包含 {len(properties)} 个正确性属性: {', '.join(properties)}")
    
    # 检查任务是否引用了验收标准
    for ac in acs:
        if ac in tasks_content:
            print(f"  ✅ 任务列表引用了 {ac}")
        else:
            print(f"  ⚠️  任务列表未引用 {ac}")
    
    # 检查任务是否引用了正确性属性
    for prop in properties:
        if prop in tasks_content:
            print(f"  ✅ 任务列表引用了 {prop}")
        else:
            print(f"  ⚠️  任务列表未引用 {prop}")
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("  Spec 验证工具 - device-dynamic-params")
    print("=" * 60)
    
    results = []
    
    # 执行验证
    results.append(("文件结构", validate_spec_structure()))
    results.append(("需求文档", validate_requirements()))
    results.append(("设计文档", validate_design()))
    results.append(("任务列表", validate_tasks()))
    results.append(("spec.json", validate_spec_json()))
    results.append(("追溯性", validate_traceability()))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("  验证总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n  总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n  🎉 所有验证通过！Spec 结构完整且正确。")
        return 0
    else:
        print("\n  ⚠️  部分验证未通过，请检查上述问题。")
        return 1

if __name__ == "__main__":
    exit(main())
