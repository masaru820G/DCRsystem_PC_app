# ----------------------------------------------------------------------------------------
# カメラから取得した画像をYOLOに渡し評価し、ID, 評価結果, 信頼度を.csvに格納するプログラムmodule
# ----------------------------------------------------------------------------------------
import os
import csv
import time
import cv2
import numpy as np
from datetime import datetime
from ultralytics import YOLO

# ==========================================================
# 定数定義 (yolo_tra_camera_v7_1023 準拠)
# ==========================================================
YOLO_IMG_SIZE = 640
CSV_DIR = "results"
MIN_AREA = 10000  # 検出とみなす最小面積

# 赤色抽出用のHSV閾値
H1_LOW, H1_HIGH = np.array([0, 70, 60]), np.array([25, 255, 255])
H2_LOW, H2_HIGH = np.array([165, 70, 60]), np.array([180, 255, 255])

# ==========================================================
# 判定結果データクラス
# ==========================================================
class YoloResult:
    def __init__(self, cam_name, obj_id, label_id, label_name, confidence, target_found):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.cam_name = cam_name
        self.obj_id = obj_id
        self.label_id = label_id
        self.label_name = label_name
        self.confidence = confidence
        self.target_found = target_found  # 赤色ターゲットの有無

# ==========================================================
# YOLO検出・画像処理クラス
# ==========================================================
class YoloDetector:
    def __init__(self, model_path="C:/gamo/yolo_v1/runs/detect/train7/weights/best.pt"):
        print(f"YOLOモデル {model_path} をロード中...")
        self.model = YOLO(model_path)
        if not os.path.exists(CSV_DIR):
            os.makedirs(CSV_DIR)
        self.csv_path = os.path.join(CSV_DIR, f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        self._init_csv()

    def _init_csv(self):
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Camera", "ID", "LabelID", "LabelName", "Confidence", "TargetFound"])

    def detect_target_hsv(self, frame):
        """HSVによる赤色領域の抽出ロジック"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, H1_LOW, H1_HIGH)
        mask2 = cv2.inRange(hsv, H2_LOW, H2_HIGH)
        mask = mask1 + mask2
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        
        coordinates = []
        target_found = False
        
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]
            mx, my = int(centroids[i][0]), int(centroids[i][1])
            
            # yolo_tra_camera_v7_1023 の条件を適用
            if 100 < mx < 1200 and area > MIN_AREA:
                target_found = True
                coordinates.append((y, y+h, x, x+w, mx, my, area))
        
        return target_found, coordinates

    def preprocess_image(self, frame):
        """【修正】拡大（切り抜き）をせず、全画面をリサイズのみ行う"""
        return cv2.resize(frame, (YOLO_IMG_SIZE, YOLO_IMG_SIZE), interpolation=cv2.INTER_AREA)
        """
        検出状況に合わせたクロップとリサイズ
        h, w = frame.shape[:2]
        if target_found and coordinates:
            # 最初のターゲットを中心に正方形で切り出すロジック
            top, bottom, left, right, mx, my, s = coordinates[0]
            ch, cw = bottom - top, right - left
            side = max(ch, cw)
            
            # 中心を維持しつつ正方形の範囲を計算
            y1, y2 = max(0, my - side//2), min(h, my + side//2)
            x1, x2 = max(0, mx - side//2), min(w, mx + side//2)
            cropped = frame[y1:y2, x1:x2]
        else:
            # ターゲットがない場合は中央をクロップ
            size = min(h, w) // 2
            cx, cy = w // 2, h // 2
            cropped = frame[cy-size:cy+size, cx-size:cx+size]
            
        if cropped.size == 0:
            return cv2.resize(frame, (YOLO_IMG_SIZE, YOLO_IMG_SIZE))
            
        return cv2.resize(cropped, (YOLO_IMG_SIZE, YOLO_IMG_SIZE), interpolation=cv2.INTER_AREA)
        """

    def evaluate_frame(self, frame, cam_name, obj_id):
        """画像処理から推論、結果保持までを一括実行"""
        # 1. ターゲット検知
        found = self.detect_target_hsv(frame)
        
        # 2. 前処理（クロップ・リサイズ）
        input_img = self.preprocess_image(frame)
        
        # 3. YOLO推論
        results = self.model.track(input_img, persist=True, verbose=False)
        annotated_frame = results[0].plot()
        
        # 4. 結果のパース
        best_result = None
        if len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            label_id = int(box.cls)
            label_name = self.model.names[label_id]
            conf = float(box.conf)
            best_result = YoloResult(cam_name, obj_id, label_id, label_name, conf, found)
            self.save_result_csv(best_result)
        else:
            # 検出なしの場合
            best_result = YoloResult(cam_name, obj_id, -1, "None", 0.0, found)
            
        return annotated_frame, best_result

    def save_result_csv(self, res: YoloResult):
        """CSVへの書き込み"""
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([res.timestamp, res.cam_name, res.obj_id, res.label_id, res.label_name, f"{res.confidence:.2f}", res.target_found])