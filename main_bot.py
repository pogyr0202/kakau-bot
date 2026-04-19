import os
import requests
from playwright.sync_api import sync_playwright

# GitHubのSettings > Secretsで設定した値を取得
LINE_TOKEN = os.environ.get('LINE_TOKEN')

def send_line_notify(message):
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {LINE_TOKEN}'}
    data = {'message': message}
    requests.post(line_notify_api, headers=headers, data=data)

def check_price():
    with sync_playwright() as p:
        # ブラウザの起動（GitHub Actions上ではheadless=Trueが必須）
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(user_agent="Mozilla/5.0...").new_page()
        
        try:
            # 例としてAmazonの商品ページ（URLは適宜書き換えてください）
            target_url = "https://www.amazon.co.jp/dp/B0CHX43N6C" 
            page.goto(target_url, wait_until="domcontentloaded")
            
            # 価格を取得（サイトに合わせてセレクタを調整してください）
            # 下記は一般的なAmazonの価格表示クラスの例です
            price_element = page.query_selector(".a-price-whole")
            
            if price_element:
                price = price_element.inner_text().replace(',', '').replace('￥', '').strip()
                message = f"\n【価格通知】\n現在の価格は {price}円 です。\nURL: {target_url}"
                send_line_notify(message)
            else:
                send_line_notify("\n価格の取得に失敗しました。サイトの構造が変わった可能性があります。")
                
        except Exception as e:
            send_line_notify(f"\nエラーが発生しました:\n{str(e)}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    if not LINE_TOKEN:
        print("エラー: LINE_TOKENが設定されていません。")
    else:
        check_price()