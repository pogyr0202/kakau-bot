import os
import requests
import json
import time
from playwright.sync_api import sync_playwright

def send_line_message(message):
    """Messaging APIを使用してLINEにメッセージを送る"""
    url = "https://api.line.me/v2/bot/message/push"
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    if not token or not user_id:
        print("⚠️ Secretsの設定が読み込めていません")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"LINE送信結果: {response.status_code}")
    except Exception as e:
        print(f"❌ LINE送信エラー: {e}")

def check_price():
    """価格をチェックするメイン処理"""
    target_url = "https://kakaku.com/item/K0001540961/" 
    
    with sync_playwright() as p:
        # ブラウザの設定をさらに厳重に「人間化」
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale="ja-JP"
        )
        page = context.new_page()
        
        try:
            print(f"URLにアクセス開始: {target_url}")
            # ページを完全に読み込み、少し待つ
            page.goto(target_url, wait_until="networkidle", timeout=60000)
            time.sleep(5) 
            
            # デバッグ用：今見ているページのタイトルを表示（「ロボット確認」になっていないかチェック）
            print(f"現在のページタイトル: {page.title()}")

            price = None

            # 対策1：HTML内の「隠しデータ（JSON-LD）」から価格を探す（これが一番確実）
            script_tags = page.locator('script[type="application/ld+json"]').all()
            for tag in script_tags:
                try:
                    data = json.loads(tag.inner_text())
                    # Offer（価格情報）が含まれているか確認
                    if "offers" in data:
                        price = data["offers"].get("lowPrice") or data["offers"].get("price")
                        if price:
                            price = f"¥{int(price):,}" # 数字を「¥150,000」形式に変換
                            print(f"隠しデータから価格を発見: {price}")
                            break
                except:
                    continue

            # 対策2：通常の画面上の文字から探す（スペア）
            if not price:
                price_selectors = [
                    "span.priceTxt",
                    ".p-main_price_value",
                    "div.view-price-panel span.price",
                    "span[itemprop='price']"
                ]
                for sel in price_selectors:
                    element = page.locator(sel).first
                    if element.is_visible():
                        price = element.inner_text().strip()
                        print(f"画面上の要素から価格を発見: {price}")
                        break

            if price:
                output_msg = f"【価格通知】\n現在の価格は {price} です。\n{target_url}"
                send_line_message(output_msg)
            else:
                # 取得失敗時の詳細ログ
                print("❌ 価格を見つけられませんでした。")
                send_line_message(f"⚠️ 価格の取得に失敗しました。\n現在のタイトル: {page.title()}\nURLを再確認してください。")
                
        except Exception as e:
            error_detail = f"⚠️ 実行エラー:\n{str(e)}"
            print(error_detail)
            send_line_message(error_detail)
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()