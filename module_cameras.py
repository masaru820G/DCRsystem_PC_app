# -------------------------------------------------
# カメラから画像取得、フォルダに保存するプログラムmodule
# -------------------------------------------------
import os
import time
import sys
import cv2
import threading
from pypylon import pylon

import module_yolo_csv as yolo

# ==========================================================
# 定数定義
# ==========================================================
# カメラのシリアルナンバーリスト
TARGET_SERIALS = [
    ("25308967", "cam_top"),
    ("21905526", "cam_under"),
    ("25308969", "cam_inside"),
    ("25308968", "cam_outside")
]

# 動画保存設定
FOLDER_PARENT = "cam_video"     # 動画保存する親フォルダ名
FOLDER_CHILD = [
    "cam_video_top",        # 上カメラ動画保存先
    "cam_video_under",      # 下カメラ動画保存先
    "cam_video_inside",     # 内カメラ動画保存先
    "cam_video_outside"     # 外カメラ動画保存先
]

# 動画コーデック (Windows環境では 'DIVX' や 'mp4v' が安定する場合もあります)
VIDEO_CODEC = 'XVID'
VIDEO_EXIT = '.avi'

# カメラの諸設定
FRAME_WIDTH = 1280
FRAME_HEIGHT = 960
FRAME_SIZE = (FRAME_WIDTH, FRAME_HEIGHT)
FPS = 20.0

# ==========================================================
# 保存先の親フォルダと子フォルダを作成する関数
# ==========================================================
def setup_folders():
    try:
        if not os.path.exists(FOLDER_PARENT):
            os.makedirs(FOLDER_PARENT)
            print(f"親フォルダ '{FOLDER_PARENT}' を作成しました。")

        paths = []
        for folder in FOLDER_CHILD:
            path = os.path.join(FOLDER_PARENT, folder)
            if not os.path.exists(path):
                os.makedirs(path)
            paths.append(path)
            print(f"子フォルダ '{path}' を確認しました。")

        print("フォルダ準備完了。")
        return paths
    except OSError as e:
        print(f"フォルダ作成エラー: {e}")
        sys.exit(1)

# ==========================================================
# 個々のカメラの制御（接続、録画、停止）を行うクラス
# ==========================================================
class CameraController:
    def __init__(self, device_info, save_path, cam_name = "unknown"):
        self.device_info = device_info
        self.save_path = save_path
        self.name = cam_name

        self.camera = None
        self.video_writer = None
        self.is_recording = False
        self.thread = None
        self.video_filename = ""
        self.latest_frame = None     # 最新フレーム保存用
        self.lock = threading.Lock() # データの衝突防止用ロック

    # --- Pypylonによりカメラを初期化しオープンする関数 -------------------
    def init_camera(self):
        """Pypylonでカメラインスタンスを生成・オープン"""
        try:
            self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(self.device_info))
            self.camera.Open()
            # 設定ファイルのロードが必要な場合はここで行う
            #pylon.FeaturePersistence.Load("path/to/settings.pfs", self.camera.GetNodeMap(), True)
            return True
        except Exception as e:
            print(f"カメラ初期化エラー: {e}")
            return False

    # --- 動画録画開始する関数 -------------------
    def start_recording(self):
        if not self.camera or not self.camera.IsOpen():
            print(f"エラー: カメラが開かれていません ({self.device_info.GetSerialNumber()})")
            return

        # 保存ファイル・書き込み設定
        folder_name = os.path.basename(self.save_path)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        self.video_filename = os.path.join(self.save_path, f"{folder_name}_{timestamp}{VIDEO_EXIT}") # ファイル名を "フォルダ名_日時.avi" にする
        self.video_writer = cv2.VideoWriter(self.video_filename, fourcc, FPS, FRAME_SIZE)
        if not self.video_writer.isOpened():
            print(f"エラー: VideoWriterの作成に失敗しました ({self.video_filename})")
            return

        self.is_recording = True

        # カメラの画像取得開始 (GrabStrategy_LatestImageOnly: バッファ詰まり防止)
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # スレッドを作成してループ処理を実行
        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True # メインプログラム終了時に強制終了できるようにする
        self.thread.start()
        print(f"録画開始: {self.name}：{self.video_filename}\n")

    # --- フレームキャプチャと保存のループ処理関数 -------------------
    def _capture_loop(self):
        serial = self.device_info.GetSerialNumber()

        while self.is_recording and self.camera.IsGrabbing():
            try:
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)  # タイムアウト5000msで画像取得待機
                if grab_result.GrabSucceeded():
                    frame = grab_result.Array
                    with self.lock:  # 鍵をかけて書き込む
                        self.latest_frame = frame.copy()
                    # Bayer配列の場合は変換が必要（カメラ設定による）
                    # frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BAYER_BG2BGR)
                    # 今回は単純化のため、取得画像が既にカラーかモノクロ扱える前提で記述# 必要に応じて cv2.cvtColor を有効化してください
                    frame_bgr = None

                    # 画像の書き込み
                    # 注意: pypylonのraw画像とOpenCVの形式が合うか要確認
                    # 保存のためにBGR形式に変換します。
                    if len(frame.shape) == 2: # モノクロの場合
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    else:
                        frame_bgr = frame

                    # リサイズが必要な場合（設定したFRAME_SIZEと異なる場合）
                    if frame_bgr.shape[:2] != (FRAME_HEIGHT, FRAME_WIDTH):
                        frame_bgr = cv2.resize(frame_bgr, (FRAME_WIDTH, FRAME_HEIGHT))

                    # 書き込み
                    self.video_writer.write(frame_bgr)
                else:
                    print(f"フレーム取得エラー: {serial}, Error: {grab_result.ErrorCode}")

                grab_result.Release()

            except Exception as e:
                print(f"Loop Error ({serial}): {e}")
                break

    # --- 動画録画停止する関数 -------------------
    def stop_recording(self):
        self.is_recording = False

        # スレッドの終了を待つ
        if self.thread is not None:
            self.thread.join(timeout=2.0)

        if self.camera and self.camera.IsGrabbing():
            self.camera.StopGrabbing()

        if self.video_writer:
            self.video_writer.release()
            print(f"録画停止・保存完了: {self.video_filename}\n")

    # --- 現在のフレームを取得してGUIに表示する関数 -------------------
    def get_current_frame(self):
        with self.lock: # 鍵をかけて読み込む
            if self.latest_frame is not None:
                # カラー変換が必要ならここで行う
                img = self.latest_frame
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                return img
        return None

    # --- カメラリソースの解放をする関数 -------------------
    def close(self):
        self.stop_recording()
        if self.camera and self.camera.IsOpen():
            self.camera.Close()

# ==========================================================
# システム全体の管理（全カメラの接続・実行）を行うクラス
# ==========================================================
class CameraManager:
    def __init__(self):
        self.controllers = []
        setup_folders()

    # --- シリアルナンバーに基づき各カメラを初期化する関数 -------------------
    def init_cameras(self):
        try:
            tlFactory = pylon.TlFactory.GetInstance()
            devices = tlFactory.EnumerateDevices()
        except Exception as e:
            print(f"Pylon初期化エラー: {e}\n")
            return

        if not devices:
            print("エラー: カメラデバイスが見つかりません。\n")
            return

        print("カメラをシリアルナンバーで検索中・・・\n")
        for i, (target_serial, cam_name) in enumerate(TARGET_SERIALS):
            found_device_info = None

            for device_info in devices:
                if device_info.GetSerialNumber() == target_serial:
                    found_device_info = device_info
                    break

            if found_device_info:
                save_path = os.path.join(FOLDER_PARENT, FOLDER_CHILD[i])
                controller = CameraController(found_device_info, save_path, cam_name)
                self.controllers.append(controller)

                if controller.init_camera():
                    print(f"(接続 + 初期化完了)シリアルナンバー{controller.device_info.GetSerialNumber()} -> {controller.save_path}\n")
                    print(f"[接続完了]シリアルナンバー：{target_serial}, カメラ位置：{cam_name}\n")
                else:
                    print(f"エラー: シリアルナンバー {target_serial}, カメラ位置：{cam_name} のカメラの初期化に失敗しました。\n")

            else:
                print(f"[接続不可] Serial：{target_serial}, カメラ位置：{cam_name}\n")

        if len(self.controllers) != len(TARGET_SERIALS):
            print(f"警告: 予定台数 {len(TARGET_SERIALS)} に対し、接続成功は {len(self.controllers)} 台です。\n")
        else:
            print(f"全 {len(self.controllers)} 台のカメラ準備完了。\n")

    # --- 全てのカメラのフレーム取得を開始する関数 -------------------
    def start_all_get_frame(self):
        if not self.controllers:
            print("有効なカメラがありません。\n")
            return
        for controller in self.controllers:
            controller.start_recording()
        print("--- 全カメラ録画開始 ---\n")

    # --- 全てのカメラのフレーム取得を停止する関数 -------------------
    def stop_all_get_frame(self):
        for controller in self.controllers:
            controller.close()
        print("--- 全カメラ録画停止完了 ---\n")