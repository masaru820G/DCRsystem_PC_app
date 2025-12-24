import os
import time
import sys
import cv2
from pypylon import pylon

#-----user settings------------------------------------------------------

#カメラのシリアルナンバーを入力
TARGET_SERIALS = [
    "25308967",     #上カメラ   シリアルナンバー
    "21905526",     #下カメラ   シリアルナンバー
    "25308969",     #内カメラ   シリアルナンバー
    "25308968"      #外カメラ   シリアルナンバー
]

# 保存設定
FOLDER_PARENT = "cam_video"     #動画保存する親フォルダ名
FOLDER_CHILD = [
    "cam_video_top",        #上カメラ動画保存先
    "cam_video_under",      #下カメラ動画保存先
    "cam_video_inside",     #内カメラ動画保存先
    "cam_video_outside"     #外カメラ動画保存先
]
#動画コーデック
VIDEO_CODEC = 'XVID'
VIDEO_EXIT = '.avi'

#カメラの諸設定
FRAME_WIDTH = 1280
FRAME_HEIGHT = 960
FRAME_SIZE = (FRAME_WIDTH, FRAME_HEIGHT)
FPS = 20.0

#------------------------------------------------------------------------
"""
関数名      ：setup_folders()
関数説明    ：保存先の親フォルダと子フォルダを作成、あれば何もしない
"""
def setup_folders():
    if not os.path.exists(FOLDER_PARENT):
        os.makedirs(FOLDER_PARENT)
        print(f"親フォルダ '{FOLDER_PARENT}' を作成しました。")

    paths = []
    for folder in FOLDER_CHILD:
        path = os.path.join(FOLDER_PARENT, folder)
        if not os.path.exists(path):
            os.makedirs(path)
        paths.append(path)
        print(f"子フォルダ '{path}' を作成しました。")
    print("親フォルダと子フォルダの存在を確認しました。")
    return paths

"""
関数名      ：combined_number()
関数説明    ：取得したシリアルナンバーからカメラを結びつける
"""
def combined_number():
    print("カメラをシリアルナンバーで検索中")
    

def main():
    #保存先フォルダの準備
    try:
        output_paths = setup_folders()
    except OSError as e:
        print(f"フォルダの作成に失敗：{e}")
        return
    
    # カメラオブジェクトの初期化
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    #Pypylonリソースを初期化
    tlFactory = pylon.TlFactory.GetInstance()
    devices = tlFactory.EnumerateDevices()

    # 保存した設定ファイル（.pfs）を読み込む
    pylon.FeaturePersistence.Load("path/to/your/settings.pfs", camera.GetNodeMap(), True)

    # これ以降、保存した設定でカメラが動作します

    if not devices:
        print("カメラが見つかりません。")
        return

    #シリアルナンバーに基づきカメラデバイスを紐づける
    #combined_number(devices)
    devices_to_use = []
    print("カメラをシリアルナンバーで検索中")
    for serial in TARGET_SERIALS:
        found = False
        for dev_info in devices:
            if dev_info.GetSerialNumber() == serial:
                devices_to_use.append(dev_info)
                print(f"発見：{serial} ({dev_info.GetModelName()})")
                found = True
                break
        if not found:
            print(f"警告：シリアルナンバー{serial}のカメラが見つかりません。")

    if len(devices_to_use) != len(TARGET_SERIALS):
        print(f"エラー：{len(TARGET_SERIALS)}台のカメラが必要です。（現在{len(devices_to_use)}台）")
        print("接続を確認してください。")
        return
