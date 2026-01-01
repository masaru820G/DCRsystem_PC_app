# -------------------------------------------------
# DCR_systemのGUIデザイン定義ファイル
# -------------------------------------------------
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QLabel, QPushButton, QCheckBox, QVBoxLayout, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QPixmap

# ==========================================================
# 定数定義
# ==========================================================
WINDOW_W, WINDOW_H = 1280, 800          # 1920×1200 拡大/縮小 150%
#WINDOW_W, WINDOW_H = 1280, 720          # 1920×1080 拡大/縮小 150%
SUB_WINDOW_W, SUB_WINDOW_H = 600, 500   # サブウインドウサイズ
MARGIN_X = 10                           # 画面の余白x
MARGIN_Y = 10                           # 画面の余白y

# --- メインウインドウゾーン ----------------------------
VIEW_CAM_SIZE_W = int(WINDOW_W * 0.34) // 10 * 10     # カメラ表示サイズw (10の倍数に丸める)
VIEW_CAM_SIZE_H = (WINDOW_H - MARGIN_Y * 3) / 2       # カメラ表示サイズh

ICON_SETTING_SIZE = 100                  # 設定アイコンサイズ
ICON_POWER_SIZE = 100                    # 電源アイコンサイズ

LABEL_DAM_SIZE_W = 360                   # 病害名表示ラベルサイズw
LABEL_DAM_SIZE_H = 80                   # 病害名表示ラベルサイズh

LABEL_MANAGEMENT_SIZE_W = 360            # システム管理ラベルサイズw
LABEL_MANAGEMENT_SIZE_H = 55             # システム管理ラベルサイズh

SWITCH_TOGGLE_SIZE_W = 260               # トグルスイッチサイズw
SWITCH_TOGGLE_SIZE_H = 130               # トグルスイッチサイズh
LABEL_TOGGLE_SIZE_W = 260                # トグルスイッチ状態表示ラベルサイズw
LABEL_TOGGLE_SIZE_H = 50                 # トグルスイッチ状態表示ラベルサイズh

BASE_X = (MARGIN_X + VIEW_CAM_SIZE_W) * 2    # システム管理エリア基準x
BASE_Y = MARGIN_Y * 2 + VIEW_CAM_SIZE_H    # システム管理エリア基準y

# --- サブウインドウゾーン ----------------------------
ICON_UP_SPEED_SIZE_W = 300               # speedアップアイコンサイズw
ICON_UP_SPEED_SIZE_H = 150               # speedアップアイコンサイズh
ICON_DOWN_SPEED_SIZE_W = 300             # speedダウンアイコンサイズw
ICON_DOWN_SPEED_SIZE_H = 150             # speedダウンアイコンサイズh

# ==========================================================
# スタイル定義
# ==========================================================
BUTTON_MAIN_STYLE = """
font-family: "Meiryo"; font-size: 30px; font-weight: bold;
color: #00FFFF; background-color: #333333; border-radius: 60px;
"""
LABEL_MANAGEMENT_STYLE = """
font-family: "Meiryo"; font-size: 40px; font-weight: bold;
color: #000000; background-color: #FFFFFF; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
BUTTON_SUB_STYLE = """
font-family: "Meiryo"; font-size: 20px; font-weight: bold;
color: #00FFFF; background-color: #333333; border-radius: 50px;
"""
LABEL_SUB_STYLE = """
font-family: "Meiryo"; font-size: 15px; font-weight: bold;
color: #000000; background-color: #FFFFFF; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
LABEL_DAM_STYLE = """
font-family: "Meiryo"; font-size: 30px; font-weight: bold;
color: #000000; background-color: #FFFFFF;
border: 1px solid #000000;
qproperty-alignment: 'AlignCenter';
"""
LABEL_STATUS_STYLE = """
font-size: 24px; font-weight: bold; color: #000000;
background-color: #adff2f; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
LABEL_CAM_STYLE = """
background-color: #333333; color: #FFFFFF;
font-size: 20px; font-weight: bold; border-radius: 5px;
qproperty-alignment: 'AlignCenter';
"""
LABEL_TOGGLE_STYLE = """
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

# ==========================================================
# リサイズ・スムージング処理関数
# ==========================================================
def resize_smooth_image(pixmap, button):
    if not pixmap.isNull():
            # 画像をラベルのサイズに合わせてリサイズ（スムージング処理付き）
            scaled_pixmap = pixmap.scaled(
                button.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            button.setPixmap(scaled_pixmap)

# ==========================================
# クリック可能なラベルクラス
# ==========================================
class ClickableLabel(QLabel):
    clicked = Signal()      # クリックされたときに反応するシグナル
    # --- 左クリック時のみ送信する関数 ------------------------------
    def mousePressEvent(self, event):
        if self.isEnabled and event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    # --- ボタンをロック・アンロックする関数 ------------------------------
    def set_locked(self, locked: bool):
        """
        locked = True   :   クリック無効＆半透明
        locked = False  :   クリック有効＆通常表示
        """
        self.setEnabled(not locked)
        opacity_effect = QGraphicsOpacityEffect(self)
        if locked:
            opacity_effect.setOpacity(0.3)
        else:
            opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(opacity_effect)


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
        self.setWindowTitle("設定画面")
        self.setFixedSize(SUB_WINDOW_W, SUB_WINDOW_H)
        self.setStyleSheet("background-color: #EEEEEE;")
        self.setWindowModality(Qt.ApplicationModal)


        # --- speed変更エリア ------------------------------
        # 配置座標
        up_speed_x = SUB_WINDOW_W - ICON_UP_SPEED_SIZE_W - 250
        up_speed_y = 20  # 上からの余白
        down_speed_x = SUB_WINDOW_W - ICON_DOWN_SPEED_SIZE_W - 250
        down_speed_y = SUB_WINDOW_H - ICON_DOWN_SPEED_SIZE_H - 20  # 下からの余白

        # up_speedボタン
        pixmap = QPixmap(resource_path("up_speed.png"))
        self.button_up_speed = ClickableLabel(self)
        self.button_up_speed.setFixedSize(ICON_UP_SPEED_SIZE_W, ICON_UP_SPEED_SIZE_H)
        self.button_up_speed.move(up_speed_x, up_speed_y)
        self.button_up_speed.setCursor(Qt.PointingHandCursor)        # マウスを乗せたときに指カーソルにする
        resize_smooth_image(pixmap, self.button_up_speed)

        # down_speedボタン
        pixmap = QPixmap(resource_path("down_speed.png"))
        self.button_down_speed = ClickableLabel(self)
        self.button_down_speed.setFixedSize(ICON_DOWN_SPEED_SIZE_W, ICON_DOWN_SPEED_SIZE_H)
        self.button_down_speed.move(down_speed_x, down_speed_y)
        self.button_up_speed.setCursor(Qt.PointingHandCursor)
        resize_smooth_image(pixmap, self.button_down_speed)


        # --- 戻るボタンエリア ------------------------------
        # 配置座標
        back_x = SUB_WINDOW_W - 150
        back_y = SUB_WINDOW_H - 150

        self.button_back = QPushButton("Back", self)
        self.button_back.setFixedSize(130, 130)
        self.button_back.setStyleSheet(BUTTON_SUB_STYLE)
        self.button_back.move(back_x, back_y)
        self.button_back.setCursor(Qt.PointingHandCursor)


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
        cam_x_right = MARGIN_X * 2 + VIEW_CAM_SIZE_W
        cam_y_upper = MARGIN_Y
        cam_y_lower = MARGIN_Y * 2 + VIEW_CAM_SIZE_H

        self.cam_in = QLabel("camera_inside", self)
        self.cam_in.setFixedSize(VIEW_CAM_SIZE_W, VIEW_CAM_SIZE_H); self.cam_in.setStyleSheet(LABEL_CAM_STYLE)
        self.cam_in.move(cam_x_left, cam_y_upper)

        self.cam_out = QLabel("camera_outside", self)
        self.cam_out.setFixedSize(VIEW_CAM_SIZE_W, VIEW_CAM_SIZE_H); self.cam_out.setStyleSheet(LABEL_CAM_STYLE)
        self.cam_out.move(cam_x_right, cam_y_upper)

        self.cam_under = QLabel("camera_underside", self)
        self.cam_under.setFixedSize(VIEW_CAM_SIZE_W, VIEW_CAM_SIZE_H); self.cam_under.setStyleSheet(LABEL_CAM_STYLE)
        self.cam_under.move(cam_x_left, cam_y_lower)

        self.cam_top = QLabel("camera_topside", self)
        self.cam_top.setFixedSize(VIEW_CAM_SIZE_W, VIEW_CAM_SIZE_H); self.cam_top.setStyleSheet(LABEL_CAM_STYLE)
        self.cam_top.move(cam_x_right, cam_y_lower)


        # --- 設定エリア ------------------------------
        # 配置座標
        setting_x = WINDOW_W - ICON_SETTING_SIZE - MARGIN_X * 2
        setting_y = MARGIN_Y * 4

        pixmap = QPixmap(resource_path("setting.png"))
        self.button_setting = ClickableLabel(self)
        self.button_setting.setFixedSize(ICON_SETTING_SIZE, ICON_SETTING_SIZE)
        self.button_setting.move(setting_x, setting_y)
        self.button_setting.setCursor(Qt.PointingHandCursor)    # マウスを乗せたときに指カーソルにする
        resize_smooth_image(pixmap, self.button_setting)


        # --- 電源エリア ------------------------------
        # 配置座標
        power_x = WINDOW_W - ICON_POWER_SIZE - MARGIN_X * 2
        power_y = MARGIN_Y * 8 + ICON_POWER_SIZE

        pixmap = QPixmap(resource_path("power_supply.png"))
        self.button_power = ClickableLabel(self)
        self.button_power.setFixedSize(ICON_POWER_SIZE, ICON_POWER_SIZE)
        self.button_power.move(power_x, power_y)
        self.button_power.setCursor(Qt.PointingHandCursor)
        resize_smooth_image(pixmap, self.button_power)


        # --- 病害管理エリア ------------------------------
        # 配置座標
        dam_x = WINDOW_W - LABEL_DAM_SIZE_W - MARGIN_X * 2
        dam_y = BASE_Y

        # 病害名表示ラベル
        self.label_dam = QLabel("病害結果", self)
        self.label_dam.setFixedSize(LABEL_DAM_SIZE_W, LABEL_DAM_SIZE_H)
        self.label_dam.setStyleSheet(LABEL_DAM_STYLE)
        self.label_dam.move(dam_x, dam_y)
        print("BASE_X:", BASE_X)
        print("dam_x:", dam_x)
        print("VIEW_CAM_SIZE_W:", VIEW_CAM_SIZE_W)
        print("VIEW_CAM_SIZE_H:", VIEW_CAM_SIZE_H)

        # --- システム管理エリア ------------------------------
        # 配置座標
        label_management_x = WINDOW_W - LABEL_MANAGEMENT_SIZE_W - MARGIN_X * 2
        label_management_y = dam_y + LABEL_DAM_SIZE_H + MARGIN_Y * 3
        toggle_switch_x = WINDOW_W - SWITCH_TOGGLE_SIZE_W - MARGIN_X * 7
        toggle_switch_y = label_management_y + LABEL_MANAGEMENT_SIZE_H + MARGIN_Y
        toggle_status_x = toggle_switch_x
        toggle_status_y = toggle_switch_y + SWITCH_TOGGLE_SIZE_H + MARGIN_Y

        # システム状態表示ラベル
        self.label_panel = QLabel("システム管理", self)
        self.label_panel.setFixedSize(LABEL_MANAGEMENT_SIZE_W, LABEL_MANAGEMENT_SIZE_H)
        self.label_panel.setStyleSheet(LABEL_MANAGEMENT_STYLE)
        self.label_panel.move(label_management_x, label_management_y)

        # トグルスイッチ
        self.toggle_switch = ToggleSwitch(self, SWITCH_TOGGLE_SIZE_W, SWITCH_TOGGLE_SIZE_H)
        self.toggle_switch.move(toggle_switch_x, toggle_switch_y)
        self.button_power.setCursor(Qt.PointingHandCursor)

        # トグルスイッチ状態表示ラベル
        self.label_toggle_status = QLabel("停止中", self)
        self.label_toggle_status.setFixedSize(LABEL_TOGGLE_SIZE_W, LABEL_TOGGLE_SIZE_H)
        self.label_toggle_status.setStyleSheet(LABEL_TOGGLE_STYLE)
        self.label_toggle_status.move(toggle_status_x, toggle_status_y)