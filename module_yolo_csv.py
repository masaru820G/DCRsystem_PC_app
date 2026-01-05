# ----------------------------------------------------------------------------------------
# カメラから取得した画像をYOLOに渡し評価し、ID, 評価結果, 信頼度を.csvに格納するプログラムmodule
# ----------------------------------------------------------------------------------------
import os
import csv
import time
import threading
import cv2
from ultralytics import yolo

# 制御モジュール
import module_cameras as cam_ctr
import module_patlite as p_ctr
import module_relay as r_ctr

# ==========================================================
# 定数定義
# ==========================================================

# ==========================================================
# トリガーチェック関数
# ==========================================================

# ==========================================================
# 汎用バックグラウンドタスク用クラス
# ==========================================================
class YoloResult:
    def __init__(self, obj_id, label, confidence):
        """コンストラクタ: 変数の初期化"""
        self.obj_id = obj_id            # 検出物体ID
        self.label = label              # 検出ラベル
        self.confidence = confidence    # 信頼度

class YoloDetector:
    def __init__(self, model_path='best.pt'):
        print("YOLOモデルをロード中...")
        self.model = YOLO(model_path)
        print("YOLOロード完了")

    def detect(self, image):
        """画像を受け取り、検出結果画像を返す"""
        results = self.model(image, verbose=False)
        # 検出結果が描画された画像を返す（GUI表示用）
        annotated_frame = results[0].plot()
        
        # 必要であれば、ここで「傷あり」「良品」などのテキスト判定結果も返せます
        return annotated_frame
