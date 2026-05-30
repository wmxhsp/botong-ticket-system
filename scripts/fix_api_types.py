#!/usr/bin/env python3
"""
批量修复API模块TypeScript错误
- 删除未使用的ApiResponse和类型导入
- 添加缺失的参数类型注解
- 添加返回类型Promise<any>
"""

import re
from pathlib import Path

API_DIR = Path('frontend/src/api')

def fix_api_file(filepath: Path):
    """修复单个API文件"""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # 1. 删除未使用的ApiResponse导入
    content = re.sub(r"import type \{ ApiResponse \} from '\./schemas'\n", '', content)
    
    # 2. 删除未使用的类型导入（如果该类型在文件中未被引用）
    type_imports = re.findall(r"import type \{ (\w+) \} from '@/types'", content)
    for type_name in type_imports:
        # 检查是否在代码中使用了这个类型
        if not re.search(rf'\b{type_name}\b', content.replace(f"import type {{ {type_name} }}", '')):
            content = re.sub(rf"import type \{{ {type_name} \}} from '@/types'\n", '', content)
    
    # 3. 为没有类型注解的参数添加类型
    # 匹配 pattern: methodName(paramName) { 或 methodName(paramName, data) {
    def add_param_types(match):
        method_name = match.group(1)
        params = match.group(2)
        
        # 跳过已经有类型的参数
        if ':' in params:
            return match.group(0)
        
        # 为常见参数名添加类型
        typed_params = []
        for param in params.split(','):
            param = param.strip()
            if not param:
                continue
            if param in ['id', 'goodsId', 'catId', 'typeId', 'ticketId', 'poId', 'parentId', 'subtaskId']:
                typed_params.append(f'{param}: number | string')
            elif param in ['data']:
                typed_params.append(f'{param}: Record<string, any>')
            else:
                typed_params.append(param)
        
        return f"{method_name}({', '.join(typed_params)})"
    
    content = re.sub(r'(\w+)\(([^)]+)\)\s*\{', add_param_types, content)
    
    # 4. 为没有返回类型的方法添加 Promise<any>
    # 匹配 pattern: methodName(...) { return client.
    def add_return_type(match):
        full_match = match.group(0)
        if 'Promise<' in full_match:
            return full_match
        return full_match.replace('{', ': Promise<any> {')
    
    content = re.sub(r'(\w+\([^)]*\))\s*\{\s*return client\.', add_return_type, content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"✓ Fixed: {filepath.name}")
        return True
    return False

def main():
    ts_files = list(API_DIR.glob('*.ts'))
    print(f"Found {len(ts_files)} TypeScript files")
    
    fixed_count = 0
    for ts_file in ts_files:
        if fix_api_file(ts_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()
