#!/usr/bin/env python3
"""
代码检查脚本 - 检测不安全的NULL值处理模式
自动扫描代码库中可能导致显示"None"的不安全字段访问
"""

import os
import re
import sys
from pathlib import Path

class CodeChecker:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.issues = []
        
        # 需要检查的字段模式
        self.risky_fields = [
            'inventory_name', 'fabric_name', 'outer_fabric_name', 'inner_fabric_name',
            'customer_name', 'processor_name', 'supplier_name'
        ]
        
        # 不安全的访问模式
        self.unsafe_patterns = [
            # 直接字典访问：item['field_name']
            r"(\w+)\s*\[\s*['\"]({fields})['\"]s*\]",
            # 没有默认值的.get()：item.get('field_name')
            r"(\w+)\.get\s*\(\s*['\"]({fields})['\"]s*\)",
            # 在显示逻辑中可能为None的变量
            r"(st\.write|st\.markdown|print|Paragraph)\s*\([^)]*(\w*(?:{fields})\w*)[^)]*\)"
        ]
        
        # 安全的模式（不报告这些）
        self.safe_patterns = [
            # 有默认值的.get()
            r"\.get\s*\(\s*['\"][^'\"]+['\"]s*,\s*[^)]+\)",
            # 使用or操作符
            r"\w+\s+or\s+['\"][^'\"]*['\"]",
            # 使用display_utils函数
            r"format_\w+_display\s*\(",
            # 在条件判断中
            r"if\s+.*\w+.*:",
            # 使用了安全函数的变量
            r"customer_display|processor_name|fabric_name",
            # 已经通过安全函数处理的变量
            r"(customer_display|outer_fabric|inner_fabric)\s*[,})]",
        ]
    
    def should_check_file(self, file_path):
        """判断是否需要检查该文件"""
        # 只检查Python文件
        if not file_path.suffix == '.py':
            return False
        
        # 跳过一些不需要检查的文件
        skip_patterns = [
            '__pycache__',
            '.git',
            'venv',
            'env',
            '.pytest_cache',
            'migrations',
            'code_checker.py',  # 跳过自己
            'display_utils.py'  # 跳过工具文件
        ]
        
        for pattern in skip_patterns:
            if pattern in str(file_path):
                return False
        
        return True
    
    def is_safe_variable_usage(self, lines, line_index, variable_name):
        """检查变量是否在之前的行中通过安全方式定义"""
        # 向前查找最多10行，看是否有安全的变量定义
        start_index = max(0, line_index - 10)
        for i in range(start_index, line_index):
            line = lines[i].strip()
            # 检查是否通过safe_get或format_xxx_display定义
            if (variable_name in line and 
                (re.search(r'safe_get\s*\(', line) or 
                 re.search(r'format_\w+_display\s*\(', line) or
                 re.search(rf'{variable_name}\s*=.*\s+or\s+[\'"][^\'\"]*[\'"]', line))):
                return True
        return False
    
    def is_safe_line(self, line):
        """检查是否是安全的代码行"""
        for pattern in self.safe_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def check_line_safety(self, line, line_num, file_path):
        """检查单行代码的安全性"""
        line = line.strip()
        if not line or line.startswith('#'):
            return
        
        # 先检查是否匹配安全模式
        for safe_pattern in self.safe_patterns:
            if re.search(safe_pattern, line, re.IGNORECASE):
                return  # 安全模式，跳过
        
        # 检查不安全模式
        fields_regex = '|'.join(self.risky_fields)
        
        for pattern_template in self.unsafe_patterns:
            pattern = pattern_template.format(fields=fields_regex)
            matches = re.finditer(pattern, line, re.IGNORECASE)
            
            for match in matches:
                self.issues.append({
                    'file': str(file_path),
                    'line': line_num,
                    'code': line,
                    'issue': f"不安全的字段访问: {match.group()}",
                    'suggestion': self.get_suggestion(match.group(), line)
                })
    
    def get_suggestion(self, unsafe_code, full_line):
        """根据不安全的代码提供修复建议"""
        if '[' in unsafe_code and ']' in unsafe_code:
            # 直接字典访问
            field_match = re.search(r"['\"]([^'\"]+)['\"]", unsafe_code)
            if field_match:
                field = field_match.group(1)
                return f"使用 item.get('{field}', '默认值') 或 format_xxx_display(item) 函数"
        
        elif '.get(' in unsafe_code:
            # 没有默认值的.get()
            return "为 .get() 方法添加默认值参数"
        
        elif any(func in unsafe_code for func in ['st.write', 'st.markdown', 'print', 'Paragraph']):
            # 显示逻辑
            return "使用 display_utils 中的格式化函数，或添加 None 检查"
        
        return "使用安全的字段访问模式"
    
    def check_file(self, file_path):
        """检查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # 检查是否是安全的代码行
                if self.is_safe_line(line):
                    continue
                
                # 对于显示逻辑，检查变量是否安全定义
                line_stripped = line.strip()
                if any(func in line_stripped for func in ['st.write', 'st.markdown', 'print', 'Paragraph']):
                    # 提取变量名
                    for field in self.risky_fields:
                        if field in line_stripped:
                            # 查找包含该字段的变量名
                            var_matches = re.findall(rf'(\w*{field}\w*)', line_stripped)
                            for var_name in var_matches:
                                if self.is_safe_variable_usage(lines, line_num - 1, var_name):
                                    continue  # 变量安全定义，跳过检查
                
                self.check_line_safety(line, line_num, file_path)
                
        except Exception as e:
            print(f"检查文件 {file_path} 时出错: {e}")
    
    def scan_project(self):
        """扫描整个项目"""
        print(f"🔍 开始扫描项目: {self.project_root}")
        print("=" * 60)
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_check_file(file_path):
                self.check_file(file_path)
        
        self.report_results()
    
    def report_results(self):
        """报告检查结果"""
        if not self.issues:
            print("✅ 太棒了！没有发现不安全的字段访问模式")
            return
        
        print(f"⚠️  发现 {len(self.issues)} 个潜在的NULL值处理问题:")
        print("=" * 60)
        
        # 按文件分组显示
        issues_by_file = {}
        for issue in self.issues:
            file_path = issue['file']
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            print(f"\n📁 {file_path}")
            print("-" * 40)
            
            for issue in file_issues:
                print(f"  第 {issue['line']} 行:")
                print(f"    代码: {issue['code']}")
                print(f"    问题: {issue['issue']}")
                print(f"    建议: {issue['suggestion']}")
                print()
        
        print("=" * 60)
        print("🔧 修复建议:")
        print("1. 使用 utils/display_utils.py 中的格式化函数")
        print("2. 将直接字典访问 item['field'] 改为 item.get('field', '默认值')")
        print("3. 在显示逻辑中使用安全的字段访问模式")
        print("4. 参考 CODING_STANDARDS.md 中的最佳实践")
    
    def check_specific_files(self, file_patterns):
        """检查特定的文件"""
        for pattern in file_patterns:
            for file_path in self.project_root.glob(pattern):
                if self.should_check_file(file_path):
                    self.check_file(file_path)
        
        self.report_results()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查代码中的NULL值处理问题")
    parser.add_argument("--path", "-p", default=".", help="项目根目录路径")
    parser.add_argument("--files", "-f", nargs="+", help="检查特定文件（支持通配符）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    checker = CodeChecker(args.path)
    
    if args.files:
        checker.check_specific_files(args.files)
    else:
        checker.scan_project()


if __name__ == "__main__":
    main()