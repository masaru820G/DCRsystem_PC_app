# --- パトライトをYoloの結果により制御するプログラムmodule ---
import hid

# ベンダーIDとプロダクトIDの指定
VENDER_ID = 0x191a   # ベンダーID
PRODUCT_ID = 0x6001  # 製品ID

# モジュール内のグローバル変数
device = None


# --- パトライト（hid device）を初期化。「OPEN」にする関数 ---
def init_patlite():
    global device
    try:
        # デバイスに接続
        device = hid.device()
        device.open(VENDER_ID, PRODUCT_ID)

        print("パトライト接続成功")
        # デバイスに関する情報を表示
        print(f'Device manufacturer: {device.get_manufacturer_string()}')
        print(f'Product: {device.get_product_string()}')

        # 初期状態として消灯しておく
        patlite_off()
        return True
    except Exception as e:
        print(f"エラー: パトライトの接続に失敗しました。{e}")
        print("デバイスが接続されているか、HIDAPIライブラリが正しくインストールされているか確認してください。")
        device = None
        return False


# --- パトライトに制御コマンドを送信する内部関数 ---
def _send_command(data):
    global device
    if device is None:
        print("エラー: パトライトが初期化されていません。")
        return False

    try:
        device.write(data)
        return True
    except Exception as e:
        print(f"エラー: パトライトへの書き込みに失敗しました。{e}")
        return False


# --- パトライトを「異常状態（赤色）」にする関数 ---
def patlite_bad():
    data = [0]*9   #パトライト制御コマンド用データ配列(9byte)
    data[1] = 0x00 #コマンドバージョン
    data[2] = 0x00 #コマンドID
    data[3] = 0x07 #ブザー制御
    data[4] = 0x00 #ブザー音量
    data[5] = 0x11 #LED制御 赤点灯
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00

    print("パトライト: 異常 (赤色点灯)")
    return _send_command(data)


# --- パトライトを「OFF」にする関数 ---
def patlite_off():
    data = [0]*9   #パトライト制御コマンド用データ配列(9byte)
    data[1] = 0x00 #コマンドバージョン
    data[2] = 0x00 #コマンドID
    data[3] = 0x07 #ブザー制御
    data[4] = 0x00 #ブザー音量
    data[5] = 0x00 #LED制御 消灯
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00

    print("パトライト: オフ(消灯)")
    return _send_command(data)


# --- パトライトを「CLOSE」にする関数 ---
def close_patlite():
    global device
    if device is not None:
        print("パトライトをCLOSEします。")
        patlite_off() # 終了時に消灯
        device.close()
        device = None