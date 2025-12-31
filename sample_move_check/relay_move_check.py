# --- リレーボードをキーボード入力で制御するプログラム ---
import platform
import ctypes
import time
import msvcrt  # Windows用キー入力ライブラリ

class RelayController:
    # --- YDCI 定数 ---
    YDCI_RESULT_SUCCESS = 0     # エラーコード(戻り値)#正常終了
    YDCI_OPEN_NORMAL = 0        # YdciOpen

    def __init__(self):
        self.board_id = ctypes.c_ushort()  # ボードID
        self.ydci = None                   # DLLハンドル

    def open(self):
        """
        リレーボードをオープンする関数
        Returns:
            bool: 成功した場合は True、失敗した場合は False
        """
        self.board_id = ctypes.c_ushort()
        self.ydci = None

        # DLLのロード
        pf = platform.system()
        if pf == 'Windows':
            try:
                # カレントディレクトリまたはPATHに Ydci.dll があることを想定
                self.ydci = ctypes.windll.Ydci
            except FileNotFoundError:
                print("[Error]: Ydci.dll が見つかりません。")
                return False
            except Exception as e:
                print(f"[Error]: DLL Load failed. {e}")
                return False
        elif pf == 'Linux':
            self.ydci = ctypes.CDLL('libydci.so')
        else:
            print(f"This OS is not supported: {pf}")
            return False

        # ボード識別スイッチが0のボードをオープン
        # 注意: 第2引数のボード名称は環境に合わせて確認してください
        result_board = self.ydci.YdciOpen(self.board_id, b'RLY-P4/2/0B-UBT', ctypes.byref(self.board_id), self.YDCI_OPEN_NORMAL)
        
        if result_board != self.YDCI_RESULT_SUCCESS:
            print(f'[Error]: Cannot open board. ErrorCode: {result_board}')
            self.ydci = None
            return False
        
        print(f"Complete success! [Opened Board ID]: {self.board_id.value}")
        return True

    def set_state(self, channel, state):
        """
        リレーの状態を設定する関数
        Args:
            channel (int): チャネル番号 (0 または 1)
            state (int): 状態 (0: Open/ON, 1: Close/OFF)
        """
        if self.ydci is None:
            print("[Error]: Not initialized")
            return False

        output_data = ctypes.c_ubyte(state)
        # 第2引数はポインタ渡し、第4引数は制御するチャネル数(1)
        result = self.ydci.YdciRlyOutput(self.board_id, ctypes.byref(output_data), channel, 1)

        if result != self.YDCI_RESULT_SUCCESS:
            print(f'[Error]: Failed setting {channel}Ch_relay_status\n[ErrorCode]: {result}')
            return False

        return True

    def move(self, channel, duration_sec):
        """
        指定したChのリレーを(duration_sec)だけopenさせ、closeする関数
        Args:
            channel (int): Ch番号 (0 or 1)
            duration_sec (float): 作動させる時間（s）
        """
        # まずOpen(0)にする
        if self.set_state(channel, 0): 
            if channel == 0:
                print(f"Action: [Ch 0: Remove] OPEN ({duration_sec}s)")
            elif channel == 1:
                print(f"Action: [Ch 1: Carry ] OPEN ({duration_sec}s)")
            
            time.sleep(duration_sec)
            
            # Close(1)に戻す
            self.set_state(channel, 1) 
            print("Action: CLOSE")

        else:
            print(f"[Error]: Failed pulse_duration of {channel}Ch")

    def finish(self):
        """
        リレーボードをcloseする関数
        """
        if self.ydci is not None:
            print("Closing relay board...")
            # 終了処理: 安全のため全て閉じる
            self.set_state(0, 1) # 被害果除去用Ch（0）をClose
            self.set_state(1, 1) # 健全果運搬用Ch（1）をClose

            self.ydci.YdciClose(self.board_id)
            print("Board closed.")


# --- ここからメイン実行ブロック ---
if __name__ == "__main__":
    print("--- Relay Control Manual Mode ---")
    print("DLLをロードして初期化します...")

    controller = RelayController()
    
    # ボードオープンに成功したらループに入る
    if controller.open():
        print("\n=== 操作説明 ===")
        print(" [1] キー : Ch 0 (除去エアー) を噴射")
        print(" [2] キー : Ch 1 (運搬エアー) を噴射")
        print(" [Q] または [Esc] : 終了")
        print("================")

        try:
            while True:
                # キーが押されているかチェック（ノンブロッキング）
                if msvcrt.kbhit():
                    # キーを取得 (バイト列として返ってきます)
                    key = msvcrt.getch()
                    
                    # '1' キーを押したとき
                    if key == b'1':
                        controller.move(0, 0.5) # 0.5秒噴射
                    
                    # '2' キーを押したとき
                    elif key == b'2':
                        controller.move(1, 0.5) # 0.5秒噴射

                    # 'q' キー または Escキー(ASCII 27) で終了
                    elif key == b'q' or key == b'\x1b':
                        print("終了コマンドを受信しました。")
                        break
                
                # CPU負荷を下げるための短いスリープ
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n強制終了されました。")
        
        finally:
            # プログラム終了時に必ずボードを閉じる
            controller.finish()
    else:
        print("初期化に失敗したため終了します。")