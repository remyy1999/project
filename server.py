import socket
import threading
import signal
import sys
import os
import time

# Global variables
connection_counter = 0
file_dir = ""
active_connections = []  

def signal_handler(signal, frame):
    print("\shutting down the server...")
    for conn, _, _ in active_connections:
        conn.close()
    sys.exit(0)

def handle_client(client_socket, connection_id):
    global file_dir
    global active_connections

    print(f"Connection {connection_id} established.")

    # Set a timeout for the 'accio' message 
    client_socket.settimeout(10)
    overall_timeout = 600  # 10 minutes overall timeout

    data_received = b""  # Initialize data_received
    start_time = time.time()

    try:
        # Send 'accio' message
        client_socket.send(b"accio\r\n")

        # Receive data until 'accio' is found or timeout occurs
        while b"accio" not in data_received:
            chunk = client_socket.recv(4096)
            if not chunk:
                break

            data_received += chunk

            # Reset the timer if new data is received
            start_time = time.time()

        while b"FILE_SENT" not in data_received:
            chunk = client_socket.recv(4096)
            if not chunk:
                break

            data_received += chunk

        save_file(connection_id, data_received)

    except socket.timeout:
        print(f"Timeout during connection {connection_id}. Closing connection.")
    except socket.error as e:
        print(f"Error during connection {connection_id}: {e}")

    finally:
        # Close the client socket
        client_socket.close()

        # Remove the connection 
        active_connections = [(conn, cid, st) for conn, cid, st in active_connections if cid != connection_id]

        print(f"Connection {connection_id} closed.")

def save_file(connection_id, data):
    global file_dir

    filename = os.path.join(file_dir, f"{connection_id}.file")

    if data:
        with open(filename, "wb") as file:
            file.write(data)
    else:
        with open(filename, "w") as file:
            file.write("ERROR")

def main():
    global connection_counter
    global file_dir
    global active_connections

    if len(sys.argv) != 3:
        sys.stderr.write("ERROR: Usage: python3 server.py <PORT> <FILE-DIR>\n")
        sys.exit(1)

    port = int(sys.argv[1])

    if not (0 <= port <= 65535):
        sys.stderr.write("ERROR: Port number must be in the range 0-65535\n")
        sys.exit(1)

    file_dir = sys.argv[2]

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(10)

        print(f"Server listening on port {port}")

        while True:
            try:
                client_socket, addr = server_socket.accept()

                # Start a new thread for each connection
                connection_counter += 1
                client_thread = threading.Thread(target=handle_client, args=(client_socket, connection_counter))
                client_thread.start()

                # Add the connection to the active list
                active_connections.append((client_socket, connection_counter, time.time()))

                if len(active_connections) < 10:
                    continue

                for conn, cid, start_time in active_connections:
                    if time.time() - start_time > overall_timeout:
                        print(f"Connection {cid} exceeded overall timeout. Closing connection.")
                        conn.close()

                # Wait for all threads to finish
                for thread in threading.enumerate():
                    if thread != threading.current_thread():
                        thread.join()

                # Clear finished threads
                active_connections = [(conn, cid, st) for conn, cid, st in active_connections if conn.is_alive()]

            except socket.error as e:
                print(f"Error accepting connection: {e}")

    except socket.error as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nServer interrupted. Waiting for threads to finish...")
        for conn, _, _ in active_connections:
            conn.close()
        for thread in threading.enumerate():
            if thread != threading.current_thread():
                thread.join()
        print("All threads finished. Closing...")
        sys.exit(0)

if __name__ == "__main__":
    main()


