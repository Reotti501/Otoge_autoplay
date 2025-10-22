# Googlecolabにて使用します
# --- でコードセルを区切って使用してください

!pip install --upgrade ultralytics
!pip install -q roboflow  # roboflow入れておくと便利な場面もある

---
from google.colab import drive
drive.mount('/content/drive')

---
import os

# データセットのパス（自分の配置場所に応じて変更）
project_path = "/content/drive/MyDrive/colab/models/deresute/3/"

# 存在確認
assert os.path.exists(project_path), "指定パスが存在しません"

# 作業ディレクトリ移動
%cd {project_path}

---
from ultralytics import YOLO

# モデル選択（n: nano, s: small）
model = YOLO("yolov8n.pt")

# 学習開始
model.train(
    data="deresute_data.yaml",   # データ定義ファイル
    epochs=50,
    imgsz=1280,
    batch=16,
    device=0,         # GPU使用
    name="yolo_colab_run"
)
