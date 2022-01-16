from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
import socket
import pickle
import struct


#--------tcp socket setting--------#
#----------------------------------#
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print("Socket successfully created")
host = '192.168.133.149'
port = 8080

server_socket.bind((host, port))
print("socket binded to %s" %(port))

server_socket.listen(2)
print("socket is listening")

client_socket, addr = server_socket.accept()
print("C++ accept success")
python_socket, addr2 = server_socket.accept()
print("python accept success")
#----------------------------------#


#--------Image Processing--------#
#--------------------------------#

# 사전학습된 얼굴영역 검출 모델 로드
facenet = cv2.dnn.readNet('models/deploy.prototxt', 'models/res10_300x300_ssd_iter_140000.caffemodel')
# 사전학습된 마스크 착용 유무 검출 모델 로드
model = load_model('models/mask_detector.model')

# 웹캠 영상 가져오기
cap = cv2.VideoCapture(0)

ret, img = cap.read()

# 버튼을 눌렀으나, 얼굴이 인식되지 않는 경우를 위한 flag 설정
faceFlags = 0

# jpeg 형식 저장 시, 이미지 품질 설정
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]


while cap.isOpened():
    
    # 가장 가까운 얼굴을 특정하기 위한 리스트 선언
    area = list()
    # 인원별 마스크 착용 확률을 저장하기위한 리스트 선언
    mask_list = list()

    # Host PC(Raspberry PI4 B+)로 부터 버튼이 눌렸다는 메세지가 들어오면 영상처리 진행
    if(client_socket.recv(5)):
        ret, img = cap.read()
        if not ret:
            break
        h, w = img.shape[:2]

        # 이미지 전처리 진행
        blob = cv2.dnn.blobFromImage(img, scalefactor=1., size=(300, 300), mean=(104., 177., 123.))
        facenet.setInput(blob)
        
        # facenet의 추론결과(몇번째 얼굴인지, 얼굴 영역일 확률, 얼굴 영역의 좌표)를 dets에 저장
        dets = facenet.forward()

        result_img = img.copy()

        # 검출된 모든 얼굴에 대하여 마스크 착용 유무 추론 진행
        for i in range(dets.shape[2]):
            
            # 얼굴 영역일 확률을 가져와, 50% 미만인 경우 continue
            confidence = dets[0, 0, i, 2]
            if confidence < 0.5:
                continue

            x1 = int(dets[0, 0, i, 3] * w)
            y1 = int(dets[0, 0, i, 4] * h)
            x2 = int(dets[0, 0, i, 5] * w)
            y2 = int(dets[0, 0, i, 6] * h)
            
            # 얼굴 면적 리스트에 Append
            area.append(np.abs(x1-x2) * np.abs(y1-y2))

            # 얼굴영역만 따로 Clipping
            face = img[y1:y2, x1:x2]

            # 마스크 착용 유무 추론을 위한 이미지 전처리
            face_input = cv2.resize(face, dsize=(224, 224))
            face_input = cv2.cvtColor(face_input, cv2.COLOR_BGR2RGB)
            face_input = preprocess_input(face_input)
            face_input = np.expand_dims(face_input, axis=0)
            
            # 마스크 착용 유무 추론 (mask를 착용했을확률, mask를 착용하지 않았을 확률 반환)
            mask, nomask = model.predict(face_input).squeeze()
            # 마스크 착용 확률 append
            mask_list.append(mask)

            if mask > nomask:
                color = (0, 255, 0)
                label = 'Mask %d%%' % (mask * 100)
            else:
                color = (0, 0, 255)
                label = 'No Mask %d%%' % (nomask * 100)
            
            if mask == 1:
                mask = 0.9999
            faceFlags = 1

            # 얼굴영영 및 마스크 착용 확률을 이미지위에 덧그리기
            cv2.rectangle(result_img, pt1=(x1, y1), pt2=(x2, y2), thickness=2, color=color, lineType=cv2.LINE_AA)
            cv2.putText(result_img, text=label, org=(x1, y1 - 10), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, color=color, thickness=2, lineType=cv2.LINE_AA)
        
        # 얼굴이 검출되었을 경우, 가장 얼굴이 가까이 있는 사람의 마스크 착용 확률을 Host PC로 전송
        if faceFlags == 1:
            mask = mask_list[np.argmax(area)]
            client_socket.send(str(mask).encode())
            print(str(mask))
            faceFlags = 0
        else:
            mask = 0.0000
            client_socket.send(str(mask).encode())
            print("not found")

        # 마스크 착용확률이 표시된 이미지를 Host PC로 전송
        result, frame = cv2.imencode('.jpg', result_img, encode_param)
        data = pickle.dumps(frame, 0)
        size = len(data)
        python_socket.sendall(struct.pack(">L", size) + data)

        print(mask)

        # 디버깅 용
        cv2.imshow('result', result_img)

        # 과도한 Resource 사용을 방지하기위한 Delay 추가
        if cv2.waitKey(1) == ord('q'):
            break

cap.release()
#--------------------------------#