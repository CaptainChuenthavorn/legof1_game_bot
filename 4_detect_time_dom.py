from playwright.sync_api import sync_playwright
import time

def wait_for_timer_zero(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        print("[*] Waiting for game to load...")
        page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)

        print("[*] Waiting for timer to start at 0:00.000...")
        while True:
            timer_text = page.inner_text(".game__ui__stats__text--time").strip()
            print("Current timer:", timer_text)
            if timer_text.startswith("0:00"):
                print("[✓] Timer started! Start bot now.")
                break
            time.sleep(0.1)

        if timer_text.startswith("0:00"):
            print("[✓] Timer started! Start bot now.")
            keyboard.press('right')
            time.sleep(5)
            keyboard.release('right')

# Example usage
wait_for_timer_zero("https://f1-contest.com/versions/th/lazada/en.html?utm_source=meta_traf&utm_medium=image&_campaign=lazada_f1_game&utm_campaign=lazada_f1_game&utm_id=7052025&utm_content=boost&fbclid=IwY2xjawKNDrpleHRuA2FlbQIxMABicmlkETFmeFcwN1VvQ2VlUmJQV3RVAR5PVfdjYvdCNQJaSQkSsxHEijzq_q9rzdRqQ_hXyUph2GkLYf2MNNBo4fJl-Q_aem_4Jnql_TSVyyYYKB7pMEN7w")
