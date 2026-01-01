# -------------------------------------------------
# DCR_systemのGUIデザイン定義ファイル
# -------------------------------------------------
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QLabel, QPushButton, QCheckBox, QVBoxLayout
)
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QPixmap

# ==========================================================
# 定数定義
# ==========================================================
WINDOW_W, WINDOW_H = 1270, 700      # 1920×1080

MARGIN_X = 10                       # 画面の余白x
MARGIN_Y = 10                       # 画面の余白y

CAM_W = int(WINDOW_W / 3)           # カメラ表示サイズw
CAM_H = int(CAM_W * 0.78)           # カメラ表示サイズh

BASE_X = (MARGIN_X + CAM_W + 10) + CAM_W + 50   # システム管理エリア基準x
BASE_Y = WINDOW_H / 2 + 100                     # システム管理エリア基準y

TOGGLE_W = 250                      # トグルスイッチサイズw
TOGGLE_H = 125                      # トグルスイッチサイズh

SETTING_ICON_SIZE = 100               # 設定アイコンサイズ
POWER_ICON_SIZE = 100                  # 電源アイコンサイズ

# ==========================================================
# スタイル定義
# ==========================================================
MAIN_BUTTON_STYLE = """
font-family: "Meiryo"; font-size: 30px; font-weight: bold;
color: #00FFFF; background-color: #333333; border-radius: 60px;
"""
MAIN_LABEL_STYLE = """
font-family: "Meiryo"; font-size: 40px; font-weight: bold;
color: #000000; background-color: #FFFFFF; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
SUB_BUTTON_STYLE = """
font-family: "Meiryo"; font-size: 20px; font-weight: bold;
color: #00FFFF; background-color: #333333; border-radius: 75px;
"""
SUB_LABEL_STYLE = """
font-family: "Meiryo"; font-size: 15px; font-weight: bold;
color: #000000; background-color: #FFFFFF; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
PL_LABEL_STYLE = """
font-family: "Meiryo"; font-size: 30px; font-weight: bold;
color: #000000; background-color: #FFFFFF; border-radius: 5px;
border: 2px solid #000000;
qproperty-alignment: 'AlignCenter';
"""
STATUS_LABEL_STYLE = """
font-size: 24px; font-weight: bold; color: #000000;
background-color: #adff2f; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
CAM_STYLE = """
background-color: #333333; color: #FFFFFF;
font-size: 20px; font-weight: bold; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
TOGGLE_LABEL_STYLE = """
font-family: "Meiryo"; font-size: 24px; font-weight: bold;
color: #888888; qproperty-alignment: 'AlignCenter';
"""

# ==========================================================
# パス取得関数
# ==========================================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ==========================================
# クリック可能なラベルクラス
# ==========================================
class ClickableLabel(QLabel):
    # クリックされたときに発火するシグナル
    clicked = Signal()

    def mousePressEvent(self, event):
        # 左クリック時のみシグナル送信
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ==========================================
# ToggleSwitch クラス (部品)
# ==========================================
class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None, width=60, height=30):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)
        self._bg_color_off = QColor("#B0B0B0")
        self._bg_color_on = QColor("#32CD32")
        self._circle_color = QColor("#FFFFFF")
        self._position = 0.0
        self._animation = QPropertyAnimation(self, b"position")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.stateChanged.connect(self.setup_animation)

    @Property(float)
    def position(self): return self._position
    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def setup_animation(self, value):
        self._animation.stop()
        self._animation.setEndValue(1.0 if value else 0.0)
        self._animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width, height = self.width(), self.height()
        radius = height / 2

        # 背景色計算
        curr_col = QColor()
        r = self._bg_color_off.red() + (self._bg_color_on.red() - self._bg_color_off.red()) * self._position
        g = self._bg_color_off.green() + (self._bg_color_on.green() - self._bg_color_off.green()) * self._position
        b = self._bg_color_off.blue() + (self._bg_color_on.blue() - self._bg_color_off.blue()) * self._position
        curr_col.setRgb(int(r), int(g), int(b))

        painter.setBrush(QBrush(curr_col))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, radius, radius)

        # 丸の描画
        circle_r = radius - 3
        circle_x = radius + (width - 2*radius) * self._position
        painter.setBrush(QBrush(self._circle_color))
        painter.drawEllipse(QPointF(circle_x, radius), circle_r, circle_r)

    def hitButton(self, pos): return self.contentsRect().contains(pos)


# ==========================================
# スタートアップウインドウUI
# ==========================================
class StartupWindowUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("起動確認")
        self.setFixedSize(500, 300)
        self.setStyleSheet("background-color: #CCCCCC;")

        self.label_msg = QLabel("システムを開始しますか？", self)
        self.label_msg.setFixedSize(400, 50)
        self.label_msg.move(50, 50)
        self.label_msg.setStyleSheet("color: black; font-size: 24px; font-weight: bold;")

        self.button_start = QPushButton("START SYSTEM", self)
        self.button_start.setFixedSize(260, 80)
        self.button_start.move(120, 150)
        self.button_start.setStyleSheet("background-color: #FF4500; color: white; font-size: 24px; border-radius: 40px;")


# ==========================================
# サブウインドウUI
# ==========================================
class SubWindowUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("サブウィンドウ")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color: #EEEEEE;")

        self.label = QLabel("戻るには「Restart」を押してください", self)
        self.label.setFixedSize(270, 20)
        self.label.setStyleSheet(SUB_LABEL_STYLE)
        self.label.move(15, 20)

        self.button_back = QPushButton("Restart", self)
        self.button_back.setFixedSize(150, 150)
        self.button_back.setStyleSheet(SUB_BUTTON_STYLE)
        self.button_back.move(75, 75)


# ==========================================
# メインウインドウUI
# ==========================================
class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("サクランボ病害虫除去システム")
        self.setFixedSize(WINDOW_W, WINDOW_H)
        self.setStyleSheet("background-color: #FFFFFF;")

        # --- カメラ管理エリア ------------------------------
        # 配置座標
        cam_x_left = MARGIN_X
        cam_x_right = MARGIN_X + CAM_W + 10
        cam_y_upper = MARGIN_Y
        cam_y_lower = MARGIN_Y + CAM_H + 10

        self.cam_in = QLabel("camera_inside", self)
        self.cam_in.setFixedSize(CAM_W, CAM_H); self.cam_in.setStyleSheet(CAM_STYLE)
        self.cam_in.move(cam_x_left, cam_y_upper)

        self.cam_out = QLabel("camera_outside", self)
        self.cam_out.setFixedSize(CAM_W, CAM_H); self.cam_out.setStyleSheet(CAM_STYLE)
        self.cam_out.move(cam_x_right, cam_y_upper)

        self.cam_under = QLabel("camera_underside", self)
        self.cam_under.setFixedSize(CAM_W, CAM_H); self.cam_under.setStyleSheet(CAM_STYLE)
        self.cam_under.move(cam_x_left, cam_y_lower)

        self.cam_top = QLabel("camera_topside", self)
        self.cam_top.setFixedSize(CAM_W, CAM_H); self.cam_top.setStyleSheet(CAM_STYLE)
        self.cam_top.move(cam_x_right, cam_y_lower)


        # --- 設定エリア ------------------------------
        self.button_setting = ClickableLabel(self)
        self.button_setting.setFixedSize(SETTING_ICON_SIZE, SETTING_ICON_SIZE)
        # マウスを乗せたときに指カーソルにする
        self.button_setting.setCursor(Qt.PointingHandCursor)
        # 画面右端からマージンを取って配置 (x = WINDOW_W - アイコンサイズ - 余白)
        setting_x = WINDOW_W - SETTING_ICON_SIZE - 20
        setting_y = 40  # 上からの余白
        self.button_setting.move(setting_x, setting_y)
        # 画像読み込みとセット
        pixmap = QPixmap(resource_path("setting.png"))
        if not pixmap.isNull():
            # 画像をラベルのサイズに合わせてリサイズ（スムージング処理付き）
            scaled_pixmap = pixmap.scaled(
                self.button_setting.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.button_setting.setPixmap(scaled_pixmap)


        # --- 電源エリア ------------------------------
        self.button_power = ClickableLabel(self)
        self.button_power.setFixedSize(POWER_ICON_SIZE, POWER_ICON_SIZE)
        # マウスを乗せたときに指カーソルにする
        self.button_power.setCursor(Qt.PointingHandCursor)
        # 画面右端からマージンを取って配置 (x = WINDOW_W - アイコンサイズ - 余白)
        power_x = WINDOW_W - POWER_ICON_SIZE - 20
        power_y = 180  # 上からの余白
        self.button_power.move(power_x, power_y)
        # 画像読み込みとセット
        pixmap = QPixmap(resource_path("power_supply.png"))
        if not pixmap.isNull():
            # 画像をラベルのサイズに合わせてリサイズ（スムージング処理付き）
            scaled_pixmap = pixmap.scaled(
                self.button_power.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.button_power.setPixmap(scaled_pixmap)


        # --- 病害管理エリア ------------------------------
        # 配置座標
        # 各サイズ

        # 病害名表示ラベル
        self.label_dam = QLabel("病害結果", self)
        self.label_dam.setFixedSize(390, 100)
        self.label_dam.move(BASE_X - 40, BASE_Y - 120)
        self.label_dam.setStyleSheet(PL_LABEL_STYLE)
        # パトライト色表示ラベル


        # --- システム管理エリア ------------------------------
        # 配置座標
        toggle_x = BASE_X + 25
        toggle_y = BASE_Y + 60
        toggle_status_x = toggle_x
        toggle_status_y = toggle_y + TOGGLE_H + 10
        # 各サイズ

        # システム状態表示ラベル
        self.label_panel = QLabel("システム管理", self)
        self.label_panel.setFixedSize(300, 55)
        self.label_panel.move(BASE_X, BASE_Y)
        self.label_panel.setStyleSheet(MAIN_LABEL_STYLE)
        # トグルスイッチ
        self.toggle = ToggleSwitch(self, width=TOGGLE_W, height=TOGGLE_H)
        self.toggle.move(toggle_x, toggle_y)
        # トグルスイッチ状態表示ラベル
        self.label_toggle_status = QLabel("停止中", self)
        self.label_toggle_status.setFixedSize(TOGGLE_W, 40)
        self.label_toggle_status.move(toggle_status_x, toggle_status_y)
        self.label_toggle_status.setStyleSheet(TOGGLE_LABEL_STYLE)