# -------------------------------------------------
# main.py : 動作ロジック記述ファイル (完全非同期・スレッド分離版)
# -------------------------------------------------
import sys
import requests
import time

# QThreadPool, QRunnable を追加
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Slot, Qt, QRunnable, QThreadPool
from PySide6.QtGui import QKeyEvent

# デザインファイルを読み込む
import module_view

# 制御モジュール
import module_patlite as p_ctr
# import module_relay as r_ctr

RPI_IP_ADDRESS = "192.168.2.2"
RPI_PORT = 5000

# ==========================================================
# ★追加クラス：通信を裏で行う作業員 (Worker)
# ==========================================================
class NetworkWorker(QRunnable):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        """
        このメソッドの中身はメインのGUIとは別の世界(スレッド)で実行されます。
        ここで数秒待機が発生しても、画面は止まりません。
        """
        try:
            print(f" >> [Background Sending]: {self.url}")
            # ここで通信！ (タイムアウトを短めに設定)
            response = requests.get(self.url, timeout=2)
            print(f" << [Response]: {response.status_code}")
        except Exception as e:
            print(f" !! [Network Error]: {e}")

# ==========================================================
# スタートアップウィンドウ
# ==========================================================
class StartupWindow(module_view.StartupWindowUI):
    def __init__(self):
        super().__init__()
        self.button_start.clicked.connect(self.launch_main)
    def launch_main(self):
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

# ==========================================================
# メインウィンドウ
# ==========================================================
class MainWindow(module_view.MainWindowUI):
    def __init__(self):
        super().__init__()
        # ★重要：スレッド管理プールの作成
        self.thread_pool = QThreadPool()
        print(f"Multithreading initialized. Max threads: {self.thread_pool.maxThreadCount()}")
        # トグルスイッチの接続 ---
        self.toggle.toggled.connect(self.on_main_toggled)
        # 設定ボタンの接続
        self.button_setting.clicked.connect(self.on_setting_button)
        # 電源ボタンの接続
        self.button_power.clicked.connect(self.on_power_bottom)

    # --- トグルスイッチ状態変更イベント --------------------------
    @Slot(bool)
    def on_main_toggled(self, checked):
        # 1. まず見た目を瞬時に更新 (待たない)
        if checked:
            print("Action: Switch ON")
            self.label_toggle_status.setText("動作中")
            self.label_toggle_status.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #32CD32; qproperty-alignment: 'AlignCenter';
            """)
            # 2. 裏でコマンド送信 (非同期)
            #self.send_async("/rotate")
        else:
            print("Action: Switch OFF")
            self.label_toggle_status.setText("停止中")
            self.label_toggle_status.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #888888; qproperty-alignment: 'AlignCenter';
            """)
            # 2. 裏でコマンド送信 (非同期)
            #self.send_async("/stop")
            #self.r_ctr.stop()  # リレーボード停止

    # --- 設定ボタン押下イベント -------------------
    @Slot()
    def on_setting_button(self):
        self.settings_window = SubWindow(parent_window=self)
        self.settings_window.show()
        print("設定ボタンが押されました。")

    # --- 電源ボタン押下イベント -------------------
    @Slot()
    def on_power_bottom(self):
        print("電源ボタンが押されました。終了します。")
        p_ctr.close_patlite()           # 画面を閉じる前に、PATLITEを閉じる
        #r_ctr.close_relay()             # 画面を閉じる前に、リレーボードを閉じる
        self.close()                    # アプリケーションを閉じる

    # --- 非同期でコマンドを送る関数-------------------
    def send_async(self, command):
        """
        GUIを止めずにラズパイへコマンドを送るための関数
        requests.get を直接書かず、必ずこれを通してください。
        """
        url = f"http://{RPI_IP_ADDRESS}:{RPI_PORT}{command}"
        # 作業員(Worker)を作成して、プールに投げる
        worker = NetworkWorker(url)
        self.thread_pool.start(worker)

    # --- キー入力イベント ------------------------------------------
    def keyPressEvent(self, event: QKeyEvent):
        # [1] キーで「カビ（紫）」
        if event.key() == Qt.Key.Key_1:
            print("Key input: 1 -> カビ")
            self.label_dam.setText("カビ")
            self.label_dam.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #FFFFFF; background-color: #800080; border-radius: 5px;
                border: 2px solid #000000;
                qproperty-alignment: 'AlignCenter';
            """)
            # もしここでも通信するなら: self.send_async("/detect_mold")
            p_ctr.set_patlite_color(p_ctr.LedPattern.VIOLET)
        # [2] キーで「未熟果（黄色）」
        elif event.key() == Qt.Key.Key_2:
            print("Key input: 2 -> 未熟果")
            self.label_dam.setText("未熟果")
            self.label_dam.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #000000; background-color: #FFFF00; border-radius: 5px;
                border: 2px solid #000000;
                qproperty-alignment: 'AlignCenter';
            """)
            # もしここでも通信するなら: self.send_async("/detect_unripe")
            p_ctr.set_patlite_color(p_ctr.LedPattern.YELLOW)
        else:
            super().keyPressEvent(event)

# ==========================================================
# サブウィンドウ
# ==========================================================
class SubWindow(module_view.SubWindowUI):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.button_back.clicked.connect(self.go_back)
    def go_back(self):
        self.parent_window.show()
        self.close()

# ==========================================================
# 実行ブロック
# ==========================================================
if __name__ == "__main__":
    p_ctr.init_patlite()
    app = QApplication(sys.argv)
    window = StartupWindow()
    window.show()
    sys.exit(app.exec())
