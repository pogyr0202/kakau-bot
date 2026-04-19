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
        print("❌ エラー: 設定（Secrets）が正しく読み込めていません。")
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
        print(f"LINE API Response Status: {response.status_code}")
        response.raise_for_status()
        print("✅ LINEへのメッセージ送信に成功しました！")
    except Exception as e:
        print(f"❌ LINEへのメッセージ送信に失敗しました: {e}")
        if response is not None:
            print(f"詳細エラー内容: {response.text}")

def check_price():
    """価格をチェックするメイン処理"""
    target_url = "https://kakaku.com/item/K0001540961/" 
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 警告が出にくいコンテキスト作成
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print(f"URLにアクセス中: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded")
            
            # 価格情報を取得（サイトの仕様変更に強い複数のセレクタで試行）
            price_element = page.locator('span.priceTxt, .price, #price, .p-main_price_value').first
            
            if price_element.is_visible():
                price = price_element.inner_text().strip()
                message = f"【価格通知】\n現在の価格は {price} です。\n{target_url}"
                print(f"取得メッセージ: {message}")
                send_line_message(message)
            else:
                raise Exception("価格の要素が見つかりませんでした。")
                
        except Exception as e:
            error_msg = f"⚠️ 価格取得中にエラーが発生しました:\n{str(e)}"
            print(error_msg)
            send_line_message(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()