import os
import requests
from playwright.sync_api import sync_playwright

def send_line_message(message):
    """Messaging APIを使用してLINEにメッセージを送る"""
    url = "https://api.line.me/v2/bot/message/push"
    
    # GitHubのSettings > Secretsで設定した名前を読み込みます
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    # どちらの設定が足りないかログに出力
    if not token:
        print("❌ エラー: LINE_CHANNEL_ACCESS_TOKEN がSecretsに設定されていません。")
    if not user_id:
        print("❌ エラー: USER_ID がSecretsに設定されていません。")
    
    if not token or not user_id:
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
        print(f"LINE API Response Status: {response.status_code}")
        if response.status_code != 200:
            print(f"LINEからのエラーメッセージ: {response.text}")
        response.raise_for_status()
        print("✅ LINEへのメッセージ送信に成功しました！")
    except Exception as e:
        print(f"❌ LINE送信失敗: {e}")

def check_price():
    """価格をチェックするメイン処理"""
    # 対象URL: iPhone 15 128GB クッキー
    target_url = "https://kakaku.com/item/K0001540961/" 
    
    with sync_playwright() as p:
        # User-Agentを設定して「ロボット感」を減らし、ブロックを防ぎます
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"URLにアクセス中: {target_url}")
            # ページ読み込み完了を待つ
            page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # 価格.comの最新の価格表示部分を狙い撃ち
            # 1. 最安価格の数値部分 2. 税込価格 などの候補を順に探す
            selectors = [
                "span.priceTxt", 
                "span[itemprop='price']",
                ".p-main_price_value",
                "#price-box .price"
            ]
            
            price = None
            for selector in selectors:
                element = page.locator(selector).first
                if element.is_visible():
                    price = element.inner_text().strip()
                    break
            
            if price:
                message = f"【価格通知】\n現在の最安価格は {price} です。\n{target_url}"
                print(f"取得成功: {price}")
                send_line_message(message)
            else:
                # 画面のスクリーンショットを撮ってログに残す（デバッグ用）
                print("❌ 価格要素が見つかりませんでした。")
                send_line_message("⚠️ 価格.comのサイト構造が変わったため、価格を取得できませんでした。")
                
        except Exception as e:
            error_msg = f"⚠️ エラー発生:\n{str(e)}"
            print(error_msg)
            send_line_message(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()