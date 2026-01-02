# -------------------------------------------------
# main.py : 動作ロジック記述ファイル (完全非同期・スレッド分離版)
# -------------------------------------------------
import sys
import requests
import time
import random

# QThreadPool, QRunnable を追加
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Slot, Qt, QRunnable, QThreadPool
from PySide6.QtGui import QKeyEvent

# デザインファイルを読み込む
import module_gui

# 制御モジュール
import module_patlite as p_ctr
# import module_relay as r_ctr

RPI_IP_ADDRESS = "192.168.2.2"
RPI_PORT = 5000

# ==========================================================
# 汎用バックグラウンドタスク用クラス
# ==========================================================
class TaskWorker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.func(*self.args, **self.kwargs)            # 渡された関数を実行 (引数付き)
        except Exception as e:
            print(f" !! [Background Task Error]: {e}")

# ==========================================================
# スタートアップウィンドウ
# ==========================================================
class StartupWindow(module_gui.StartupWindowUI):
    def __init__(self):
        super().__init__()
        self.button_start.clicked.connect(self.launch_main)
    def launch_main(self):
        self.main_window = MainWindow()
        self.main_window.showFullScreen()
        self.close()

# ==========================================================
# メインウィンドウ
# ==========================================================
class MainWindow(module_gui.MainWindowUI):
    def __init__(self):
        super().__init__()
        # スレッド管理プールの作成
        self.thread_pool = QThreadPool()
        print(f"Multithreading initialized. Max threads: {self.thread_pool.maxThreadCount()}")
        # トグルスイッチの接続 ---
        self.toggle_switch.toggled.connect(self.on_main_toggled)
        # 設定ボタンの接続
        self.button_setting.clicked.connect(self.on_setting_button)
        # 電源ボタンの接続
        self.button_power.clicked.connect(self.on_power_bottom)

        self.saved_speed = 5        # 速度設定値を記憶しておく変数 初期値5

        # 履歴管理用の変数
        self.history_data = []  # 履歴データリスト [(id, result, conf), ...]
        self.current_id = 1     # IDカウンタ
        # 初期表示の更新
        #self.update_history_display()

    # --- バックグラウンドで関数を実行するヘルパー関数 ---
    def run_in_background(self, func, *args, **kwargs):
        """
        渡された関数をスレッドプールで実行します。
        例: self.run_in_background(p_ctr.set_patlite_color, "RED")
        """
        worker = TaskWorker(func, *args, **kwargs)
        self.thread_pool.start(worker)

    # --- ラズパイと通信する関数 -------------------
    def __async_raspi_request(self, command):
        url = f"http://{RPI_IP_ADDRESS}:{RPI_PORT}{command}"
        try:
            print(f" >> [Sending]: {url}")
            requests.get(url, timeout=2)
            print(" << [Sent]")
        except Exception as e:
            print(f" !! [Net Error]: {e}")

    # --- 設定ボタン押下イベント -------------------
    @Slot()
    def on_setting_button(self):
        self.settings_window = SubWindow(parent_window=self, initial_speed=self.saved_speed)
        self.settings_window.show()

    # --- 電源ボタン押下イベント -------------------
    @Slot()
    def on_power_bottom(self):
        print("電源ボタンが押されました。終了します。")
        p_ctr.close_patlite()           # 画面を閉じる前に、PATLITEを閉じる
        #r_ctr.close_relay()             # 画面を閉じる前に、リレーボードを閉じる
        self.close()                    # アプリケーションを閉じる

    # --- 履歴表示を更新する関数 -------------------
    def update_history_display(self):
        header_id   = "　ＩＤ　"       # 全角4文字
        header_res  = "　　結果　　"   # 全角6文字
        header_conf = "　　信頼度　　" # 全角7文字
        display_text = f"|{header_id}|{header_res}|{header_conf}|\n"
        display_text += "|" + "－" * 4 + "|" + "－" * 6 + "|" + "－" * 7 + "|\n"

        for item in self.history_data:
            # [ID列] 右寄せ
            id_half = f"{item['id']:03}"
            id_full = id_half.translate(str.maketrans("0123456789", "０１２３４５６７８９"))
            # 幅合わせ: (4 - 文字数) 個の全角スペースを左に足す
            # 例: "　００１"
            id_str = "　" * (4 - len(id_full)) + id_full

            # [判定結果列] 右寄せ
            r_text = item['result']
            # 幅合わせ: (6 - 文字数) 個の全角スペースを左に足す
            res_str = "　" * (6 - len(r_text)) + r_text

            # [信頼度列] 右寄せ
            conf_half = f"{item['conf']}　％"
            conf_full = conf_half.translate(str.maketrans("0123456789", "０１２３４５６７８９"))
            # 幅合わせ: (7 - 文字数) 個の全角スペースを左に足す
            # 例: "　００１"
            conf_str = "　" * (7 - len(conf_full)) + conf_full

            # 行を結合して追加
            line = f"|{id_str}|{res_str}|{conf_str}|\n"
            display_text += line

        self.label_history.setText(display_text)

    # --- キー入力イベント ------------------------------------------
    def keyPressEvent(self, event: QKeyEvent):
        # トグルスイッチがOFFなら、処理しない
        if not self.toggle_switch.isChecked():
            super().keyPressEvent(event)
            return

        disease_name = ""
        pattern = None

        if event.key() == Qt.Key.Key_1:
            disease_name = "カビ"
            pattern = p_ctr.LedPattern.VIOLET
            self.label_dam.setText("カビ")
            self.label_dam.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #FFFFFF; background-color: #800080;
                border: 1px solid #000000;
                qproperty-alignment: 'AlignCenter';
            """)
            # もしここでも通信するなら: self.send_async("/detect_mold")
            self.run_in_background(p_ctr.set_patlite_color, p_ctr.LedPattern.VIOLET)    # 非同期で実行
        elif event.key() == Qt.Key.Key_2:
            disease_name = "未熟果"
            pattern = p_ctr.LedPattern.YELLOW
            self.label_dam.setText("未熟果")
            self.label_dam.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #000000; background-color: #FFFF00;
                border: 1px solid #000000;
                qproperty-alignment: 'AlignCenter';
            """)
            # もしここでも通信するなら: self.send_async("/detect_unripe")
            self.run_in_background(p_ctr.set_patlite_color, p_ctr.LedPattern.YELLOW)
        elif event.key() == Qt.Key.Key_3:
            disease_name = "健全果"
            pattern = p_ctr.LedPattern.WHITE
            self.label_dam.setText("健全果")
            self.label_dam.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #000000; background-color: #FFFFFF;
                border: 1px solid #000000;
                qproperty-alignment: 'AlignCenter';
            """)
            # もしここでも通信するなら: self.send_async("/detect_unripe")
            self.run_in_background(p_ctr.set_patlite_color, p_ctr.LedPattern.WHITE)

        # 判定処理が行われた場合のみ履歴更新
        if disease_name != "":
            # 1. パトライト制御 (非同期)
            self.run_in_background(p_ctr.set_patlite_color, pattern)
            # 2. 履歴データの追加処理
            confidence = random.randint(60, 95) # 信頼度ランダム (60~95)
            # 辞書として作成
            record = {
                "id": self.current_id,
                "result": disease_name,
                "conf": confidence
            }
            # リストに追加
            self.history_data.append(record)
            # 古いものを削除
            if len(self.history_data) > 7:
                self.history_data.pop(0)
            # IDを加算
            self.current_id += 1
            # 確認用ログ
            _, color_name = pattern
            print(f"Latest History: |ID: {record['id']:03} | 判定結果: {record['result']}({color_name}) | 信頼度: {record['conf']} %")
            # 画面更新
            self.update_history_display()
        else:
            super().keyPressEvent(event)

    # --- トグルスイッチ状態変更イベント --------------------------
    @Slot(bool)
    def on_main_toggled(self, checked):
        self.button_setting.set_locked(checked)
        if checked:
            self.label_toggle_status.setText("動作中")
            self.label_toggle_status.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #32CD32; qproperty-alignment: 'AlignCenter';
            """)
            # 2. 裏でコマンド送信 (非同期)
            #self.run_in_background(self.__async_raspi_request, "/rotate")
        else:
            self.label_toggle_status.setText("停止中")
            self.label_toggle_status.setStyleSheet("""
                font-family: "Meiryo"; font-size: 30px; font-weight: bold;
                color: #888888; qproperty-alignment: 'AlignCenter';
            """)
            # 2. 裏でコマンド送信 (非同期)
            #self.run_in_background(self.__async_raspi_request, "/stop")
            #self.run_in_background(r_ctr.stop)  # リレーボード停止

# ==========================================================
# サブウィンドウ
# ==========================================================
class SubWindow(module_gui.SubWindowUI):
    # --- 戻るボタン押下イベント -------------------
    def __init__(self, parent_window, initial_speed):
        super().__init__()
        self.button_up_speed.clicked.connect(self.on_up_speed)
        self.button_down_speed.clicked.connect(self.on_down_speed)
        self.parent_window = parent_window
        self.button_back.clicked.connect(self.go_back)

        # スピード値の管理と初期化
        self.current_speed = initial_speed  # 親ウィンドウから現在の速度を受け取る変数
        self.update_speed_ui()  # 画面更新

    # --- 画面の表示とボタンの状態を更新する関数 ---
    def update_speed_ui(self):
        # 1. ラベルの数字を更新
        self.label_current_speed.setText(str(self.current_speed))

        # 2. 上限チェック (10になったらUpボタンをロック)
        if self.current_speed >= 10:
            self.button_up_speed.set_locked(True)   # ロック＆半透明
        else:
            self.button_up_speed.set_locked(False)  # 解除

        # 3. 下限チェック (1になったらDownボタンをロック)
        if self.current_speed <= 1:
            self.button_down_speed.set_locked(True) # ロック＆半透明
        else:
            self.button_down_speed.set_locked(False)# 解除

    # --- speed upボタン押下イベント -------------------
    @Slot()
    def on_up_speed(self):
        if self.current_speed < 10:
            self.current_speed += 1
            self.parent_window.saved_speed = self.current_speed
            print(f"Pushed Speed UP: {self.current_speed}")
            self.update_speed_ui()

    # --- speed downボタン押下イベント -------------------
    @Slot()
    def on_down_speed(self):
        if self.current_speed > 1:
            self.current_speed -= 1
            self.parent_window.saved_speed = self.current_speed
            print(f"Pushed Speed DOWN: {self.current_speed}")
            self.update_speed_ui()

    # --- 戻るボタン押下イベント -------------------
    @Slot()
    def go_back(self):
        self.parent_window.showFullScreen()
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
