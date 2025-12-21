# ==================================================
# リレーボードをYOLOの結果により制御するプログラムmodule
# ==================================================
import platform
import ctypes
# import sys
import time

# --- YDCI 定数 ---
YDCI_RESULT_SUCCESS = 0     # エラーコード(戻り値)#正常終了
YDCI_OPEN_NORMAL = 0        # YdciOpen

# --- モジュールのグローバル変数 ---
board_id = ctypes.c_ushort()
ydci = None


def init_relay():
    """
    リレーボード(Ydci)を初期化し、オープンします。
    Returns:
        bool: 初期化が成功した場合は True、失敗した場合は False
    """
    global board_id, ydci

    # DLLのロード
    pf = platform.system()
    if pf == 'Windows':
        try:
            ydci = ctypes.windll.Ydci
        except OSError:
            print("エラー: Ydci.dll が見つかりません。")
            return False
    else:
        print(f"サポートされていないOSです: {pf}")
        return False

    # ボード識別スイッチが0のボードをオープン
    result_board = ydci.YdciOpen(board_id, b'RLY-P4/2/0B-UBT', ctypes.byref(board_id), YDCI_OPEN_NORMAL)
    if result_board != YDCI_RESULT_SUCCESS:
        print(f'オープンできません。エラーコード: {result_board}')
        ydci = None
        return False
    print(f"リレーボードが正常にオープンしました。Board ID: {board_id.value}")

    # 初期状態設定:
    set_relay_state(0, 1)       # 被害果除去用Ch（0）をClose
    set_relay_state(1, 1)       # 健全果運搬用Ch（1）をClose

    print("リレー初期状態: 除去エアー CLOSE, 運搬エアー CLOSE")
    return True

# --- リレーの状態を設定する関数 ---
"""
Args:
    channel (int): チャネル番号 (0 または 1)
    state (int): 状態 (0: Open, 1: Close)
Returns:
    bool: 成功した場合は True、失敗した場合は False

[ydci.YdciRlyOutput()]
board_id -> リレー制御ボードを識別するための変数。ctypes.c_ushort 型で定義し、YdciRlyOpen が正常に実行されると、この変数にボードIDが格納されます。
ctypes.byref(output_data) -> relay_ON(0),relay_OFF(1)
start_channel -> 操作を開始するチャネルの番号
num_channel -> 操作するチャネルの総数
"""

def set_relay_state(channel, state):
    global ydci, board_id
    if ydci is None:
        print("エラー: リレーボードが初期化されていません。")
        return False

    output_data = ctypes.c_ubyte(state)
    result = ydci.YdciRlyOutput(board_id, ctypes.byref(output_data), channel, 1)

    if result != YDCI_RESULT_SUCCESS:
        print(f'リレー Ch{channel} の状態設定に失敗しました。エラーコード: {result}')
        return False

    return True

# --- 指定したChのリレーを(duration_sec)だけopenさせ、closeする関数 ---
"""
Args:
    channel (int): Ch番号 (0 or 1)
    duration_sec (float): 作動させる時間（s）
"""
def pulse_relay(channel, duration_sec):
    if set_relay_state(channel, 0): # Open
        time.sleep(duration_sec)
        set_relay_state(channel, 1) # Close
    else:
        print(f"エラー: リレー Ch{channel} のパルス動作に失敗しました。")

# --- リレーボードをcloseする関数 ---
def close_relay():
    global ydci, board_id
    if ydci is not None:
        print("リレーボードをCLOSEします。")
        set_relay_state(0, 1) # 除去用 Close
        set_relay_state(1, 1) # 運搬用 Close

        ydci.YdciClose(board_id)
        ydci = None
        board_id = ctypes.c_ushort() # IDリセット