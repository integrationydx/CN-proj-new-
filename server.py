import hashlib
import os
import socket
import sqlite3
import ssl
import threading

HOST = "0.0.0.0"
PORT = 5001
DB_PATH = "reservation.db"
CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"

db_lock = threading.Lock()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS seats (
                seat TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                user TEXT
            )"""
        )

        defaults = [("C1", hash_password("pass1")), ("C2", hash_password("pass2"))]
        for username, password in defaults:
            cur.execute(
                "INSERT OR IGNORE INTO users(username, password) VALUES (?, ?)",
                (username, password),
            )

        for index in range(1, 6):
            cur.execute(
                "INSERT OR IGNORE INTO seats(seat, status, user) VALUES (?, 'free', NULL)",
                (f"A{index}",),
            )

        conn.commit()


def build_response(rows):
    return "\n".join(rows) if rows else ""


def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.execute("PRAGMA busy_timeout = 5000")
    cur = db.cursor()

    try:
        while True:
            data = conn.recv(4096).decode().strip()
            if not data:
                break

            parts = data.split()
            command = parts[0].upper()

            if command == "LOGIN" and len(parts) == 3:
                username, password = parts[1], parts[2]
                cur.execute("SELECT password FROM users WHERE username = ?", (username,))
                row = cur.fetchone()
                if row and row[0] == hash_password(password):
                    conn.sendall(b"Login successful")
                else:
                    conn.sendall(b"Invalid credentials")

            elif command == "LOCK" and len(parts) == 3:
                seat, username = parts[1].upper(), parts[2]
                with db_lock:
                    cur.execute("SELECT status FROM seats WHERE seat = ?", (seat,))
                    row = cur.fetchone()
                    if not row:
                        conn.sendall(b"Seat not found")
                    elif row[0] == "free":
                        cur.execute(
                            "UPDATE seats SET status = 'locked', user = ? WHERE seat = ?",
                            (username, seat),
                        )
                        db.commit()
                        conn.sendall(f"{seat} locked".encode())
                    else:
                        conn.sendall(f"{seat} not available".encode())

            elif command == "BOOK" and len(parts) == 3:
                seat, username = parts[1].upper(), parts[2]
                with db_lock:
                    cur.execute("SELECT status, user FROM seats WHERE seat = ?", (seat,))
                    row = cur.fetchone()
                    if row and row[0] == "locked" and row[1] == username:
                        cur.execute(
                            "UPDATE seats SET status = 'booked' WHERE seat = ?",
                            (seat,),
                        )
                        db.commit()
                        conn.sendall(f"{seat} booked".encode())
                    else:
                        conn.sendall(b"Cannot book")

            elif command == "CANCEL" and len(parts) == 3:
                seat, username = parts[1].upper(), parts[2]
                with db_lock:
                    cur.execute("SELECT user FROM seats WHERE seat = ?", (seat,))
                    row = cur.fetchone()
                    if row and row[0] == username:
                        cur.execute(
                            "UPDATE seats SET status = 'free', user = NULL WHERE seat = ?",
                            (seat,),
                        )
                        db.commit()
                        conn.sendall(f"{seat} cancelled".encode())
                    else:
                        conn.sendall(b"Not your booking")

            elif command == "MAP":
                cur.execute("SELECT seat, status FROM seats ORDER BY seat")
                rows = [f"{seat}: {status}" for seat, status in cur.fetchall()]
                conn.sendall(build_response(rows).encode() or b"No seats")

            elif command == "STATUS":
                cur.execute("SELECT seat, status, user FROM seats ORDER BY seat")
                rows = [str(row) for row in cur.fetchall()]
                conn.sendall(build_response(rows).encode() or b"No seats")

            elif command == "MYBOOKINGS" and len(parts) == 2:
                username = parts[1]
                cur.execute(
                    "SELECT seat FROM seats WHERE user = ? AND status = 'booked' ORDER BY seat",
                    (username,),
                )
                rows = [row[0] for row in cur.fetchall()]
                conn.sendall(str(rows).encode())

            else:
                conn.sendall(b"Invalid command")

    except Exception as exc:
        print(f"[ERROR] {addr}: {exc}")
    finally:
        db.close()
        conn.close()
        print(f"[DISCONNECTED] {addr}")


def create_server_context():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        raise FileNotFoundError(
            "cert.pem/key.pem not found. Generate a self-signed certificate before running the server."
        )

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    return context


def main():
    init_db()
    context = create_server_context()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[SERVER STARTED] {HOST}:{PORT}")

    while True:
        client_sock, addr = server.accept()
        secure_conn = context.wrap_socket(client_sock, server_side=True)
        thread = threading.Thread(target=handle_client, args=(secure_conn, addr), daemon=True)
        thread.start()


if __name__ == "__main__":
    main()
