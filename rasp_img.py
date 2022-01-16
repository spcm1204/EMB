import cv2
import socket
import struct
import pickle
import threading
import time

def recv_img(client_socket):
    data = b""
    payload_size = struct.calcsize(">L")
    count = 0
    

    while True:
        # 프레임 수신
        while len(data) < payload_size:
            data += client_socket.recv(4096)
            
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        while len(data) < msg_size:
            data += client_socket.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        print("@@@@@@recv success@@@@@@ {}".format(msg_size)) # 프레임 크기 출력

        # 역직렬화(de-serialization) : 직렬화된 파일이나 바이트를 원래의 객체로 복원하는 것
        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes") # 직렬화되어 있는 binary file로 부터 객체로 역직렬화
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR) # 프레임 디코딩

        # 영상 출력
        cv2.imshow('img',frame)
        if cv2.waitKey(1) == ord('q') : # q를 입력하면 종료
            cv2.destroyWindow('img')
        time.sleep(5)
        cv2.destroyWindow('img')
        cv2.imwrite(str(count)+'.jpg', frame)



ip = '192.168.133.149' # ip 주소
port = 8080 # port 번호

# 소켓 객체를 생성 및 연결
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((ip, port))
print('연결 성공')



# 사진 전송받기 위한 thread
thread = threading.Thread(target = recv_img, args = (client_socket, ))
thread.start()

