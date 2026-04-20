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
    # URLの末尾に余計なものが付かないよう、変数をクリーンにします
    target_url = "https://kakaku.com/item/K0001540961/"
    
    with sync_playwright() as p:
        # iPhone 15 Pro としてアクセスを装う最強の「なりすまし」設定
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
            viewport={'width': 390, 'height': 844},
            locale="ja-JP",
            extra_http_headers={
                "Referer": "https://www.google.com/", # Googleから来たように見せかける
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
            }
        )
        page = context.new_page()
        
        try:
            print(f"URLにアクセス開始: {target_url}")
            # タイムアウトを長めに設定し、完全に読み込まれるまで待機
            response = page.goto(target_url, wait_until="load", timeout=60000)
            
            # 5秒待機（JavaScriptが動いて価格が出るまでの時間）
            time.sleep(5) 
            
            print(f"現在のページタイトル: {page.title()}")
            print(f"ステータスコード: {response.status}")

            price = None

            # 方法1：隠しデータ（JSON-LD）から抽出を試みる
            script_tags = page.locator('script[type="application/ld+json"]').all()
            for tag in script_tags:
                try:
                    data = json.loads(tag.inner_text())
                    # 商品情報の中の価格データを探す
                    if isinstance(data, list): data = data[0]
                    offers = data.get("offers")
                    if offers:
                        raw_price = offers.get("lowPrice") or offers.get("price")
                        if raw_price:
                            price = f"¥{int(raw_price):,}"
                            print(f"隠しデータから発見: {price}")
                            break
                except:
                    continue

            # 方法2：スマホ版サイトのセレクタで抽出を試みる
            if not price:
                price_selectors = [
                    ".p-main_price_value", 
                    ".price", 
                    ".priceTxt",
                    "span[itemprop='price']"
                ]
                for sel in price_selectors:
                    element = page.locator(sel).first
                    if element.is_visible():
                        price = element.inner_text().strip()
                        print(f"画面要素から発見: {price}")
                        break

            if price:
                output_msg = f"【価格通知】\n現在の価格は {price} です。\n{target_url}"
                send_line_message(output_msg)
            else:
                # 404ページ等に飛ばされている場合の通知
                print("❌ 価格を見つけられませんでした。")
                if "見つかりません" in page.title():
                    send_line_message("⚠️ サイトからブロック（404誘導）されました。対策を更新します。")
                else:
                    send_line_message(f"⚠️ 価格が見つかりません。\nタイトル: {page.title()}")
                
        except Exception as e:
            error_detail = f"⚠️ 実行エラー:\n{str(e)}"
            print(error_detail)
            send_line_message(error_detail)
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()