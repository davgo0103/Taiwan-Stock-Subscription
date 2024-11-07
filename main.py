import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import date, datetime

# URL
url = "https://stock.wespai.com/draw"

# Discord Webhook URL
webhook_url = "<YOUR_DISCORD_WEBHOOK_URL>?wait=true"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Accept-Language": "zh-TW,en;q=0.9",
}

def get_data(url):
    """
    取得資料並篩選符合日期範圍的項目
    回傳一個 pandas dataframe
    """
    resp = requests.get(url, headers=headers)
    
    if resp.status_code != 200:
        print(f"Failed to retrieve data, status code: {resp.status_code}")
        return pd.DataFrame()
    
    soup = BeautifulSoup(resp.text, 'html5lib')
    tbody = soup.find('tbody')
    
    if not tbody:
        print("Error: <tbody> not found in the HTML page.")
        return pd.DataFrame()

    data = []
    trs = tbody.find_all('tr')
    current_date = datetime.now().date()
    
    for tr in trs:
        cells = tr.find_all('td')
        if len(cells) < 16:
            continue

        stock_info = {
            "抽籤日期": cells[0].text.strip(),
            "代號": cells[1].text.strip(),
            "公司": cells[2].text.strip(),
            "發行市場": cells[3].text.strip(),
            "申購起日": cells[4].text.strip(),
            "申購迄日": cells[5].text.strip(),
            "撥券日期": cells[6].text.strip(),
            "承銷張數": cells[7].text.strip(),
            "承銷價": cells[8].text.strip(),
            "收盤價": cells[9].text.strip(),
            "報酬率(%)": cells[10].text.strip(),
            "賺賠": cells[11].text.strip(),
            "申購張數": cells[12].text.strip(),
            "需有多少錢才能抽": cells[13].text.strip(),
            "總合格件": cells[14].text.strip(),
            "中籤率(%)": cells[15].text.strip()
        }

        try:
            start_date = datetime.strptime(stock_info["申購起日"], "%m/%d").replace(year=current_date.year).date()
            end_date = datetime.strptime(stock_info["申購迄日"], "%m/%d").replace(year=current_date.year).date()
        except ValueError:
            continue 

        if start_date <= current_date <= end_date:
            data.append(stock_info)

    # 定義欄位名稱
    columns = [
        '抽籤日期', '代號', '公司', '發行市場', '申購起日', '申購迄日', '撥券日期', '承銷張數',
        '承銷價', '收盤價', '報酬率(%)', '賺賠', '申購張數', '需有多少錢才能抽', '總合格件', '中籤率(%)'
    ]
    df = pd.DataFrame(data, columns=columns)
    df['報酬率(%)'] = pd.to_numeric(df['報酬率(%)'], errors='coerce')

    # 篩選: 報酬率 > 10%
    # df = df[df['報酬率(%)'] > 10]
    return df

def send_or_edit_discord_message(data):
    try:
        with open("message_id.json", "r") as f:
            message_info = json.load(f)
            message_id = message_info.get("message_id")
    except (FileNotFoundError, json.JSONDecodeError):
        message_id = None

    description = ""
    for index, row in data.iterrows():
        description += (
            f"### **{row['公司']} - 代號： {row['代號']}**\n"
            f"```報酬率: {row['報酬率(%)']}%\n"
            f"申購時間: {row['申購起日']} ~ {row['申購迄日']}\n"
            f"抽籤日期: {row['抽籤日期']}\n"
            f"承銷價: {row['承銷價']}\n"
            f"收盤價: {row['收盤價']}\n"
            f"馬上賣掉賺賠: {row['賺賠']}\n"
            f"要準備的摳摳: {row['需有多少錢才能抽']}```\n"
        )
    description += "-# 投資一定有風險，請謹慎評估自己的風險承受能力\n-# 資料僅供參考，不構成投資建議"
    

    embed = {
        "title": "抽獎囉!!! 🤑",
        "description": description.strip(),
        "color": 5814783,
        "footer": {"text": f"小蔡開發! 祝你賺大錢 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}","icon_url": "https://i.imgur.com/Bx4sGZ1.jpg"}
    }

    payload = {"embeds": [embed]}

    # 編輯或發送新的訊息
    if message_id:
        # 編輯現有訊息
        edit_url = f"{webhook_url.rsplit('?', 1)[0]}/messages/{message_id}"
        response = requests.patch(edit_url, json=payload)
        if response.status_code == 200:
            print("訊息已成功更新")
        else:
            print(f"訊息更新失敗，狀態碼: {response.status_code}")
    else:
        # 發送新訊息並儲存訊息 ID
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200 or response.status_code == 204:
            # 儲存訊息 ID
            message_id = response.json().get("id")
            with open("message_id.json", "w") as f:
                json.dump({"message_id": message_id}, f)
            print("訊息已成功發送並儲存 ID")
        else:
            print(f"訊息發送失敗，狀態碼: {response.status_code}")

def main():
    df = get_data(url)
    if df.empty:
        print("No data retrieved.")
        return
    send_or_edit_discord_message(df)
    print(df)

if __name__ == "__main__":
    main()
