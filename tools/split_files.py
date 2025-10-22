#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import random
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont

# ---------- 共通関数 ----------
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# ---------- GUIで選択 ----------
def select_input_folder():
    path = filedialog.askdirectory()
    if path:
        input_var.set(path)

def select_output_folder():
    path = filedialog.askdirectory()
    if path:
        output_var.set(path)

# ---------- ファイル移動・コピー ----------
def move_file_with_label(image_path, dst_img_dir, dst_lbl_dir, label_base, copy_mode):
    base_name = os.path.basename(image_path)
    name, _ = os.path.splitext(base_name)
    label_path = os.path.join(label_base, f"{name}.txt")

    dst_img_path = os.path.join(dst_img_dir, base_name)
    dst_lbl_path = os.path.join(dst_lbl_dir, f"{name}.txt")

    ensure_dir(os.path.dirname(dst_img_path))
    ensure_dir(os.path.dirname(dst_lbl_path))

    try:
        if copy_mode:
            shutil.copy2(image_path, dst_img_path)
            if os.path.exists(label_path):
                shutil.copy2(label_path, dst_lbl_path)
        else:
            shutil.move(image_path, dst_img_path)
            if os.path.exists(label_path):
                shutil.move(label_path, dst_lbl_path)
    except Exception as e:
        messagebox.showerror("エラー", f"ファイルの処理に失敗しました：\n{e}")

# ---------- 実行処理 ----------
def execute_split():
    input_dir = input_var.get()
    output_dir = output_var.get()
    copy_mode = copy_var.get()
    ratio_str = ratio_var.get()

    try:
        ratio = float(ratio_str)
        if not (0 < ratio < 100):
            raise ValueError
    except ValueError:
        messagebox.showerror("エラー", "0〜100未満の割合を入力してください")
        return

    if not input_dir or not output_dir:
        messagebox.showerror("エラー", "入力および出力フォルダを設定してください")
        return

    images_dir = os.path.join(input_dir, "images")
    labels_dir = os.path.join(input_dir, "labels")

    if not os.path.exists(images_dir):
        messagebox.showerror("エラー", f"images フォルダが存在しません: {images_dir}")
        return

    # 出力先のtrain/valパス作成
    out_img_train = os.path.join(output_dir, "images", "train")
    out_img_val = os.path.join(output_dir, "images", "val")
    out_lbl_train = os.path.join(output_dir, "labels", "train")
    out_lbl_val = os.path.join(output_dir, "labels", "val")

    # 拡張子フィルタ
    files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not files:
        messagebox.showinfo("情報", "images フォルダに画像がありません。")
        return

    random.shuffle(files)
    split_index = int(len(files) * ratio / 100)

    train_files = files[:split_index]
    val_files = files[split_index:]

    for fname in train_files:
        img_path = os.path.join(images_dir, fname)
        move_file_with_label(img_path, out_img_train, out_lbl_train, labels_dir, copy_mode)

    for fname in val_files:
        img_path = os.path.join(images_dir, fname)
        move_file_with_label(img_path, out_img_val, out_lbl_val, labels_dir, copy_mode)

    messagebox.showinfo("完了", f"分割完了\nTrain: {len(train_files)}枚\nVal: {len(val_files)}枚")

# ---------- GUI構築 ----------
root = tk.Tk()
root.title("画像＆ラベル振り分けツール")

default_font = tkfont.nametofont("TkDefaultFont")
default_font.configure(family="Meiryo", size=10)
root.option_add("*Font", default_font)

input_var = tk.StringVar()
output_var = tk.StringVar()
ratio_var = tk.StringVar(value="80")
copy_var = tk.BooleanVar(value=True)

tk.Label(root, text="データセットのルートフォルダ（images/labels含む）:").grid(row=0, column=0, sticky="e")
tk.Entry(root, textvariable=input_var, width=50).grid(row=0, column=1)
tk.Button(root, text="選択", command=select_input_folder).grid(row=0, column=2)

tk.Label(root, text="出力フォルダ（images/train等が生成されます）:").grid(row=1, column=0, sticky="e")
tk.Entry(root, textvariable=output_var, width=50).grid(row=1, column=1)
tk.Button(root, text="選択", command=select_output_folder).grid(row=1, column=2)

tk.Label(root, text="Train 割合（%）:").grid(row=2, column=0, sticky="e")
tk.Entry(root, textvariable=ratio_var, width=10).grid(row=2, column=1, sticky="w")

tk.Checkbutton(root, text="コピー（OFFで移動）", variable=copy_var).grid(row=3, column=1, sticky="w", pady=5)

tk.Button(root, text="実行", command=execute_split, bg="lightblue").grid(row=4, column=1, pady=10)

root.mainloop()
