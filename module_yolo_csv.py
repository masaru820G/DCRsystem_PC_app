import os
import csv
import time
import cv2
import numpy as np
from datetime import datetime
from ultralytics import YOLO

# ==========================================================
# 定数定義
# ==========================================================
YOLO_IMG_SIZE = 640
CSV_DIR = "results"
VIDEO_DIR = "evaluated_videos"
MIN_AREA = 10000

# 中心判定用のマージン (画面中央240pxから左右どの程度の範囲にいたら「中心」とみなすか)
CENTER_THRESHOLD_X = 100

# 動画保存用の設定
VIDEO_CODEC = cv2.VideoWriter_fourcc(*'mp4v')
VIDEO_FPS = 40.0

# 赤色抽出用のHSV閾値
H1_LOW, H1_HIGH = np.array([0, 100, 60]), np.array([25, 255, 255])
H2_LOW, H2_HIGH = np.array([165, 100, 60]), np.array([180, 255, 255])

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
        self.target_found = target_found

# ==========================================================
# YOLO検出・画像処理クラス
# ==========================================================
class YoloDetector:
    def __init__(self, model_path="C:/gamo/yolo_v1/runs/detect/train7/weights/best.pt"):
        print(f"YOLOモデル {model_path} をロード中...")
        self.model = YOLO(model_path).to('CUDA')
        
        # CSV設定
        if not os.path.exists(CSV_DIR): os.makedirs(CSV_DIR)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_path = os.path.join(CSV_DIR, f"result_{timestamp}.csv")
        self._init_csv()

        # 動画設定
        if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)
        self.video_path = os.path.join(VIDEO_DIR, f"eval_{timestamp}.mp4")
        self.video_writer = cv2.VideoWriter(self.video_path, VIDEO_CODEC, VIDEO_FPS, (YOLO_IMG_SIZE, YOLO_IMG_SIZE))
        
        if self.video_writer.isOpened():
            print(f"評価動画保存開始: {self.video_path}")

    def _init_csv(self):
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Camera", "ID", "LabelID", "LabelName", "Confidence", "TargetFound"])

    def get_target_info(self, frame):
        """HSVで赤いサクランボの位置とサイズを特定する"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, H1_LOW, H1_HIGH) + cv2.inRange(hsv, H2_LOW, H2_HIGH)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        
        best_target = None
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]
            mx, my = int(centroids[i][0]), int(centroids[i][1])
            if area > MIN_AREA:
                # 最も面積が大きいものを現在のターゲットとする
                if best_target is None or area > best_target['area']:
                    best_target = {'x': x, 'y': y, 'w': w, 'h': h, 'mx': mx, 'my': my, 'area': area}
        return best_target

    def dynamic_crop(self, frame, target):
        """サクランボの中心座標を基準に周辺を切り出す"""
        img_h, img_w = frame.shape[:2]
        
        # 切り出しサイズ: 果実の最大辺の1.8倍、最低でも300pxを確保
        crop_size = int(max(target['w'], target['h']) * 1.8)
        crop_size = max(crop_size, 300)
        
        # 切り出し範囲の計算（画面外に出ないようにクランプ）
        x1 = max(0, target['mx'] - crop_size // 2)
        y1 = max(0, target['my'] - crop_size // 2)
        x2 = min(img_w, x1 + crop_size)
        y2 = min(img_h, y1 + crop_size)
        
        # 端に寄った際にサイズが小さくならないよう再調整
        x1 = max(0, x2 - crop_size)
        y1 = max(0, y2 - crop_size)
        
        return frame[y1:y2, x1:x2]

    def evaluate_frame(self, frame, cam_name, obj_id):
        """画像処理から推論、動画保存までを実行"""
        target = self.get_target_info(frame)
        found = target is not None
        
        # 修正: ターゲットが見つからない時は、YOLOをスキップして元の画像を返す
        if not found:
            # 動画には書き込むが、YOLOの枠はない生の画像をリサイズして保存
            input_img_resized = cv2.resize(frame, (YOLO_IMG_SIZE, YOLO_IMG_SIZE))
            if self.video_writer and self.video_writer.isOpened():
                self.video_writer.write(input_img_resized)
            return input_img_resized, None
        
        # 画面中央付近にいるか判定
        img_w = frame.shape[1]
        is_centered = found and (abs(target['mx'] - img_w//2) < CENTER_THRESHOLD_X)

        if is_centered:
            # 中心にいる時だけ果実周辺を切り抜く
            input_img = self.dynamic_crop(frame, target)
        else:
            # 中心にいない、または未検出時は全体を使用
            input_img = frame

        # YOLO推論 (常に640x640にリサイズ)
        input_img_resized = cv2.resize(input_img, (YOLO_IMG_SIZE, YOLO_IMG_SIZE), interpolation=cv2.INTER_AREA)
        results = self.model.track(input_img_resized, persist=True, verbose=False)
        annotated_frame = results[0].plot()
        
        # 動画書き込み
        if self.video_writer and self.video_writer.isOpened():
            self.video_writer.write(annotated_frame)
        
        # 結果パースとCSV保存
        best_result = None
        if len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            label_id, label_name, conf = int(box.cls), self.model.names[int(box.cls)], float(box.conf)
            best_result = YoloResult(cam_name, obj_id, label_id, label_name, conf, found)
            self.save_result_csv(best_result)
        else:
            best_result = YoloResult(cam_name, obj_id, -1, "None", 0.0, found)
            
        return annotated_frame, best_result

    def save_result_csv(self, res):
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([res.timestamp, res.cam_name, res.obj_id, res.label_id, res.label_name, f"{res.confidence:.2f}", res.target_found])

    def close(self):
        if self.video_writer:
            self.video_writer.release()
            print(f"評価動画保存完了: {self.video_path}")
            self.video_writer = None