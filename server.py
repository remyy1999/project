import socket
import threading
import signal
import sys
import os
import time

# Global variables
connection_counter = 0
file_dir = ""

def signal_handler(signal, frame):
    print("\nGracefully shutting down the server...")
    sys.exit(0)

def handle_client(client_socket, connection_id):
    global file_dir

    print(f"Connection {connection_id} established.")
    client_socket.send(b"accio\r\n")

    data_received = b""
    start_time = time.time()

    try:
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break

            data_received += chunk

            # Reset the timer if new data is received
            start_time = time.time()

    except socket.error as e:
        print(f"Error during connection {connection_id}: {e}")

    finally:
        # Close the client socket
        client_socket.close()

        # Save the data or write an ERROR message
        save_file(connection_id, data_received)

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

    if len(sys.argv) != 3:
        sys.stderr.write("ERROR: Usage: python3 server.py <PORT> <FILE-DIR>\n")
        sys.exit(1)

    port = int(sys.argv[1])
    file_dir = sys.argv[2]

    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    # Set up the main server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(10)

        print(f"Server listening on port {port}")

        while True:
            client_socket, addr = server_socket.accept()

            # Increment connection counter
            connection_counter += 1

            # Create a new thread for each client connection
            client_thread = threading.Thread(target=handle_client, args=(client_socket, connection_counter))
            client_thread.start()

    except socket.error as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nServer interrupted. Closing...")
        sys.exit(0)

if __name__ == "__main__":
    main()
