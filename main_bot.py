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
    # ターゲットURL
    target_url = "https://kakaku.com/item/K0001540961/"
    
    with sync_playwright() as p:
        # ブラウザの起動オプションを調整
        browser = p.chromium.launch(headless=True)
        
        # 【重要】日本の一般的なiPhoneユーザーを完全に模倣する設定
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
            viewport={'width': 390, 'height': 844},
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.google.co.jp/"
            }
        )
        page = context.new_page()
        
        try:
            print(f"URLにアクセス開始: {target_url}")
            
            # サイト側に怪しまれないよう、ランダムな待ち時間を入れながらアクセス
            response = page.goto(target_url, wait_until="load", timeout=60000)
            time.sleep(7) # 読み込み時間をさらに長く確保
            
            print(f"現在のページタイトル: {page.title()}")
            print(f"ステータスコード: {response.status}")

            price = None

            # 方法1：構造化データ（JSON-LD）から価格を抜き出す（ボット対策を回避しやすい）
            scripts = page.locator('script[type="application/ld+json"]').all()
            for script in scripts:
                try:
                    content = script.inner_text()
                    if '"offers"' in content:
                        data = json.loads(content)
                        if isinstance(data, list): data = data[0]
                        offers = data.get("offers", {})
                        raw_price = offers.get("lowPrice") or offers.get("price")
                        if raw_price:
                            price = f"¥{int(raw_price):,}"
                            print(f"JSONから発見: {price}")
                            break
                except:
                    continue

            # 方法2：HTML要素から直接探す
            if not price:
                selectors = [".p-main_price_value", ".priceTxt", "span[itemprop='price']", ".price"]
                for sel in selectors:
                    element = page.locator(sel).first
                    if element.is_visible():
                        price = element.inner_text().strip()
                        print(f"HTML要素から発見: {price}")
                        break

            if price:
                output_msg = f"【価格通知】\n現在の最安価格は {price} です。\n{target_url}"
                send_line_message(output_msg)
            else:
                # 失敗時の詳細をLINEに送る
                print("❌ 価格取得に失敗")
                if response.status == 404:
                    send_line_message(f"⚠️ サイトから拒否(404)されました。GitHub ActionsのサーバーIPがブロックされている可能性があります。")
                else:
                    send_line_message(f"⚠️ 価格が見つかりません。\nタイトル: {page.title()}\nStatus: {response.status}")
                
        except Exception as e:
            print(f"⚠️ 実行エラー: {str(e)}")
            send_line_message(f"⚠️ 実行エラーが発生しました。")
        finally:
            browser.close()

if __name__ == "__main__":
    check_price()