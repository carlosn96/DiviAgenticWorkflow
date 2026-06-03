from playwright.sync_api import sync_playwright

def inspect_buttons():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Homepage
        print("=== HOMEPAGE BUTTONS ===")
        page.goto("http://divitheme.local/")
        page.wait_for_load_state("networkidle")
        
        buttons = page.query_selector_all("a.et_pb_button, button.et_pb_button")
        print(f"Found {len(buttons)} buttons on homepage.")
        for idx, btn in enumerate(buttons):
            text = btn.inner_text().strip()
            styles = page.evaluate("(el) => { let s = window.getComputedStyle(el); return { fg: s.color, bg: s.backgroundColor, border: s.borderColor, pad: s.padding, radius: s.borderRadius }; }", btn)
            print(f"Button {idx+1} '{text}':")
            print(f"  Classes: {btn.get_attribute('class')}")
            print(f"  Styles: {styles}")

        # 2. Blog Page
        print("\n=== BLOG PAGE BUTTONS ===")
        page.goto("http://divitheme.local/blog/")
        page.wait_for_load_state("networkidle")
        
        buttons = page.query_selector_all("a.et_pb_button, button.et_pb_button")
        print(f"Found {len(buttons)} buttons on blog page.")
        for idx, btn in enumerate(buttons):
            text = btn.inner_text().strip()
            styles = page.evaluate("(el) => { let s = window.getComputedStyle(el); return { fg: s.color, bg: s.backgroundColor, border: s.borderColor, pad: s.padding, radius: s.borderRadius }; }", btn)
            print(f"Button {idx+1} '{text}':")
            print(f"  Classes: {btn.get_attribute('class')}")
            print(f"  Styles: {styles}")
            
        browser.close()

if __name__ == '__main__':
    inspect_buttons()
