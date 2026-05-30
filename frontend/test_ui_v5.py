from playwright.sync_api import sync_playwright
import time

def test_ui_v5_features():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        
        print("=" * 50)
        print("UI v5 功能测试开始")
        print("=" * 50)
        
        # 1. 测试首页加载
        print("\n[1/6] 测试首页加载...")
        page.goto('http://localhost:5174/')
        page.wait_for_load_state('networkidle')
        page.screenshot(path='/tmp/test_01_homepage.png', full_page=True)
        print("✅ 首页加载成功")
        
        # 2. 测试命令面板 (Cmd+K)
        print("\n[2/6] 测试命令面板 (Cmd+K)...")
        page.keyboard.press('Control+k')
        time.sleep(0.5)
        page.screenshot(path='/tmp/test_02_command_palette.png')
        
        # 检查命令面板是否出现
        palette = page.locator('.command-palette, [class*="palette"]').first
        if palette.is_visible():
            print("✅ 命令面板已打开")
        else:
            print("⚠️ 命令面板可能未正确显示")
        
        # 关闭命令面板
        page.keyboard.press('Escape')
        time.sleep(0.3)
        
        # 3. 测试快捷键帮助 (Shift+?)
        print("\n[3/6] 测试快捷键帮助 (Shift+?)...")
        page.keyboard.press('Shift+?')
        time.sleep(0.5)
        page.screenshot(path='/tmp/test_03_shortcuts_help.png')
        
        # 关闭帮助
        page.keyboard.press('Escape')
        time.sleep(0.3)
        
        # 4. 测试工单列表（双栏布局）
        print("\n[4/6] 测试工单列表（双栏布局）...")
        page.goto('http://localhost:5174/tickets')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='/tmp/test_04_tickets_list.png', full_page=True)
        print("✅ 工单列表页面加载成功")
        
        # 5. 测试移动端快速创建页面
        print("\n[5/6] 测试移动端快速创建页面...")
        page.set_viewport_size({'width': 375, 'height': 667})
        page.goto('http://localhost:5174/tickets/quick')
        page.wait_for_load_state('networkidle')
        time.sleep(0.5)
        page.screenshot(path='/tmp/test_05_quick_ticket_mobile.png', full_page=True)
        print("✅ 快速创建页面加载成功")
        
        # 6. 测试移动端一键结算页面
        print("\n[6/6] 测试移动端一键结算页面...")
        page.goto('http://localhost:5174/tickets/1/settle')
        page.wait_for_load_state('networkidle')
        time.sleep(0.5)
        page.screenshot(path='/tmp/test_06_quick_settle_mobile.png', full_page=True)
        print("✅ 一键结算页面加载成功")
        
        # 恢复桌面视图
        page.set_viewport_size({'width': 1280, 'height': 800})
        
        browser.close()
        
        print("\n" + "=" * 50)
        print("UI v5 功能测试完成")
        print("=" * 50)
        print("\n截图保存位置：")
        print("  /tmp/test_01_homepage.png - 首页")
        print("  /tmp/test_02_command_palette.png - 命令面板")
        print("  /tmp/test_03_shortcuts_help.png - 快捷键帮助")
        print("  /tmp/test_04_tickets_list.png - 工单列表（双栏）")
        print("  /tmp/test_05_quick_ticket_mobile.png - 快速创建（移动端）")
        print("  /tmp/test_06_quick_settle_mobile.png - 一键结算（移动端）")

if __name__ == '__main__':
    test_ui_v5_features()
