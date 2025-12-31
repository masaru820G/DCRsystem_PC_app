# サクランボ被害果除去システム_弐号機 PC側の制御フォルダ
## 環境
- Windows 11
- Python 3.12

## 使用するパッケージ
- "flask>=3.1.2"
- "hidapi>=0.14.0.post4"
- "pypylon>=4.2.0"
- "pyside6>=6.10.1"
- "requests>=2.32.5"

## インストール
初回実行時にクローンしたフォルダに移動し、以下コマンドをターミナルで実行
```bash
uv run python first.py
```
「実行環境」「使用するパッケージ」が自動でインストールされる

## プログラム説明
```text
main.py
├── import module_gui
├── import module_relay
├── import module_patlite
├── import module_cap_video
      └── import module_yolo
```

### main_Flask_GUI.py
- GUIのボタン制御で回転台、エアー制御を行う
- 4カ所からのカメラ取得画像が連続で表示される（予定）
- 検出したサクランボが被害果か健全果なのか、画面にテキスト表示しパトライトの点灯色も表示（予定）

### module_relay.py
- エアー制御するモジュール
  - 「健全果」であれば健全果エアーを開放
  - 「被害果」であれば被害果エアーを開放
  - 開放時間はn秒（予定）
    
### module_patlite.py
- パトライトを制御するモジュール
  - 検出したサクランボの状態に対し、点灯をコントロール
    - 「健全果」：青
    - 「カビ」：  紫
    - 「裂果」：  黄
    - 残りは検討
   
### module_cap_video.py（予定）
- サクランボを撮影するモジュール

### module_yolo.py（予定）
- 撮影した画像を、訓練済みモデルに渡し検出するモジュール
