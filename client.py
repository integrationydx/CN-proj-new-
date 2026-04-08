import socket
import ssl

HOST = "127.0.0.1"
PORT = 5001


def connect():
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    secure_socket = context.wrap_socket(raw_socket, server_hostname=HOST)
    secure_socket.connect((HOST, PORT))
    return secure_socket


def main():
    print("Reservation System")
    username = input("Login as client (ex: C1, C2): ").strip()
    password = input("Password: ").strip()

    with connect() as sock:
        sock.sendall(f"LOGIN {username} {password}".encode())
        print(sock.recv(4096).decode())

        while True:
            command = input(f"{username}> ").strip()
            if not command:
                continue
            if command.lower() == "logout":
                break

            parts = command.split()
            action = parts[0].upper()

            if action in {"LOCK", "BOOK", "CANCEL"} and len(parts) == 2:
                message = f"{action} {parts[1]} {username}"
            elif action == "MYBOOKINGS":
                message = f"MYBOOKINGS {username}"
            elif action in {"MAP", "STATUS"}:
                message = action
            else:
                print("Invalid command")
                continue

            sock.sendall(message.encode())
            print(sock.recv(4096).decode())


if __name__ == "__main__":
    main()
