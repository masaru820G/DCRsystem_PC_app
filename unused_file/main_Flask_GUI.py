# -------------------------------------------------
# DCR_systemをノートPCで実行するためのmain文
#・YOLOで検出したものを「pyside」で作成したGUIに表示（カメラ4つ）
#・GUIのボタン動作でラズパイに対応する命令を送る
#    └ "http://192.168.2.2:5000/[command]"
#・GUIのボタン動作でリレーボードの制御をする
#    └ ON/OFF
# -------------------------------------------------
import sys
import requests
import time
from PySide6.QtWidgets import (
    QApplication,    # アプリケーション全体を管理する
    QMainWindow,     # メインウィンドウ
    QWidget,         # 基本ウィジェット(サブウインドウ用)
    QVBoxLayout,    # 縦型レイアウト
    QLabel,          # テキストラベル
    QPushButton      # ボタン
)
from PySide6.QtCore import (
    Slot,            # 実行動作用
    Qt,              # キー操作できる
    QTimer
)
from PySide6.QtGui import (
    QKeyEvent,
    QImage,
    QPixmap
)
import module_patlite as p_ctr              # パトライト制御のモジュール
import module_relay as r_ctr                # リレーボード制御のclassモジュール
# ================================================
# 設定変数
# ================================================
RPI_IP_ADDRESS = "192.168.2.2"  # ラズパイのIPアドレス
RPI_PORT = 5000                 # ラズパイのポート番号

# --- スタイルシートテンプレート ---
"""
・  .setFixedSize(H, W)   :サイズ固定
・  .setStyleSheet("""
#font-family: " "                       #フォントの種類指定
#font-size: px;                         #フォントサイズ指定
#font-weight: bold;                     #太字に
#color: #000000;                        #文字カラー指定
#background-color: #FFFFFF;             #背景カラー指定
#border-radius: px;                     #角を丸く
#qproperty-alignment: 'AlignCenter';    #テキストを中央ぞろえ
""")
"""
# --- メインボタンスタイル ---
MAIN_BUTTON_STYLE = """
font-family: "Meiryo";
font-size: 30px;
font-weight: bold;
color: #00FFFF;
background-color: #333333;
border-radius: 60px;
"""
# --- メインラベルスタイル ---
MAIN_LABEL_STYLE = """
font-family: "Meiryo";
font-size: 40px;
font-weight: bold;
color: #000000;
background-color: #FFFFFF;
border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
# --- サブボタンスタイル ---
SUB_BUTTON_STYLE = """
font-family: "Meiryo";
font-size: 20px;
font-weight: bold;
color: #00FFFF;
background-color: #333333;
border-radius: 75px;
"""
# --- サブラベルスタイル ---
SUB_LABEL_STYLE = """
font-family: "Meiryo";
font-size: 15px;
font-weight: bold;
color: #000000;
background-color: #FFFFFF;
border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
# --- ステータスラベルスタイル ---
STATUS_LABEL_STYLE = """
font-size: 40px;
font-weight: bold;
color: #000000;
background-color: #adff2f;
qproperty-alignment: 'AlignCenter';
"""
# --- カメラ表示ラベル ---
CAM_WIDTH = 640
CAM_HEIGHT = 480
CAM_STYLE = """
background-color: #333333;
color: #FFFFFF;
font-size: 20px;
font-weight: bold;
border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
# ================================================
# スタートアップウィンドウ (ここを追加)
# ================================================
class StartupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("起動確認")
        self.setFixedSize(500, 300)
        self.setStyleSheet("background-color: #CCCCCC;") # 少しグレーな背景

        # メッセージラベル
        self.label_msg = QLabel("システムを開始しますか？", self)
        self.label_msg.setFixedSize(400, 50)
        self.label_msg.move(50, 50)
        self.label_msg.setStyleSheet("""
            font-family: "Meiryo";
            font-size: 24px;
            font-weight: bold;
            color: #333333;
            qproperty-alignment: 'AlignCenter';
        """)

        # 開始ボタン
        self.button_start = QPushButton("START SYSTEM", self)
        self.button_start.setFixedSize(260, 80)
        self.button_start.move(120, 150)
        # スタイルはメインのボタンと似た雰囲気で調整
        self.button_start.setStyleSheet("""
            font-family: "Meiryo";
            font-size: 24px;
            font-weight: bold;
            color: #FFFFFF;
            background-color: #FF4500;
            border-radius: 40px;
        """)

        # ボタンを押したらメイン画面へ遷移
        self.button_start.clicked.connect(self.launch_main_window)

    def launch_main_window(self):
        # メインウィンドウのインスタンスを作成
        self.main_window = MainWindow()
        # メインウィンドウを表示
        self.main_window.show()
        # 自分自身（スタートアップ画面）を閉じる
        self.close()
# ================================================
# エアー制御用サブウィンドウ
# ================================================
class SubWindowAir(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setWindowTitle("エアー制御ウィンドウ")
        self.setFixedSize(300, 300)
        self.setStyleSheet("background-color: #000000;") # 分かりやすく色を変更

        self.label_air_management = QLabel("戻るには「Restart」を押してください", self)
        self.label_air_management.setFixedSize(270, 20)
        self.label_air_management.setStyleSheet(SUB_LABEL_STYLE)
        self.label_air_management.move(15, 20)

        self.button_air_pause = QPushButton("Restart", self)
        self.button_air_pause.setFixedSize(150, 150)
        self.button_air_pause.setStyleSheet(SUB_BUTTON_STYLE)
        self.button_air_pause.move(75, 75)

        self.button_air_pause.clicked.connect(self.go_back)

    def go_back(self):
        self.parent_window.show()
        self.close()
# ================================================
# メインウィンドウ
# ================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__() # QMainWindowの初期化
        self.setWindowTitle("サクランボ病害虫除去システム（仮）")
        self.setFixedSize(1700, 990) # (幅, 高さ)
        self.setStyleSheet("background-color: #FFFFFF;")

        # --- カメララベル設定 ---
        self.label_camera_inside = QLabel("camera_inside", self)
        self.label_camera_inside.setFixedSize(CAM_WIDTH, CAM_HEIGHT)
        self.label_camera_inside.setStyleSheet(CAM_STYLE)

        self.label_camera_outside = QLabel("camera_outside", self)
        self.label_camera_outside.setFixedSize(CAM_WIDTH, CAM_HEIGHT)
        self.label_camera_outside.setStyleSheet(CAM_STYLE)

        self.label_camera_underside = QLabel("camera_underside", self)
        self.label_camera_underside.setFixedSize(CAM_WIDTH, CAM_HEIGHT)
        self.label_camera_underside.setStyleSheet(CAM_STYLE)

        self.label_camera_topside = QLabel("camera_topside", self)
        self.label_camera_topside.setFixedSize(CAM_WIDTH, CAM_HEIGHT)
        self.label_camera_topside.setStyleSheet(CAM_STYLE)

        # --- モーターラベル設定 ---
        self.label_motor_management = QLabel("モーター管理", self)
        self.label_motor_management.setFixedSize(300, 55)
        self.label_motor_management.setStyleSheet(MAIN_LABEL_STYLE)

        self.label_motor_status = QLabel("status", self)
        self.label_motor_status.setFixedSize(150, 45)
        self.label_motor_status.setStyleSheet(STATUS_LABEL_STYLE)

        # --- エアーラベル設定 ---
        self.label_air_management = QLabel("エアー状態", self)
        self.label_air_management.setFixedSize(300, 55)
        self.label_air_management.setStyleSheet(MAIN_LABEL_STYLE)

        # --- モーターボタン設定 ---
        self.button_motor_start = QPushButton("start", self)
        self.button_motor_start.setFixedSize(120, 120)
        self.button_motor_start.setStyleSheet(MAIN_BUTTON_STYLE)

        self.button_motor_stop = QPushButton("stop", self)
        self.button_motor_stop.setFixedSize(120, 120)
        self.button_motor_stop.setStyleSheet(MAIN_BUTTON_STYLE)

        # --- エアーボタン設定 ---
        self.button_air_pause = QPushButton("pause", self)
        self.button_air_pause.setFixedSize(120, 120)
        self.button_air_pause.setStyleSheet(MAIN_BUTTON_STYLE)

        # --- レイアウト（配置）の作成 ---
        self.label_camera_inside.move(20, 10)
        self.label_camera_outside.move(670, 10)
        self.label_camera_underside.move(20, 500)
        self.label_camera_topside.move(670, 500)

        # 操作パネル配置 (カメラの右側 X=1350付近へ移動)
        BASE_X = 1350  # 基準となるX座標

        self.label_motor_management.move(BASE_X + 30, 40)
        self.button_motor_start.move(BASE_X, 100)
        self.button_motor_stop.move(BASE_X + 200, 100)
        self.label_motor_status.move(BASE_X + 80, 220)

        self.label_air_management.move(BASE_X + 30, 530)
        self.button_air_pause.move(BASE_X + 120, 590)

        # --- シグナルとスロット（動作）の接続 ---
        self.button_motor_start.clicked.connect(self.on_button_clicked_start)
        self.button_motor_stop.clicked.connect(self.on_button_clicked_stop)
        self.button_air_pause.clicked.connect(self.open_sub_window_air)

    # --- 各動作 ---
    @Slot()
    def on_button_clicked_start(self):
        #send_rpi_command("/rotate")
        self.label_motor_status.setText("動作中")

    @Slot()
    def on_button_clicked_stop(self):
        #send_rpi_command("/stop")
        self.label_motor_status.setText("停止中")

    @Slot()
    def open_sub_window_air(self):
        # 自分自身(self)を渡すロジックは全く同じ
        self.sub_window_air = SubWindowAir(parent_window=self)
        self.sub_window_air.show()
        #self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        """ウィンドウがアクティブな時にキーが押されたら呼ばれる"""
        if event.key() == Qt.Key.Key_Q:     # qキーが押されたか確認
            print(" 'q' キーが押されたため、プログラムを終了します。")
            self.close()
        else:
            # 'q' 以外の場合は、親クラスのデフォルト動作を実行(ex Tab キーでのフォーカス移動など)
            super().keyPressEvent(event)

# ================================================
# ラズパイにコマンドを送る関数
# ================================================
def send_rpi_command(command):
    url = f"http://{RPI_IP_ADDRESS}:{RPI_PORT}{command}"

    try:
        print(f"Sending command [{url}] to Raspberry Pi")
        response = requests.get(url, timeout = 10)

        if response.status_code == 200:
            print("Command sent successfully.")
        else:
            print(f"Failed to send command. Status code: {response.status_code}")

    except requests.ConnectionError:
        print("[Error]: Couldn't access. check for IP address.")
    except requests.Timeout:
        print("[Error]: Timeout, not response")
    except requests.exceptions.RequestException as e:
        print(f"[Error]: sending command: {e}")



# --- アプリケーションの実行 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    startup_window = StartupWindow()
    startup_window.show()
    #window = MainWindow()
    #window.show()
    #RelayContoroller.open()

    #RelayContoroller.finish()
    sys.exit(app.exec())