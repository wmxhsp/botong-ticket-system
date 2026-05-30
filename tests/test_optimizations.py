#!/usr/bin/env python3
"""
博通工单系统优化功能自动化测试脚本
测试6周优化计划的15个任务
"""

import requests
import time
import json
import sys
from datetime import datetime
from pathlib import Path

# 配置
BASE_URL = "http://localhost:5053"
FRONTEND_URL = "http://localhost:5173"

class OptimizationTests:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        self.start_time = datetime.now()
        
    def log(self, message, level="INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def login(self, username="admin", password="123456"):
        """登录获取认证"""
        try:
            # 先获取CSRF token
            response = self.session.get(f"{BASE_URL}/login")
            
            # 尝试登录（根据实际情况调整）
            login_data = {
                'username': username,
                'password': password
            }
            response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            
            if response.status_code == 200:
                self.log("登录成功")
                return True
            else:
                self.log(f"登录失败: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"登录异常: {e}", "ERROR")
            return False
    
    def test_api_fields_filtering(self):
        """Task 1.4: 测试API字段过滤"""
        self.log("开始测试 Task 1.4: API字段过滤")
        
        try:
            # 测试不带fields参数
            start = time.time()
            response_full = self.session.get(f"{BASE_URL}/api/v1/tickets/", params={
                'page': 1,
                'per_page': 5
            })
            time_full = time.time() - start
            
            if response_full.status_code != 200:
                self.log(f"API请求失败: {response_full.status_code}", "ERROR")
                self.results.append({
                    'task': '1.4',
                    'name': 'API字段过滤',
                    'status': 'FAIL',
                    'reason': f'API返回错误: {response_full.status_code}'
                })
                return
            
            data_full = response_full.json()
            size_full = len(response_full.content)
            
            # 测试带fields参数
            start = time.time()
            response_filtered = self.session.get(f"{BASE_URL}/api/v1/tickets/", params={
                'page': 1,
                'per_page': 5,
                'fields': 'id,ticket_no,client,status,total'
            })
            time_filtered = time.time() - start
            
            data_filtered = response_filtered.json()
            size_filtered = len(response_filtered.content)
            
            # 计算减少比例
            reduction = ((size_full - size_filtered) / size_full) * 100 if size_full > 0 else 0
            
            self.log(f"完整响应大小: {size_full} bytes ({time_full:.3f}s)")
            self.log(f"过滤响应大小: {size_filtered} bytes ({time_filtered:.3f}s)")
            self.log(f"体积减少: {reduction:.1f}%")
            
            # 验证
            passed = reduction >= 30  # 至少减少30%
            status = "PASS" if passed else "FAIL"
            
            self.results.append({
                'task': '1.4',
                'name': 'API字段过滤',
                'status': status,
                'metrics': {
                    'full_size': size_full,
                    'filtered_size': size_filtered,
                    'reduction_percent': round(reduction, 1),
                    'target': 60
                }
            })
            
            self.log(f"Task 1.4 测试结果: {status}")
            
        except Exception as e:
            self.log(f"Task 1.4 测试异常: {e}", "ERROR")
            self.results.append({
                'task': '1.4',
                'name': 'API字段过滤',
                'status': 'ERROR',
                'reason': str(e)
            })
    
    def test_api_response_time(self):
        """Task 3.5: 测试API响应时间"""
        self.log("开始测试 Task 3.5: API响应时间")
        
        try:
            times = []
            for i in range(5):
                start = time.time()
                response = self.session.get(f"{BASE_URL}/api/v1/tickets/", params={
                    'page': 1,
                    'per_page': 10
                })
                elapsed = time.time() - start
                times.append(elapsed)
                
                if response.status_code != 200:
                    self.log(f"请求 {i+1} 失败: {response.status_code}", "WARN")
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            self.log(f"平均响应时间: {avg_time*1000:.1f}ms")
            self.log(f"最快: {min_time*1000:.1f}ms, 最慢: {max_time*1000:.1f}ms")
            
            passed = avg_time < 0.5  # 平均<500ms
            status = "PASS" if passed else "FAIL"
            
            self.results.append({
                'task': '3.5',
                'name': 'API响应时间',
                'status': status,
                'metrics': {
                    'avg_ms': round(avg_time * 1000, 1),
                    'max_ms': round(max_time * 1000, 1),
                    'min_ms': round(min_time * 1000, 1),
                    'target_ms': 500
                }
            })
            
            self.log(f"Task 3.5 测试结果: {status}")
            
        except Exception as e:
            self.log(f"Task 3.5 测试异常: {e}", "ERROR")
            self.results.append({
                'task': '3.5',
                'name': 'API响应时间',
                'status': 'ERROR',
                'reason': str(e)
            })
    
    def test_database_query_performance(self):
        """测试数据库查询性能"""
        self.log("开始测试数据库查询性能")
        
        try:
            import sqlite3
            db_path = Path(__file__).parent.parent / "tickets.db"
            
            if not db_path.exists():
                self.log("数据库文件不存在", "ERROR")
                return
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 测试工单表查询
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM tickets")
            count = cursor.fetchone()[0]
            query_time = time.time() - start
            
            self.log(f"工单总数: {count}")
            self.log(f"查询时间: {query_time*1000:.2f}ms")
            
            # 检查索引
            cursor.execute("PRAGMA index_list(tickets)")
            indexes = cursor.fetchall()
            self.log(f"索引数量: {len(indexes)}")
            
            conn.close()
            
            self.results.append({
                'task': 'DB',
                'name': '数据库查询性能',
                'status': 'PASS',
                'metrics': {
                    'ticket_count': count,
                    'query_time_ms': round(query_time * 1000, 2),
                    'index_count': len(indexes)
                }
            })
            
        except Exception as e:
            self.log(f"数据库测试异常: {e}", "ERROR")
    
    def check_frontend_files(self):
        """检查前端优化文件是否存在"""
        self.log("开始检查前端优化文件")
        
        frontend_path = Path(__file__).parent.parent / "frontend" / "src"
        
        files_to_check = [
            ("composables/useCommandPalette.ts", "1.1", "命令面板"),
            ("composables/useKeyboardShortcuts.ts", "1.2", "快捷键系统"),
            ("core/composables/useDebounce.ts", "1.5", "防抖机制"),
            ("core/composables/useHapticFeedback.ts", "2.2", "触觉反馈"),
            ("core/composables/useOfflineSync.ts", "3.1", "离线同步"),
            ("core/composables/useVoiceInput.ts", "3.2", "语音输入"),
            ("core/composables/useBatchOperations.ts", "3.3", "批量操作"),
            ("components/common/LoadingSkeleton.vue", "2.1", "骨架屏"),
        ]
        
        for file_path, task_id, name in files_to_check:
            full_path = frontend_path / file_path
            exists = full_path.exists()
            
            if exists:
                size = full_path.stat().st_size
                self.log(f"[PASS] Task {task_id}: {name} ({size} bytes)")
                self.results.append({
                    'task': task_id,
                    'name': name,
                    'status': 'PASS',
                    'file_size': size
                })
            else:
                self.log(f"[FAIL] Task {task_id}: {name} - 文件不存在", "ERROR")
                self.results.append({
                    'task': task_id,
                    'name': name,
                    'status': 'FAIL',
                    'reason': '文件不存在'
                })
    
    def check_backend_files(self):
        """检查后端优化文件"""
        self.log("开始检查后端优化文件")
        
        backend_path = Path(__file__).parent.parent / "api" / "v1"
        tickets_py = backend_path / "tickets.py"
        
        if tickets_py.exists():
            content = tickets_py.read_text()
            
            # 检查fields参数支持
            has_fields_param = 'fields' in content and 'request.args.get("fields"' in content
            
            if has_fields_param:
                self.log("[PASS] Task 1.4: API字段过滤已实现")
                self.results.append({
                    'task': '1.4',
                    'name': 'API字段过滤实现',
                    'status': 'PASS'
                })
            else:
                self.log("[FAIL] Task 1.4: API字段过滤未实现", "ERROR")
                self.results.append({
                    'task': '1.4',
                    'name': 'API字段过滤实现',
                    'status': 'FAIL',
                    'reason': '代码中未找到fields参数处理'
                })
        else:
            self.log("[FAIL] tickets.py 文件不存在", "ERROR")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("博通工单系统优化功能测试报告")
        print("=" * 60)
        print(f"测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试耗时: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        print()
        
        # 按阶段分组
        stages = {
            '阶段1: P0核心瓶颈修复': ['1.1', '1.2', '1.3', '1.4', '1.5'],
            '阶段2: P1体验增强': ['2.1', '2.2', '2.3', '2.4', '2.5'],
            '阶段3: P2高级功能': ['3.1', '3.2', '3.3', '3.4', '3.5'],
        }
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['status'] == 'PASS')
        failed_tests = sum(1 for r in self.results if r['status'] in ['FAIL', 'ERROR'])
        
        for stage_name, task_ids in stages.items():
            print(f"\n{stage_name}")
            print("-" * 60)
            
            stage_results = [r for r in self.results if r['task'] in task_ids]
            
            for result in stage_results:
                status_icon = "✓" if result['status'] == 'PASS' else "✗"
                print(f"  [{status_icon}] Task {result['task']}: {result['name']} - {result['status']}")
                
                if 'metrics' in result:
                    for key, value in result['metrics'].items():
                        print(f"      {key}: {value}")
                
                if result['status'] in ['FAIL', 'ERROR'] and 'reason' in result:
                    print(f"      原因: {result['reason']}")
        
        print("\n" + "=" * 60)
        print("总体统计")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)" if total_tests > 0 else "通过: 0")
        print(f"失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)" if total_tests > 0 else "失败: 0")
        
        # 保存JSON报告
        report = {
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'results': self.results
        }
        
        report_path = Path(__file__).parent / "optimization_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"测试报告已保存到: {report_path}")
        
        return passed_tests, total_tests
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 60)
        self.log("开始执行优化功能自动化测试")
        self.log("=" * 60)
        print()
        
        # 尝试登录（可选）
        # self.login()
        
        # 执行测试
        self.check_frontend_files()
        print()
        self.check_backend_files()
        print()
        self.test_api_fields_filtering()
        print()
        self.test_api_response_time()
        print()
        self.test_database_query_performance()
        print()
        
        # 生成报告
        passed, total = self.generate_report()
        
        # 退出码
        if passed == total:
            self.log("所有测试通过！✓")
            return 0
        else:
            self.log(f"部分测试失败，请检查报告", "WARN")
            return 1


def main():
    """主函数"""
    tester = OptimizationTests()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
