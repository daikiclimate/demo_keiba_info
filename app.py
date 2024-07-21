import os
import unicodedata
from os.path import dirname, join

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# set_configする。layoutをwideにする。
st.set_page_config(layout="wide")


def text_normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return text


dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)
DEMO_USER = os.environ.get("DEMO_USER")
PASSWORD = os.environ.get("PASSWORD")

with st.sidebar:
    login_option = st.selectbox(
        "ログインする？",
        (
            "フリー機能",
            "ログイン",
        ),
    )
    if login_option == "ログイン":
        password = st.text_input("パスワード", value=PASSWORD)


def get_place_list():
    place_list = [
        "札幌",
        "函館",
        "福島",
        "新潟",
        "東京",
        "中山",
        "中京",
        "京都",
        "阪神",
        "小倉",
    ]
    return place_list


def id2race_place(place):
    if place == "札幌":
        place_id = "01"
    elif place == "函館":
        place_id = "02"
    elif place == "福島":
        place_id = "03"
    elif place == "新潟":
        place_id = "04"
    elif place == "東京":
        place_id = "05"
    elif place == "中山":
        place_id = "06"
    elif place == "中京":
        place_id = "07"
    elif place == "京都":
        place_id = "08"
    elif place == "阪神":
        place_id = "09"
    elif place == "小倉":
        place_id = "10"
    return place_id


with st.container():
    if login_option == "ログイン":
        if password == PASSWORD:
            tab_get, tab_check = st.tabs(["データ取得", "データ確認"])
            with tab_get:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    year = st.text_input("年", value="2024")
                with col2:
                    place = st.selectbox("競馬場名", get_place_list())
                with col3:
                    # その競馬場の01-06回で何回目の開催かを取得。
                    times = st.selectbox("何回目", ["01", "02", "03", "04", "05", "06"])
                with col4:
                    days = st.selectbox(
                        "何日目",
                        [
                            "01",
                            "02",
                            "03",
                            "04",
                            "05",
                            "06",
                            "07",
                            "08",
                            "09",
                            "10",
                            "11",
                            "12",
                        ],
                    )

                get_button = st.button("取得する")
                if get_button:
                    race_id = year + id2race_place(place) + times + days
                    race_id += "01"
                    url = "https://db.netkeiba.com/race/" + race_id

                    url = f"https://race.netkeiba.com/race/shutuba_past.html?race_id={race_id}&rf=shutuba_submenu"
                    st.write(url)
                    response = requests.get(url)

                    soup = BeautifulSoup(response.content, "html.parser")

                    table = soup.find("table", {"class": "Shutuba_Table"})

                    # ヘッダーを取得
                    headers = table.find_all("th")

                    # 列名を抽出
                    columns = [header.text.strip() for header in headers]
                    # st.write(columns)
                    # print(columns)

                    # 行データを抽出
                    rows = table.find_all("tr", {"class": "HorseList"})

                    # データを格納するためのリストを作成
                    data = []

                    # 各行のデータを取得してリストに追加
                    for row in rows:
                        row_data = {}
                        cells = row.find_all(["td", "th"])
                        for i, cell in enumerate(cells):

                            if i == 0:
                                row_data[columns[i]] = (
                                    cell.text.strip()
                                )  # .find('td', class_='Waku').text

                            #     row_data[columns[i]] = cell.find('div').text.strip()  # 枠

                            elif i == 1:
                                row_data[columns[i]] = cell.text.strip()  # 馬番
                            elif i == 2:
                                # row_data[columns[i]] = cell.text.strip()  # 印
                                pass
                            elif i == 3:
                                print("---")
                                print(f"{i}|{cell}")
                                row_data["馬名"] = (
                                    cell.find("div", class_="Horse02")
                                    .text.replace("\n", "")
                                    .replace(" ", "")
                                )  # 馬名
                                horse_weight_data = (
                                    cell.find("div", class_="Weight color-red")
                                    .text.replace("\n", "")
                                    .replace(" ", "")
                                )  # 馬名
                                horse_weight = int(horse_weight_data.split("kg")[0])
                                horse_weight_diff = int(
                                    horse_weight_data.split("kg")[1]
                                    .replace("(", "")
                                    .replace(")", "")
                                )
                                row_data["馬体重"] = horse_weight
                                row_data["馬体重変化"] = int(horse_weight_diff)
                                race_span = cell.find("div", class_="Horse06 fc").text
                                row_data["レース間隔"] = race_span[1:]
                                row_data["推定脚質"] = race_span[0]

                            elif i == 4:
                                # row_data[columns[i]] = cell.text.strip()  # 騎手斤量
                                row_data["性別"] = cell.text.strip().split("\n")[0][0]
                                row_data["馬齢"] = int(
                                    cell.text.strip().split("\n")[0][1]
                                )
                                row_data["騎手"] = cell.text.strip().split("\n")[2]
                                row_data["斤量"] = float(
                                    cell.text.strip().split("\n")[3]
                                )

                            elif i >= 5 and i <= 9:
                                prefix = f"{columns[i]}_"
                                base_text = cell.text.strip()
                                base_text = text_normalize(base_text)
                                if base_text == "":
                                    row_data[prefix + "日付"] = ""
                                    row_data[prefix + "競馬場"] = ""
                                    row_data[prefix + "着順"] = 0
                                elif not base_text[0].isnumeric():  # 近親のこと
                                    row_data[prefix + "日付"] = ""
                                    row_data[prefix + "競馬場"] = ""
                                    row_data[prefix + "着順"] = 0
                                else:
                                    print(base_text.split("\n")[0].split(" "))
                                    row_data[prefix + "日付"] = base_text.split("\n")[
                                        0
                                    ].split(" ")[0]
                                    row_data[prefix + "競馬場"] = base_text.split("\n")[
                                        0
                                    ].split(" ")[1]
                                    row_data[prefix + "着順"] = int(
                                        base_text.split("\n")[1]
                                    )

                        data.append(row_data)
                    data = pd.DataFrame(data)
                    st.table(data)
