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

    # Set a timeout for the 'accio' message
    client_socket.settimeout(10)

    data_received = b""  # Initialize data_received

    try:
        # Receive data until 'accio' is found or timeout occurs
        while b"accio" not in data_received:
            chunk = client_socket.recv(4096)
            if not chunk:
                break

            data_received += chunk

        # Rest of the code...

        # Inform the server that the file has been completely sent
        while b"FILE_SENT" not in data_received:
            chunk = client_socket.recv(4096)
            if not chunk:
                break

            data_received += chunk

    except socket.timeout:
        print(f"Timeout during connection {connection_id}. Closing connection.")
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
    if len(sys.argv) != 4:
        sys.stderr.write("ERROR: Usage: python3 client.py <HOST> <PORT> <FILE>\n")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    file_path = sys.argv[3]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((host, port))

            # Send 'accio' message immediately after connection
            client_socket.send(b"accio\r\n")

            with open(file_path, "rb") as file:
                data = file.read(4096)
                while data:
                    client_socket.send(data)
                    data = file.read(4096)

            # Inform the server that the file has been completely sent
            client_socket.send(b"FILE_SENT\r\n")

        except socket.error as e:
            print(f"Error during connection: {e}")

    print("Client finished.")

if __name__ == "__main__":
    main()



