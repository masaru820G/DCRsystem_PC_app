# -------------------------------------------------
# パトライトをYOLOの結果により制御するプログラムmodule
# -------------------------------------------------
import hid
import time

# ================================================
# 設定変数
# ================================================
VENDER_ID = 0x191a   # ベンダーID指定
PRODUCT_ID = 0x6001  # 製品ID指定
device = None        # モジュール内のグローバル変数

class LedPattern():
    """
    >>> LEDの制御値とデバッグ表示名を管理するクラス
    構成: (Byte5の16進数値, デバッグ用表示名)
    """
    OFF    = (0x00, "消灯")
    RED    = (0x11, "赤")
    GREEN  = (0x21, "緑")
    YELLOW = (0x31, "黄")
    BLUE   = (0x41, "青")
    VIOLET = (0x51, "紫")
    SKY    = (0x61, "空")
    WHITE  = (0x71, "白")
# ================================================
# 内部関数
# ================================================
def _send_command(data):
    """ >>> パトライトに制御コマンドを送信する内部関数"""
    global device
    if device is None:
        print("エラー: パトライトが初期化されていません。")
        return False

    try:
        device.write(data)
        return True
    except Exception as e:
        print(f"{e}: 書き込み失敗。")
        return False
# ================================================
# 外部関数
# ================================================
def init_patlite():
    """ >>> パトライト（hid device）を初期化し「OPEN」にする関数"""
    global device
    try:
        # 既に接続されている場合は何もしない
        if device:
            return True

        # デバイスに接続
        device = hid.device()
        device.open(VENDER_ID, PRODUCT_ID)
        print(">>> パトライト接続成功")

        # 初期状態として消灯・ブザー停止
        time.sleep(1.0)
        set_patlite_color(LedPattern.OFF)
        return True
    except Exception as e:
        print(f"接続エラー: {e}")
        device = None
        return False

def set_patlite_color(pattern = LedPattern.OFF):
    # 引数: True=点灯, False=消灯
    """ >>> パトライト制御関数
    引数 pattern には LedPattern クラスの定数 (値, 名前) を渡す
    ・LEDの制御 --> data[5]
    """
    # patternは (数値, 名前) のタプルなので分解する
    led_byte, color_name = pattern

    data = [0] * 9  #データの初期化9Bytes

    data[1] = 0x00      # コマンドバージョン
    data[2] = 0x00      # コマンドID
    data[3] = 0x07      # ブザー制御
    data[4] = 0x00      # ブザー音量
    data[5] = led_byte  # LED制御
    # 残りのバイト
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00

    #print(f"パトライト制御: {color_name}")

    return _send_command(data), color_name

def close_patlite():
    """
    >>> パトライトを「CLOSE」にする関数
    """
    global device
    if device:
        set_patlite_color(LedPattern.OFF) # 終了時に消灯
        device.close()
        device = None
        print(">>> パトライト切断完了")