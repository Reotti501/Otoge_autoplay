# class_remap_train_val.py

import os

# -------------------- 設定ここから --------------------
# モデルBのクラス順（元の順番）
old_classes = ['tap', 'long', 'left_flick', 'right_flick']

# モデルAのクラス順（正しい順番）
new_classes = ['tap', 'long', 'right_flick', 'left_flick']

# ラベルディレクトリのルート（例: datasets/merged/labels）
label_root_dir = 'models/deresute/raw/dere2/labels'

# 処理対象のサブディレクトリ（trainとval）
subdirs = ['train', 'val']
# -------------------- 設定ここまで --------------------

# クラスIDのマッピング辞書 {旧ID: 新ID}
remap = {old_classes.index(cls): new_classes.index(cls) for cls in old_classes}

# 各サブディレクトリ（train, val）を処理
for subdir in subdirs:
    target_dir = os.path.join(label_root_dir, subdir)
    if not os.path.exists(target_dir):
        print(f"⚠️ フォルダが存在しません: {target_dir}")
        continue

    print(f"🔁 処理中: {target_dir}")

    for filename in os.listdir(target_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(target_dir, filename)

            with open(file_path, 'r') as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue
                old_id = int(parts[0])
                new_id = remap.get(old_id, old_id)  # 万一対応外なら元のID
                new_line = ' '.join([str(new_id)] + parts[1:])
                new_lines.append(new_line)

            with open(file_path, 'w') as f:
                f.write('\n'.join(new_lines) + '\n')

    print(f"✅ 完了: {target_dir}")

print("🎉 すべての変換が完了しました。")
