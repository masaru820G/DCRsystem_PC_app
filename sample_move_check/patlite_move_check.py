import hid
import sys
import msvcrt  # Windowsでのキー入力検知用

# --- 設定 ---
VENDOR_ID = 0x191a   # パトライト社のベンダーID
PRODUCT_ID = 0x6001  # 製品ID

def get_patlite_device():
    """パトライトデバイスに接続してdeviceオブジェクトを返す"""
    try:
        device = hid.device()
        device.open(VENDOR_ID, PRODUCT_ID)
        print(f"接続成功: {device.get_manufacturer_string()} - {device.get_product_string()}")
        return device
    except Exception as e:
        print(f"デバイスを開けませんでした: {e}")
        print("USB接続を確認してください。")
        sys.exit()

def create_command(mode):
    """
    制御用のバイトデータを作成する
    mode: 'ON' (異常時/bad) または 'OFF' (消灯)
    """
    # 9バイトのデータを初期化 (Report ID 1byte + Data 8bytes)
    data = [0] * 9

    # 共通ヘッダー (元のコードに基づく)
    data[1] = 0x00 # コマンドバージョン
    data[2] = 0x00 # コマンドID
    data[3] = 0x07 # ブザー制御有効化フラグ?

    if mode == 'ON':
        # 元の patlite_bad 関数相当
        data[4] = 0x00 # ブザー音量
        data[5] = 0x11 # LED制御 (赤点灯など)
        # data[6]〜[8]は0x00のまま
        print(">> 送信: 点灯コマンド (Red/Bad)")
        
    elif mode == 'OFF':
        # 元の patlite_off 関数相当
        data[4] = 0x00 # ブザー音量 0:消音
        data[5] = 0x00 # LED制御 全消灯
        print(">> 送信: 消灯コマンド (Off)")

    return data

def main():
    # デバイス接続
    device = get_patlite_device()

    print("\n--- 操作方法 ---")
    print("[1]キー: パトライト点灯 (異常モード)")
    print("[0]キー: パトライト消灯")
    print("[q]キー: 終了")
    print("----------------\n")

    try:
        while True:
            # キーが押されたかチェック (ノンブロッキング)
            if msvcrt.kbhit():
                # 押されたキーを取得 (バイト列なのでデコード)
                key = msvcrt.getch().decode().lower()

                if key == '1':
                    # 点灯処理
                    cmd = create_command('ON')
                    device.write(cmd)
                
                elif key == '0':
                    # 消灯処理
                    cmd = create_command('OFF')
                    device.write(cmd)
                
                elif key == 'q':
                    # 終了処理
                    print("終了します...")
                    # 念のため消灯して終了
                    cmd = create_command('OFF')
                    device.write(cmd)
                    break

    except KeyboardInterrupt:
        print("\n強制終了されました")
    
    finally:
        device.close()
        print("デバイスを切断しました")

if __name__ == "__main__":
    main()