import cv2
import numpy as np
import mss
from ultralytics import YOLO
from pynput.keyboard import Controller
import pygetwindow as gw
import time

# ---------------- 設定 ----------------
DRAW_MODE = True  # ← 描画を無効にしたい場合は False に設定
CONF_THRESHOLD = 0.8
LANE_X_POSITIONS_REL = [0.16, 0.325, 0.485, 0.65, 0.81]
JUDGE_LINE_Y_REL = 0.79
FLICK_TO_LONG_RELEASE_DELAY = 0.1  # flick押下からlong離すまでの遅延秒数
# -------------------------------------

# モデルとキーボード初期化
model = YOLO("models/deresute/fin/dere1.pt")
keyboard = Controller()

# 実座標は後でウィンドウサイズから更新
LANE_X_POSITIONS = [0] * 5
JUDGE_LINE_Y = 0

KEYMAP = {
    0: {"tap": "q", "long": "q", "left_flick": "1", "right_flick": "a"},
    1: {"tap": "w", "long": "w", "left_flick": "2", "right_flick": "s"},
    2: {"tap": "e", "long": "e", "left_flick": "3", "right_flick": "d"},
    3: {"tap": "r", "long": "r", "left_flick": "4", "right_flick": "f"},
    4: {"tap": "t", "long": "t", "left_flick": "5", "right_flick": "g"},
}

active_notes = {}
triggered_notes = set()
long_hold_active = {}
delayed_release = {}  # レーン → longを離す予定時間
sct = mss.mss()

# FPS計測用
frame_times = []
start_time = time.time()

def get_bluestacks_bbox():
    for w in gw.getWindowsWithTitle("Bluestacks App Player"):
        if w.visible and w.width > 100 and w.height > 100:
            return {"top": w.top, "left": w.left, "width": w.width, "height": w.height}
    raise RuntimeError("Bluestacks App Player ウィンドウが見つかりません")

def update_lane_positions(bbox):
    global LANE_X_POSITIONS, JUDGE_LINE_Y
    width = bbox["width"]
    height = bbox["height"]
    LANE_X_POSITIONS = [int(width * rel) for rel in LANE_X_POSITIONS_REL]
    JUDGE_LINE_Y = int(height * JUDGE_LINE_Y_REL)

def get_lane(x):
    return min(range(len(LANE_X_POSITIONS)), key=lambda i: abs(x - LANE_X_POSITIONS[i]))

try:
    while True:
        frame_start = time.time()

        bbox = get_bluestacks_bbox()
        update_lane_positions(bbox)

        img = np.array(sct.grab(bbox))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        results = model.track(img_rgb, persist=True, verbose=False, tracker="bytetrack.yaml")[0]
        boxes = results.boxes
        current_notes = []
        current_note_ids = set()

        if boxes is not None and boxes.id is not None:
            for box, cls_id, track_id, conf in zip(
                boxes.xywh.cpu().numpy(),
                boxes.cls.cpu().numpy(),
                boxes.id.cpu().numpy(),
                boxes.conf.cpu().numpy()
            ):
                if conf < CONF_THRESHOLD:
                    continue
                x, y, w, h = box
                if y > JUDGE_LINE_Y + 10:
                    continue

                cls = int(cls_id)
                note_id = int(track_id)
                lane = get_lane(x)

                current_notes.append((cls, x, y, w, h, note_id, lane, conf))
                current_note_ids.add(note_id)
                active_notes[note_id] = {"bbox": (x, y, w, h), "cls": cls, "lane": lane}

        now = time.time()

        # 遅延リリース判定
        for lane, release_time in list(delayed_release.items()):
            if now >= release_time and lane in long_hold_active:
                keyboard.release(long_hold_active[lane]["key"])
                del long_hold_active[lane]
                del delayed_release[lane]

        for cls, x, y, w, h, note_id, lane, conf in current_notes:
            label = model.names[cls]
            if note_id in triggered_notes:
                continue

            if label == "tap" and JUDGE_LINE_Y - 10 <= y <= JUDGE_LINE_Y + 10:
                key = KEYMAP[lane]["tap"]
                keyboard.press(key)
                keyboard.release(key)
                triggered_notes.add(note_id)

            elif label == "long":
                if lane not in long_hold_active and JUDGE_LINE_Y - 10 <= y <= JUDGE_LINE_Y + 10:
                    key = KEYMAP[lane]["long"]
                    keyboard.press(key)
                    long_hold_active[lane] = {"note_id": note_id, "key": key, "y": y}
                    triggered_notes.add(note_id)

                elif lane in long_hold_active and JUDGE_LINE_Y - 10 <= y <= JUDGE_LINE_Y + 10:
                    # 通常離すタイミング（flick未関与時）
                    if lane not in delayed_release:
                        keyboard.release(long_hold_active[lane]["key"])
                        del long_hold_active[lane]
                        triggered_notes.add(note_id)

            elif label in ["left_flick", "right_flick"] and JUDGE_LINE_Y - 10 <= y <= JUDGE_LINE_Y + 10:
                flick_key = KEYMAP[lane][label]
                keyboard.press(flick_key)
                keyboard.release(flick_key)
                triggered_notes.add(note_id)

                # longが押されていた場合、0.1秒後に離す予約
                if lane in long_hold_active:
                    delayed_release[lane] = now + FLICK_TO_LONG_RELEASE_DELAY

        for lane in list(long_hold_active.keys()):
            long_data = long_hold_active[lane]
            if long_data["y"] > JUDGE_LINE_Y + 10:
                if lane not in delayed_release:
                    keyboard.release(long_data["key"])
                    del long_hold_active[lane]

        # FPS計測
        frame_end = time.time()
        frame_times.append(frame_end - frame_start)
        if len(frame_times) > 100:
            frame_times.pop(0)
        fps = 1.0 / (frame_times[-1] if frame_times[-1] != 0 else 1)

        # 描画モードなら描画
        if DRAW_MODE:
            for cls, x, y, w, h, note_id, lane, conf in current_notes:
                label = model.names[cls]
                color = (0, 255, 0) if label == "tap" else (0, 0, 255) if label == "long" else (255, 0, 255)
                cv2.rectangle(img_rgb, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), color, 2)
                cv2.putText(
                    img_rgb,
                    f"{label}:{note_id} {conf:.2f}",
                    (int(x - w / 2), int(y - h / 2 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )

            for i, lx in enumerate(LANE_X_POSITIONS):
                cv2.line(img_rgb, (lx, 0), (lx, bbox["height"]), (100 + i * 20, 200, 255 - i * 30), 1)
                cv2.putText(img_rgb, f"Lane {i}", (lx - 20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 255, 255), 1)
                for j, (label, key) in enumerate(KEYMAP[i].items()):
                    cv2.putText(
                        img_rgb,
                        f"{label}: {key}",
                        (lx - 30, 40 + 15 * j),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        (180, 255, 180),
                        1,
                    )

            cv2.line(img_rgb, (0, JUDGE_LINE_Y), (bbox["width"], JUDGE_LINE_Y), (255, 255, 255), 2)
            cv2.putText(img_rgb, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            cv2.imshow("Note Detection", img_rgb)
            if cv2.getWindowProperty("Note Detection", 0) < 0:
                break
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

finally:
    avg_fps = len(frame_times) / sum(frame_times) if frame_times else 0
    print(f"[INFO] 平均FPS: {avg_fps:.2f}")
    cv2.destroyAllWindows()
