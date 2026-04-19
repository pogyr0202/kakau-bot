import os
import requests
from playwright.sync_api import sync_playwright

def send_line_message(message):
    """Messaging APIを使用してLINEにメッセージを送る"""
    url = "https://api.line.me/v2/bot/message/push"
    
    # GitHubのSettings > Secretsで設定した名前を読み込みます
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    if not token or not user_id:
        print("Error: LINE_CHANNEL_ACCESS_TOKEN or USER_ID is not set.")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("LINE message sent successfully!")
    except Exception as e:
        print(f"Failed to send LINE message: {e}")

def check_price():
    """価格をチェックするメイン処理"""
    target_url = "https://kakaku.com/item/K0001540961/" # 例として価格.comのURL
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_depth_page() if hasattr(browser, 'new_depth_page') else browser.new_page()
        
        try:
            page.goto(target_url)
            # 価格情報を取得（サイトの構造に合わせて調整してください）
            price = page.locator('.price').first.inner_text()
            message = f"\n現在の価格は {price} です。\n{target_url}"
            send_line_message(message)
        except Exception as e:
            error_msg = f"\n価格取得エラーが発生しました:\n{str(e)}"
            print(error_msg)
            send_line_message(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()