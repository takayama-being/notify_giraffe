# coding: utf-8
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import os
from os.path import join, dirname
from dotenv import load_dotenv

import cv2
import time
import os
import pdb;
from vidgear.gears import CamGear
import datetime
import slackweb

# 環境変数設定
load_dotenv(join(dirname(__file__), '.env'))
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# slack通知先設定
slack = slackweb.Slack(url=SLACK_WEBHOOK_URL)

base_options = python.BaseOptions(model_asset_path='./dataset/efficientnet_lite0_int8_2.tflite')
options = vision.ImageClassifierOptions(
    base_options=base_options, max_results=4)
classifier = vision.ImageClassifier.create_from_options(options)

# 本番のストリーミング
source_url = "https://www.youtube.com/watch?v=ydYDqZQpim8"
# devのデータ用
dev_url = "https://www.youtube.com/watch?v=6asnFsav__4"

stream = CamGear(
    source=dev_url,
    stream_mode=True,
    logging=True
).start()
start_time = time.time()

last_snapshot_time = start_time
interval_sec = 1
while True:
    frame = stream.read()

    if frame is None:
        print("ビデオストリームの終了")
        break
    else:
        current_time = time.time()
        elapsed_time = current_time - last_snapshot_time

        # プログラム上の1秒とstrem.read()の1秒は一緒ではないため
        # n秒ごとのフレームを保存しそのフレームに対して実行とはなっていない
        if (elapsed_time >= interval_sec):
            current_datetime = datetime.datetime.fromtimestamp(current_time).strftime("%Y%m%d%H%M%S")
            file_name = f'frame_{current_datetime}.jpg'
            file_path = os.path.join('images', file_name)
            cv2.imwrite(file_path, frame)
            last_snapshot_time = current_time

            image = mp.Image.create_from_file(file_path)
            classification_result = classifier.classify(image)
            top_category = classification_result.classifications[0].categories[0]

            print(f"{top_category.category_name} ({top_category.score:.2f})")

            if top_category.category_name == "zebra":
                print("しまうまが現われた！")
                notify_text = "しまうまが現われた！"
            else:
                print("しまうまはいないようだ")
                # os.remove(file_path)
                notify_text = "しまうまはいないようだ"
            slack.notify(text=notify_text)

stream.stop()