# ================================================
# パトライトをYOLOの結果により制御するプログラムmodule
# ================================================
import hid
import time
# -------------------------------------------------
"""設定変数"""
VENDER_ID = 0x191a   # ベンダーID指定
PRODUCT_ID = 0x6001  # 製品ID指定
device = None        # モジュール内のグローバル変数
# -------------------------------------------------

# ------------------------------------------------------------------------------------------------------------
"""内部関数"""
"""
・ _send_command(data)
>>> パトライトに制御コマンドを送信する内部関数
・ _set_patlite_color(red=False, yellow=False, green=False, blue=False, white=False, buzzer=False)
>>> パトライト各制御をするための内部関数
"""
def _send_command(data):
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

def _set_patlite_color(red=False, yellow=False, green=False, blue=False, white=False, buzzer=False):
    # 引数: True=点灯, False=消灯
    # データの初期化 (9バイト: ReportID + 8バイトデータ)
    data = [0] * 9
    
    data[1] = 0x00 # コマンドバージョン
    data[2] = 0x00 # コマンドID
    
    # --- ブザー制御 (Byte 3) ---
    # 0x07: ブザー停止, 0x09: ブザー吹鳴 (モデルにより値が異なる場合があります)
    # ここでは既存コードの 0x07(停止?) をベースにしつつ、吹鳴時はビットを立てる例とします
    # ※お使いの機種の仕様に合わせて調整が必要な場合があります
    if buzzer:
        data[3] = 0x09 # 例: 吹鳴 (機種により 0x01 等の場合あり)
    else:
        data[3] = 0x07 # 停止
        
    data[4] = 0x00 # ブザー音量

    # --- LED制御 (Byte 5) ---
    # パトライトのUSB制御は一般的にビット演算で色を指定します
    # bit0: 赤, bit1: 黄, bit2: 緑, bit3: 青, bit4: 白
    led_byte = 0x00
    
    if red:    led_byte |= 0x01  # 赤 (0000 0001)
    if yellow: led_byte |= 0x02  # 黄 (0000 0010)
    if green:  led_byte |= 0x04  # 緑 (0000 0100)
    if blue:   led_byte |= 0x08  # 青 (0000 1000)
    if white:  led_byte |= 0x10  # 白 (0001 0000)

    data[5] = led_byte # 計算したLED値をセット
    
    # 残りのバイト
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00

    # デバッグ表示（現在どの色がONか）
    status = []
    if red: status.append("赤")
    if yellow: status.append("黄")
    if green: status.append("緑")
    if blue: status.append("青")
    if white: status.append("白")
    if not status: status.append("消灯")
    
    print(f"パトライト制御: {','.join(status)} (Byte5: {hex(led_byte)})")
    
    return _send_command(data)
# ------------------------------------------------------------------------------------------------------------

# -----------------------------------------------------------
"""外部関数"""
"""
・ init_patlite()
>>> パトライト（hid device）を初期化し「OPEN」にする関数
・ patlite_off()
>>> 全消灯
・ patlite_red()
>>> 赤点灯 --> 
・ patlite_yellow()
>>> 黄点灯 -->
・ patlite_green()
>>> 緑点灯 -->
・ patlite_blue()
>>> 青点灯 -->
・ patlite_white()
>>> 白点灯 -->
・ close_patlite()
>>> パトライトを「CLOSE」にする関数
"""

def init_patlite():
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
        patlite_off()
        return True
    except Exception as e:
        print(f"{e}: パトライトの接続に失敗しました。")
        device = None
        return False

def patlite_off():
    """全消灯"""
    return _set_patlite_color() # 全てFalseなので消灯

def patlite_red():
    """赤点灯 (異常)"""
    return _set_patlite_color(red=True)

def patlite_yellow():
    """黄点灯 (警告)"""
    return _set_patlite_color(yellow=True)

def patlite_green():
    """緑点灯 (正常)"""
    return _set_patlite_color(green=True)

def patlite_blue():
    """青点灯 ()"""
    return _set_patlite_color(blue=True)

def patlite_white():
    """白点灯 (正常)"""
    return _set_patlite_color(green=True)

def close_patlite():
    global device
    if device is not None:
        print(">>> パトライトをCLOSEします。")
        patlite_off() # 終了時に消灯
        device.close()
        device = None
# -----------------------------------------------------------

# ==========================================
# 動作確認用メイン
# ==========================================
if __name__ == "__main__":
    if init_patlite():
        try:
            # 緑 (正常)
            patlite_green()
            time.sleep(2)

            # 黄 (警告)
            patlite_yellow()
            time.sleep(2)

            # 赤 (異常)
            patlite_red()
            time.sleep(2)

            # 赤と黄色を同時点灯（複数指定も可能）
            print("--- 複数点灯テスト ---")
            _set_patlite_color(red=True, yellow=True)
            time.sleep(2)

        finally:
            close_patlite()