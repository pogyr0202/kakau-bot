import os
import requests
from playwright.sync_api import sync_playwright

def send_line_message(message):
    """Messaging APIを使用してLINEにメッセージを送る"""
    url = "https://api.line.me/v2/bot/message/push"
    
    # さっき作り直した名前をここで読み込みます
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    # どちらの設定が足りないか、ログでハッキリ教えるようにしました
    if not token or not user_id:
        print("\n⚠️ 【重要】GitHubのSecrets設定が足りません！")
        if not token: print("- LINE_CHANNEL_ACCESS_TOKEN が見つかりません")
        if not user_id: print("- USER_ID が見つかりません")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"LINE API Response: {response.status_code}")
        if response.status_code != 200:
            print(f"LINEからのエラー返信: {response.text}")
        response.raise_for_status()
        print("✅ LINEへのメッセージ送信に成功しました！")
    except Exception as e:
        print(f"❌ LINE送信失敗: {e}")

def check_price():
    """価格をチェックするメイン処理"""
    target_url = "https://kakaku.com/item/K0001540961/" 
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 人間が操作しているように見せかける設定
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"URLにアクセス開始: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            # 価格.comの「最安価格」の数字部分を特定する複数の方法
            # 2026年現在の最新の構成に対応
            price_selectors = [
                "span.priceTxt",
                ".p-main_price_value",
                "span[itemprop='price']",
                ".price-box .price"
            ]
            
            price = None
            for sel in price_selectors:
                element = page.locator(sel).first
                if element.is_visible():
                    price = element.inner_text().strip()
                    break
            
            if price:
                output_msg = f"【価格通知】\n現在の価格は {price} です。\n{target_url}"
                print(f"取得成功: {price}")
                send_line_message(output_msg)
            else:
                # 取得できなかった場合は、エラーとしてLINEに送る（どこで詰まったか知るため）
                error_info = "❌ 価格の数字が見つかりませんでした。サイトのデザインが変わった可能性があります。"
                print(error_info)
                send_line_message(error_info)
                
        except Exception as e:
            error_detail = f"⚠️ 実行中にエラーが起きました:\n{str(e)}"
            print(error_detail)
            send_line_message(error_detail)
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()