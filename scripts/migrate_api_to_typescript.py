#!/usr/bin/env python3
"""
API模块批量TypeScript迁移脚本
自动将frontend/src/api/*.js迁移到*.ts
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
API_DIR = PROJECT_ROOT / 'frontend' / 'src' / 'api'
TYPES_FILE = PROJECT_ROOT / 'frontend' / 'src' / 'types' / 'index.ts'

# 模块名到类型名的映射
MODULE_TYPE_MAP = {
    'goods': 'Goods',
    'todos': 'Todo',
    'staff': 'Staff',
    'suppliers': 'Supplier',
    'purchase': 'PurchaseOrder',
    'reminders': 'Reminder',
    'warehouses': 'Warehouse',
    'service-fees': 'ServiceFee',
}

def extract_api_methods(js_content: str) -> List[Tuple[str, str, str, str]]:
    """提取API方法定义
    
    Returns:
        List of (method_name, params, http_method, data_param)
    """
    methods = []
    
    # 匹配API方法定义
    pattern = r'(\w+)\s*\(([^)]*)\)\s*\{[^}]*return\s+client\.(get|post|put|delete)\s*\('
    
    for match in re.finditer(pattern, js_content, re.MULTILINE | re.DOTALL):
        method_name = match.group(1)
        params = match.group(2).strip()
        http_method = match.group(3)
        
        # 提取URL和data参数
        rest_of_line = js_content[match.end():match.end()+100]
        data_match = re.search(r',\s*([^)}]+)', rest_of_line)
        data_param = data_match.group(1).strip() if data_match else ''
        
        methods.append((method_name, params, http_method, data_param))
    
    return methods

def find_type_for_module(module_name: str) -> str:
    """根据模块名查找对应的类型名"""
    return MODULE_TYPE_MAP.get(module_name, 'any')

def generate_method_signature(method_name: str, params: str, http_method: str, 
                             data_param: str, type_name: str) -> str:
    """生成TypeScript方法签名"""
    
    # 处理参数
    if not params or params == '=':
        params_str = ''
    elif 'params' in params.lower():
        params_str = f'params: Record<string, any> = {{}}'
    elif 'id' in params.lower():
        params_str = f'id: number | string'
    elif 'data' in params.lower() or 'formData' in params.lower():
        params_str = f'data: any'
    else:
        params_str = f'{params}: any'
    
    # 确定返回类型
    if http_method in ['post', 'put', 'delete']:
        return_type = f'Promise<ApiResponse<{type_name}>>'
    else:  # get
        return_type = f'Promise<ApiResponse<{type_name}[]>>'
    
    # 特殊处理：delete通常返回void
    if http_method == 'delete' and 'photo' not in method_name.lower():
        return_type = 'Promise<ApiResponse<void>>'
    
    signature = f"  /** API方法 */\n"
    signature += f"  {method_name}({params_str}): {return_type} {{\n"
    
    # 构建调用
    if http_method == 'get':
        if params_str:
            signature += f"    return client.get('/xxx/', {{ params }})\n"
        else:
            signature += f"    return client.get('/xxx/')\n"
    else:
        signature += f"    return client.{http_method}('/xxx/', data)\n"
    
    signature += f"  }},\n\n"
    
    return signature

def generate_ts_content(module_name: str, methods: List[Tuple], type_name: str) -> str:
    """生成完整的TypeScript文件内容"""
    
    # 模块名转API对象名
    api_name = module_name.replace('-', '_') + 'Api'
    
    content = f"""import client from './client'
import type {{ ApiResponse }} from './schemas'
import type {{ {type_name} }} from '@/types'

/**
 * {module_name} API
 */
export const {api_name} = {{
"""
    
    # 添加方法（简化版，实际URL需要手动调整）
    for method_name, params, http_method, data_param in methods:
        content += f"  {method_name}("
        
        if not params or params == '=':
            content += ")"
        elif 'params' in params.lower():
            content += "params: Record<string, any> = {})"
        elif 'id' in params.lower():
            content += "id: number | string)"
        else:
            content += f"{params})"
        
        # 返回类型
        if http_method == 'get':
            content += f": Promise<ApiResponse<any>> {{\n"
            content += f"    return client.get('/xxx/'"
            if 'params' in params.lower():
                content += ", { params }"
            content += ")\n"
        else:
            content += f": Promise<ApiResponse<void>> {{\n"
            content += f"    return client.{http_method}('/xxx/', data)\n"
        
        content += "  },\n\n"
    
    content += "}\n"
    
    return content

def migrate_single_module(js_file: Path, dry_run: bool = False) -> bool:
    """迁移单个模块"""
    
    module_name = js_file.stem
    ts_file = js_file.with_suffix('.ts')
    
    print(f"\n处理: {module_name}.js")
    
    # 读取.js文件
    try:
        js_content = js_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ✗ 读取失败: {e}")
        return False
    
    # 提取API方法
    methods = extract_api_methods(js_content)
    print(f"  找到 {len(methods)} 个API方法")
    
    # 查找对应类型
    type_name = find_type_for_module(module_name)
    print(f"  使用类型: {type_name}")
    
    if dry_run:
        print(f"  [DRY RUN] 将生成 {ts_file.name}")
        return True
    
    # 生成.ts文件内容（简化版，保留原.js的逻辑结构）
    ts_content = convert_js_to_ts(js_content, module_name, type_name)
    
    # 写入.ts文件
    try:
        ts_file.write_text(ts_content, encoding='utf-8')
        print(f"  ✓ 已生成 {ts_file.name}")
    except Exception as e:
        print(f"  ✗ 写入失败: {e}")
        return False
    
    # 删除.js文件
    try:
        js_file.unlink()
        print(f"  ✓ 已删除 {js_file.name}")
    except Exception as e:
        print(f"  ⚠ 删除失败: {e}")
    
    return True

def convert_js_to_ts(js_content: str, module_name: str, type_name: str) -> str:
    """将JavaScript内容转换为TypeScript（基础版本）"""
    
    # 添加import语句
    lines = js_content.split('\n')
    
    # 找到第一行import之后插入TypeScript imports
    new_lines = []
    import_inserted = False
    
    for line in lines:
        new_lines.append(line)
        
        # 在第一个import之后插入类型导入
        if not import_inserted and line.startswith('import client'):
            new_lines.append(f"import type {{ ApiResponse }} from './schemas'")
            if type_name != 'any':
                new_lines.append(f"import type {{ {type_name} }} from '@/types'")
            import_inserted = True
    
    # 添加简单的类型注解（函数参数）
    ts_content = '\n'.join(new_lines)
    
    # 简单的类型推断替换
    ts_content = re.sub(r'list\(params = \{\}\)', 'list(params: Record<string, any> = {})', ts_content)
    ts_content = re.sub(r'getById\(id\)', 'getById(id: number | string)', ts_content)
    ts_content = re.sub(r'create\(data\)', 'create(data: any)', ts_content)
    ts_content = re.sub(r'update\((\w+), data\)', r'update(\1: number | string, data: any)', ts_content)
    ts_content = re.sub(r'delete\((\w+)\)', r'delete(\1: number | string)', ts_content)
    
    return ts_content

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='API模块TypeScript迁移工具')
    parser.add_argument('--batch', type=int, choices=[1, 2, 3], 
                       help='执行批次 (1=简单模块, 2=中等模块, 3=复杂模块)')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式，不实际修改文件')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("API模块批量TypeScript迁移工具")
    print("=" * 60)
    
    # 获取所有待迁移的.js文件
    js_files = list(API_DIR.glob('*.js'))
    
    # 过滤掉已有.ts的模块
    files_to_migrate = []
    for js_file in js_files:
        ts_file = js_file.with_suffix('.ts')
        if not ts_file.exists():
            files_to_migrate.append(js_file)
    
    print(f"\n发现 {len(files_to_migrate)} 个待迁移模块\n")
    
    if not files_to_migrate:
        print("没有需要迁移的文件！")
        return
    
    # 按文件大小分组
    simple_modules = [f for f in files_to_migrate if f.stat().st_size < 2000]  # <50行
    medium_modules = [f for f in files_to_migrate if 2000 <= f.stat().st_size < 5000]  # 50-100行
    complex_modules = [f for f in files_to_migrate if f.stat().st_size >= 5000]  # >100行
    
    print(f"简单模块 (<50行): {len(simple_modules)} 个")
    print(f"中等模块 (50-100行): {len(medium_modules)} 个")
    print(f"复杂模块 (>100行): {len(complex_modules)} 个")
    
    # 根据批次选择要处理的文件
    if args.batch == 1:
        target_files = simple_modules
        print(f"\n执行第一批迁移（简单模块）...")
    elif args.batch == 2:
        target_files = medium_modules
        print(f"\n执行第二批迁移（中等模块）...")
    elif args.batch == 3:
        target_files = complex_modules
        print(f"\n执行第三批迁移（复杂模块）...")
    else:
        target_files = files_to_migrate
        print(f"\n执行全部迁移...")
    
    # 执行迁移
    success_count = 0
    for js_file in target_files:
        if migrate_single_module(js_file, args.dry_run):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"迁移完成！成功: {success_count}/{len(target_files)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
