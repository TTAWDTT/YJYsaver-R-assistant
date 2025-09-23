"""
代码分析器
对R代码进行静态分析和质量评估
"""

import re
import ast
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """代码指标数据类"""
    lines_of_code: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions_count: int = 0
    complexity_score: float = 0.0
    readability_score: float = 0.0


class RCodeAnalyzer:
    """R代码分析器"""
    
    def __init__(self):
        # R语言关键字
        self.r_keywords = {
            'if', 'else', 'for', 'while', 'function', 'return', 'next', 'break',
            'repeat', 'TRUE', 'FALSE', 'NULL', 'NA', 'Inf', 'NaN'
        }
        
        # R内置函数（部分）
        self.r_builtin_functions = {
            'c', 'list', 'data.frame', 'matrix', 'array', 'factor',
            'length', 'dim', 'names', 'colnames', 'rownames',
            'head', 'tail', 'str', 'summary', 'print',
            'mean', 'median', 'sd', 'var', 'sum', 'min', 'max',
            'apply', 'lapply', 'sapply', 'tapply', 'mapply',
            'ggplot', 'aes', 'geom_point', 'geom_line', 'geom_bar'
        }
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """分析R代码并返回分析结果"""
        try:
            metrics = self._calculate_metrics(code)
            quality_issues = self._detect_quality_issues(code)
            style_issues = self._check_style(code)
            complexity = self._calculate_complexity(code)
            
            # 计算总体质量分数
            quality_score = self._calculate_quality_score(
                metrics, quality_issues, style_issues, complexity
            )
            
            return {
                'metrics': metrics.__dict__,
                'quality_score': quality_score,
                'quality_issues': quality_issues,
                'style_issues': style_issues,
                'complexity': complexity,
                'recommendations': self._generate_recommendations(
                    quality_issues, style_issues, complexity
                )
            }
            
        except Exception as e:
            logger.error("Code analysis failed: %s", str(e))
            return {
                'error': f"分析失败: {str(e)}",
                'quality_score': 0
            }
    
    def _calculate_metrics(self, code: str) -> CodeMetrics:
        """计算基本代码指标"""
        lines = code.split('\n')
        metrics = CodeMetrics()
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith('#'):
                metrics.comment_lines += 1
            else:
                metrics.lines_of_code += 1
        
        # 计算函数数量
        function_pattern = r'\b\w+\s*<-\s*function\s*\('
        metrics.functions_count = len(re.findall(function_pattern, code))
        
        return metrics
    
    def _detect_quality_issues(self, code: str) -> List[Dict[str, str]]:
        """检测代码质量问题"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 检查过长的行
            if len(line) > 100:
                issues.append({
                    'type': 'line_length',
                    'line': i,
                    'message': f'第{i}行过长 ({len(line)} 字符，建议不超过100字符)',
                    'severity': 'warning'
                })
            
            # 检查缺少空格
            if re.search(r'[a-zA-Z0-9][\+\-\*\/\=][a-zA-Z0-9]', stripped):
                issues.append({
                    'type': 'spacing',
                    'line': i,
                    'message': f'第{i}行运算符周围缺少空格',
                    'severity': 'style'
                })
            
            # 检查硬编码值
            if re.search(r'\b\d{4,}\b', stripped) and not stripped.startswith('#'):
                issues.append({
                    'type': 'magic_number',
                    'line': i,
                    'message': f'第{i}行包含魔法数字，建议使用常量',
                    'severity': 'warning'
                })
        
        # 检查是否缺少注释
        total_lines = len([l for l in lines if l.strip()])
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        
        if total_lines > 10 and comment_lines / total_lines < 0.1:
            issues.append({
                'type': 'lack_of_comments',
                'line': 0,
                'message': '代码缺少足够的注释（建议注释率不低于10%）',
                'severity': 'warning'
            })
        
        return issues
    
    def _check_style(self, code: str) -> List[Dict[str, str]]:
        """检查代码风格"""
        style_issues = []
        
        # 检查变量命名风格
        variable_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*<-'
        variables = re.findall(variable_pattern, code)
        
        for var in variables:
            if not re.match(r'^[a-z][a-z0-9_]*$', var) and not re.match(r'^[A-Z][A-Z0-9_]*$', var):
                style_issues.append({
                    'type': 'naming_convention',
                    'message': f'变量 "{var}" 不符合命名规范（建议使用小写字母和下划线）',
                    'severity': 'style'
                })
        
        # 检查函数命名
        function_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*<-\s*function'
        functions = re.findall(function_pattern, code)
        
        for func in functions:
            if not re.match(r'^[a-z][a-z0-9_]*$', func):
                style_issues.append({
                    'type': 'function_naming',
                    'message': f'函数 "{func}" 不符合命名规范（建议使用小写字母和下划线）',
                    'severity': 'style'
                })
        
        return style_issues
    
    def _calculate_complexity(self, code: str) -> Dict[str, Any]:
        """计算代码复杂度"""
        # 简单的圈复杂度计算
        control_structures = [
            r'\bif\s*\(',
            r'\bfor\s*\(',
            r'\bwhile\s*\(',
            r'\brepeat\s*\{',
            r'\&\&',
            r'\|\|'
        ]
        
        complexity = 1  # 基础复杂度
        for pattern in control_structures:
            complexity += len(re.findall(pattern, code))
        
        # 嵌套深度
        max_nesting = self._calculate_max_nesting(code)
        
        complexity_level = 'low'
        if complexity > 20:
            complexity_level = 'high'
        elif complexity > 10:
            complexity_level = 'medium'
        
        return {
            'cyclomatic_complexity': complexity,
            'max_nesting_depth': max_nesting,
            'complexity_level': complexity_level
        }
    
    def _calculate_max_nesting(self, code: str) -> int:
        """计算最大嵌套深度"""
        max_depth = 0
        current_depth = 0
        
        for char in code:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _calculate_quality_score(self, metrics: CodeMetrics, 
                                quality_issues: List[Dict], 
                                style_issues: List[Dict], 
                                complexity: Dict) -> float:
        """计算总体质量分数（0-100）"""
        base_score = 100.0
        
        # 根据问题扣分
        for issue in quality_issues:
            if issue['severity'] == 'error':
                base_score -= 15
            elif issue['severity'] == 'warning':
                base_score -= 8
            elif issue['severity'] == 'style':
                base_score -= 3
        
        for issue in style_issues:
            base_score -= 2
        
        # 根据复杂度扣分
        if complexity['complexity_level'] == 'high':
            base_score -= 20
        elif complexity['complexity_level'] == 'medium':
            base_score -= 10
        
        # 根据注释率加分
        if metrics.lines_of_code > 0:
            comment_ratio = metrics.comment_lines / (metrics.lines_of_code + metrics.comment_lines)
            if comment_ratio > 0.2:
                base_score += 5
            elif comment_ratio < 0.05:
                base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _generate_recommendations(self, quality_issues: List[Dict], 
                                style_issues: List[Dict], 
                                complexity: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if quality_issues:
            recommendations.append("修复代码质量问题，特别关注错误和警告级别的问题")
        
        if style_issues:
            recommendations.append("统一代码风格，遵循R语言编码规范")
        
        if complexity['complexity_level'] == 'high':
            recommendations.append("考虑重构复杂的函数，将其分解为更小的函数")
        
        if complexity['max_nesting_depth'] > 4:
            recommendations.append("减少代码嵌套层次，提高可读性")
        
        # 通用建议
        recommendations.extend([
            "添加更多有意义的注释",
            "使用描述性的变量和函数名",
            "考虑添加错误处理机制",
            "遵循DRY（Don't Repeat Yourself）原则"
        ])
        
        return recommendations


# 全局分析器实例
code_analyzer = RCodeAnalyzer()