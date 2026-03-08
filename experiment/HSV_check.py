import os
import time
import sys
import cv2
import threading
import re
import numpy as np
from pypylon import pylon
from collections import deque

# ==========================================================
# 定数定義 (録画関連を削除)
# ==========================================================
TARGET_SERIALS = [
    ("25308967", "cam_top"),
    ("21905526", "cam_under"),
    ("25308969", "cam_inside"),
    ("25308968", "cam_outside")
]
FPS = 20.0

# ==========================================================
# PFSファイルを正確に読み込むための補助関数
# ==========================================================
def load_pfs_custom(camera, pfs_path):
    if not os.path.exists(pfs_path):
        return False
        
    nodemap = camera.GetNodeMap()
    pattern_with_selector = re.compile(r'^(\w+)\s+\{(\w+)=(\w+)\}\s+(.+)$')
    pattern_simple = re.compile(r'^(\w+)\s+(.+)$')

    with open(pfs_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('['):
                continue
            try:
                match_sel = pattern_with_selector.match(line)
                if match_sel:
                    feature, selector_name, selector_val, value = match_sel.groups()
                    sel_node = nodemap.GetNode(selector_name)
                    if sel_node:
                        sel_node.FromString(selector_val)
                    feat_node = nodemap.GetNode(feature)
                    if feat_node:
                        feat_node.FromString(value)
                    continue

                match_simple = pattern_simple.match(line)
                if match_simple:
                    feature, value = match_simple.groups()
                    feat_node = nodemap.GetNode(feature)
                    if feat_node and pylon.IsWritable(feat_node):
                        feat_node.FromString(value)

            except Exception:
                continue
    return True

# ==========================================================
# カメラ制御クラス (録画機能を削除)
# ==========================================================
class CameraController:
    def __init__(self, device_info, cam_name="unknown"):
        self.device_info = device_info
        self.name = cam_name
        self.settings_file = f"{self.name}.pfs"

        self.camera = None
        self.is_grabbing = False
        self.thread = None
        self.latest_frame = None
        self.lock = threading.Lock()
        
        self.delay_seconds = 0.0
        self.frame_queue = deque()

        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        
        self.width = 1280
        self.height = 960

    def init_camera(self):
        try:
            self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(self.device_info))
            self.camera.Open()
            
            if os.path.exists(self.settings_file):
                load_pfs_custom(self.camera, self.settings_file)
                print(f"[Success] {self.name}: 設定を精密に適用しました")
            
            self.width = self.camera.Width.Value
            self.height = self.camera.Height.Value
            print(f"[Info] {self.name} Resolution: {self.width}x{self.height}")

            return True
        except Exception as e:
            print(f"!!カメラ初期化エラー ({self.name}): {e}")
            return False

    def start_grabbing(self):
        if not self.camera or not self.camera.IsOpen():
            return
        
        self.is_grabbing = True
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()
        print(f"フレーム取得開始: {self.name}")

    def _capture_loop(self):
        while self.is_grabbing and self.camera.IsGrabbing():
            try:
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grab_result.GrabSucceeded():
                    converted = self.converter.Convert(grab_result)
                    frame_bgr = converted.GetArray()

                    with self.lock:
                        delay_frames = int(self.delay_seconds * FPS)
                        if delay_frames > 0:
                            self.frame_queue.append(frame_bgr.copy())
                            if len(self.frame_queue) > delay_frames:
                                self.latest_frame = self.frame_queue.popleft()
                            else:
                                self.latest_frame = frame_bgr.copy() 
                        else:
                            self.latest_frame = frame_bgr.copy()
                            self.frame_queue.clear()
                
                grab_result.Release()
            except Exception as e:
                print(f"!!Loop Error ({self.name}): {e}")
                break

    def stop_grabbing(self):
        self.is_grabbing = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.camera and self.camera.IsGrabbing():
            self.camera.StopGrabbing()

    def get_current_frame(self):
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return None

    def close(self):
        self.stop_grabbing()
        if self.camera and self.camera.IsOpen():
            self.camera.Close()

# ==========================================================
# カメラマネージャークラス
# ==========================================================
class CameraManager:
    def __init__(self):
        self.controllers = []

    def init_cameras(self):
        try:
            tl_factory = pylon.TlFactory.GetInstance()
            devices = tl_factory.EnumerateDevices()
        except Exception as e:
            print(f"!!Pylon初期化エラー: {e}")
            return False

        if not devices:
            return False

        for target_serial, cam_name in TARGET_SERIALS:
            found_device_info = next((d for d in devices if d.GetSerialNumber() == target_serial), None)
            if found_device_info:
                controller = CameraController(found_device_info, cam_name)
                if controller.init_camera():
                    self.controllers.append(controller)

        return len(self.controllers) > 0

    def start_all_get_frame(self):
        for controller in self.controllers:
            controller.start_grabbing()

    def stop_all_get_frame(self):
        for controller in self.controllers:
            controller.close()


# ==========================================================
# HSV範囲取得用アプリケーションクラス (矩形選択機能を追加)
# ==========================================================
class HSVViewerApp:
    def __init__(self, camera_manager):
        self.cam_mgr = camera_manager
        self.rect_data = {} 
        self.running = False

    def on_mouse_event(self, event, x, y, flags, param):
        """マウスイベントのコールバック: ドラッグによる矩形選択"""
        cam_name = param
        data = self.rect_data[cam_name]
        
        if event == cv2.EVENT_LBUTTONDOWN:
            data['drawing'] = True
            data['pt1'] = (x, y)
            data['pt2'] = (x, y)
            data['selected'] = False
        elif event == cv2.EVENT_MOUSEMOVE:
            if data['drawing']:
                data['pt2'] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            data['drawing'] = False
            data['pt2'] = (x, y)
            data['selected'] = True

    def run(self):
        """メインの表示ループ"""
        self.running = True
        
        for controller in self.cam_mgr.controllers:
            window_name = controller.name
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(window_name, self.on_mouse_event, param=window_name)
            # 初期状態の設定
            self.rect_data[window_name] = {'drawing': False, 'pt1': (0, 0), 'pt2': (0, 0), 'selected': False}

        print("HSVビュアーを開始しました。終了するには映像ウィンドウ上で 'q' キーを押してください。")
        print("映像をドラッグして領域を選択すると、その範囲のHSV最小・最大値が表示されます。")

        while self.running:
            for controller in self.cam_mgr.controllers:
                window_name = controller.name
                frame = controller.get_current_frame()
                
                if frame is not None:
                    display_frame = frame.copy()
                    data = self.rect_data[window_name]
                    
                    # ドラッグ中、または選択完了状態であれば矩形を描画・計算
                    if data['drawing'] or data['selected']:
                        x1, y1 = data['pt1']
                        x2, y2 = data['pt2']
                        
                        # 座標の正規化 (左上と右下の座標を確定)
                        left, right = min(x1, x2), max(x1, x2)
                        top, bottom = min(y1, y2), max(y1, y2)
                        
                        # 画像サイズ内にクランプ
                        h, w = frame.shape[:2]
                        left, right = max(0, left), min(w, right)
                        top, bottom = max(0, top), min(h, bottom)

                        # 領域が有効なサイズを持っている場合のみ処理
                        if right > left and bottom > top:
                            # 矩形の描画
                            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                            
                            # 領域の切り出しとHSV変換
                            roi = frame[top:bottom, left:right]
                            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                            
                            # 最小値・最大値の計算
                            h_min, s_min, v_min = np.min(hsv_roi, axis=(0, 1))
                            h_max, s_max, v_max = np.max(hsv_roi, axis=(0, 1))
                            
                            # テキストの準備
                            text_h = f"H: {h_min:3d} - {h_max:3d}"
                            text_s = f"S: {s_min:3d} - {s_max:3d}"
                            text_v = f"V: {v_min:3d} - {v_max:3d}"
                            
                            # 背景黒の矩形とテキストの描画
                            cv2.rectangle(display_frame, (10, 10), (220, 100), (0, 0, 0), -1)
                            cv2.putText(display_frame, text_h, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            cv2.putText(display_frame, text_s, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            cv2.putText(display_frame, text_v, (15, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                    cv2.imshow(window_name, display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.running = False

        cv2.destroyAllWindows()


# ==========================================================
# 実行ブロック
# ==========================================================
if __name__ == "__main__":
    manager = CameraManager()
    
    print("カメラを初期化しています...")
    if manager.init_cameras():
        print("フレームの取得を開始します...")
        manager.start_all_get_frame()
        
        time.sleep(1)
        
        viewer = HSVViewerApp(manager)
        viewer.run()
        
        print("終了処理を行っています...")
        manager.stop_all_get_frame()
    else:
        print("利用可能なカメラが見つかりませんでした。")