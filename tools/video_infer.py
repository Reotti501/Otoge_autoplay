# video_infer.py
# mkv動画ファイルに対してYOLOv8の推論を実行し、描画付きで表示

import cv2
from ultralytics import YOLO

# モデルの読み込み（自作学習済みモデル）
model = YOLO("models/deresute/result/best.pt")  # 正しいモデルパスに変更

# 推論対象の動画ファイル（.mkvなど）
video_path = "move/sample.mkv"  # 実際のパスに合わせて変更

# OpenCVで動画ファイルを読み込み
cap = cv2.VideoCapture(video_path)

# FPS確認用
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"[INFO] Input video FPS: {fps}")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("[INFO] Video end or cannot read frame.")
        break

    # 推論
    results = model(frame, verbose=False)[0]

    # 推論結果にバウンディングボックスを描画
    annotated_frame = results.plot()

    # 表示
    cv2.imshow("YOLOv8 - Video Inference", annotated_frame)

    # qキーで中断
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 後処理
cap.release()
cv2.destroyAllWindows()
