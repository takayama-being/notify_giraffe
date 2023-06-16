# coding: utf-8
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import cv2
import time
from vidgear.gears import CamGear
import datetime
import boto3
import json

s3 = boto3.resource('s3')

base_options = python.BaseOptions(model_asset_path='./dataset/efficientnet_lite0_int8_2.tflite')
options = vision.ImageClassifierOptions(
    base_options=base_options, max_results=4)
classifier = vision.ImageClassifier.create_from_options(options)

def clasification_to_json(classification_result):
    first = classification_result.classifications[0].categories[0]
    second = classification_result.classifications[0].categories[1]
    third = classification_result.classifications[0].categories[2]

    return {
        'classifications': {
            '1st': {
                'category': first.category_name,
                'score': f'{round(first.score * 100, 2)}%'
            },
            '2nd': {
                'category': second.category_name,
                'score': f'{round(second.score * 100, 2)}%'
            },
            '3rd': {
                'category': third.category_name,
                'score': f'{round(third.score * 100, 2)}%'
            }
        }
    }

def zebra_exist(classification_result):
    data = classification_result.classifications[0].categories
    for i in range(3):
         if data[i].category_name == "zebra":
            return True      
    return False

# 本番のストリーミング
source_url = "https://www.youtube.com/watch?v=ydYDqZQpim8"
# devのデータ用
dev_url = "https://www.youtube.com/watch?v=6asnFsav__4"

stream = CamGear(
    source=os.environ.get("SOURCE_URL", dev_url),
    stream_mode=True,
    logging=True
).start()
start_time = time.time()

last_snapshot_time = start_time
interval_sec = int(os.environ.get("INTERVAL_SEC", '10'))
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
            
            # imageの保存先
            image_file_name = f'frame_{current_datetime}.jpg'
            image_file_path = os.path.join('images', image_file_name)
            
            # 分析結果の保存先
            json_file_name = f'frame_{current_datetime}.json'
            json_file_path = os.path.join('classification', json_file_name)

            # jpegの画像を保存
            cv2.imwrite(image_file_path, frame)
            
            # 保存した画像を分析する
            image = mp.Image.create_from_file(image_file_path)
            classification_result = classifier.classify(image)
            
            # 分析結果をJSONにして保存する
            json_data = json.dumps(clasification_to_json(classification_result))
            with open(json_file_path, 'w') as file:
                file.write(json_data)

            last_snapshot_time = current_time

            # ローカルファイルからデータをロードし、しまうまの存在可否によってアップロードするバケットを分ける
            image_data = open(image_file_path, 'rb')
            json_data = open(json_file_path, 'rb')
            
            # バケット名をキリンにしてしまった。。。
            if zebra_exist(classification_result):
                s3.Bucket('notify-giraffe').put_object(Key=f'giraffe_found/{image_file_name}', Body=image_data)
                s3.Bucket('notify-giraffe').put_object(Key=f'giraffe_found/{json_file_name}', Body=json_data)
                
            else:
                s3.Bucket('notify-giraffe').put_object(Key=f'giraffe_not_found/{image_file_name}', Body=image_data)
                s3.Bucket('notify-giraffe').put_object(Key=f'giraffe_not_found/{json_file_path}', Body=json_data)

            # ローカルファイルを削除
            os.remove(image_file_path)
            os.remove(json_file_path)

stream.stop()