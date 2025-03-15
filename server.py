import socket
import os
import threading
import time

import request_types

# ソケット設定
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
port = 8000
ttl = 15 #[s]

# 接続済みクライアントの情報を保存
clients = {}  # キー: username_length 値: クライアント情報

# クライアントメッセージを他のクライアントに転送する関数
def forward_message_to_others(message_data, sender_username_length):
    """
    送信者以外のすべてのクライアントにメッセージを転送する
    """
    
    for client in list(clients.items()):
        # 送信者自身には送らない
        if client[0] != sender_username_length:
            client_address = client[1]['address']
            try:
                sock.sendto(message_data, client_address)
                print(f'Sent to {client_address}.')
            except Exception as e:
                print(f"Send error {client_address}: {e}")
                clients.pop(client[0], None)

def remove_non_active_clients():
    """
    定期的に不要なクライアントを削除する
    """
    while True:
        now = time.time()
        for client in list(clients.items()):
            if now - client[1]['last_active'] > ttl:
                client_address = client[1]['address']
                username_binary = 'System Administrator'.encode('utf-8')
                username_binary_len = len(username_binary)
                message_binary = f"[Session expired]{client[1]['username']} has been removed from this session.".encode('utf-8')
                sock.sendto(username_binary_len.to_bytes(1, byteorder='big') + username_binary + message_binary, client_address)
                clients.pop(client[0], None)
                print(clients)

        time.sleep(2)


# メイン処理
def main():
    try:
        # ソケットのセットアップ
        try:
            os.unlink(server_address)
        except (FileNotFoundError, OSError):
            pass

        print(f'Starting up on {server_address}:{port}')
        sock.bind((server_address, port))
        
        print('Waiting...')

        remove_thread = threading.Thread(target=remove_non_active_clients)
        remove_thread.daemon = True
        remove_thread.start()
        
        while True:
            data, address = sock.recvfrom(4096)
            request_type = int.from_bytes(data[:1], "big")
            username_length = int.from_bytes(data[1:2], "big")
            now = time.time()

            if request_type == request_types.REGISTER_USER:
                print('Register')
                username = data[1:].decode('utf-8')
                clients[username_length] = {
                    'address': address,
                    'username': username,
                    'last_active': now  # 最終アクティブ時間も記録
                }
                print('clients: {}'.format(clients))

            elif request_type == request_types.DELETE_USER:
                clients.pop(username_length, None)

            elif request_type == request_types.SEND_MESSAGE:
                print('Received a message.')
                username = clients.get(username_length, { 'username': 'x' * username_length })["username"]
                message_binary = data[2:]
                message = message_binary.decode('utf-8')

                if username_length in clients:
                    # クライアント情報の更新
                    clients[username_length]['address'] = address
                    clients[username_length]['last_active'] = now
                    
                    # 非同期で他のクライアントにメッセージを転送
                    username_binary = clients[username_length]['username'].encode('utf-8')
                    forward_thread = threading.Thread(
                        target=forward_message_to_others,
                        args=(username_length.to_bytes(1, byteorder='big') + username_binary + message_binary, username_length)
                    )
                    forward_thread.daemon = True
                    forward_thread.start()
                    
                print(f"ユーザー名: {username}")
                print(f"メッセージ: {message}")

    except KeyboardInterrupt:
        print("\nBye")
    finally:
        sock.close()
        print("Close socket")

if __name__ == "__main__":
    main()