import os
import requests
import time
from playwright.sync_api import sync_playwright

def send_line_message(message):
    """Messaging APIを使用してLINEにメッセージを送る"""
    url = "https://api.line.me/v2/bot/message/push"
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    if not token or not user_id:
        print("⚠️ Secretsの設定が足りません")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"LINE API Response: {response.status_code}")
        response.raise_for_status()
    except Exception as e:
        print(f"❌ LINE送信失敗: {e}")

def check_price():
    """価格をチェックするメイン処理"""
    target_url = "https://kakaku.com/item/K0001540961/" 
    
    with sync_playwright() as p:
        # ブラウザを起動（言語設定を日本語に固定）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="ja-JP"
        )
        page = context.new_page()
        
        try:
            print(f"URLにアクセス開始: {target_url}")
            # 少しゆっくりアクセスして人間っぽさを出します
            page.goto(target_url, wait_until="networkidle", timeout=60000)
            time.sleep(3) # 3秒待機して読み込みを確実にする
            
            # 価格.comの「最安価格」を指す複数のパターン
            price_selectors = [
                "span.priceTxt",
                ".p-main_price_value",
                "span[itemprop='price']",
                "div.view-price-panel span.price"
            ]
            
            price = None
            for sel in price_selectors:
                element = page.locator(sel).first
                if element.is_visible():
                    price = element.inner_text().strip()
                    if price: break
            
            if price:
                output_msg = f"【価格通知】\n現在の最安価格は {price} です。\n{target_url}"
                print(f"取得成功: {price}")
                send_line_message(output_msg)
            else:
                # 取得できなかった場合のデバッグ情報
                print("❌ 価格要素が特定できませんでした")
                send_line_message("⚠️ 価格の場所が見つかりませんでした。再度実行してみてください。")
                
        except Exception as e:
            error_detail = f"⚠️ エラー発生:\n{str(e)}"
            print(error_detail)
            send_line_message(error_detail)
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()