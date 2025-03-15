import socket
import threading

import request_types

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 8000

def receive_messages(sock):
    """ソケットからメッセージを受信し続けるスレッド関数"""
    while True:
        try:
            # バッファサイズを4096バイトとしてデータを受信
            data, server = sock.recvfrom(4096)
            username_length = int.from_bytes(data[:1], "big")
            username = data[1:username_length+1].decode('utf-8')
            message = data[username_length+1:].decode('utf-8')
            print(f"\n{username}: {message}")
            print(">> ", end='', flush=True)  # 入力プロンプトを再表示
        except Exception as e:
            print(e)
            break

def main():
    try:
        print('your name?: ')
        username = input()
        username_binary = username.encode('utf-8')
        usernamelen = len(username_binary)
        usernamelen_binary = usernamelen.to_bytes(1, byteorder='big')
        request_type_binary = request_types.REGISTER_USER.to_bytes(1, byteorder='big')
        address = (server_address, server_port)
        
        # ユーザー名を送信
        print('sending {!r}'.format(username))
        sent = sock.sendto(request_type_binary + usernamelen_binary + username_binary, address)
        print(f"sent {sent} bytes")
        
        # 受信用スレッドを開始
        receive_thread = threading.Thread(target=receive_messages, args=(sock,))
        receive_thread.daemon = True  # メインスレッドが終了したら一緒に終了
        receive_thread.start()
        
        while True:
            print(">> ", end='', flush=True)
            message = input()
            if message.lower() == 'exit':
                break
                
            message_binary = message.encode('utf-8')
            if len(request_type_binary + usernamelen_binary + message_binary) > 4096:
                print("The message was not sent because it's too long.")
                continue

            request_type_binary = request_types.SEND_MESSAGE.to_bytes(1, byteorder='big')
            
            sock.sendto(request_type_binary + usernamelen_binary + message_binary, address)
    
    except KeyboardInterrupt:
        print("\nQuit program")
    except Exception as e:
        print(e)
    finally:
        print('Close socket')
        sock.close()

if __name__ == "__main__":
    main()