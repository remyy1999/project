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
overall_timeout = 600  #

def signal_handler(signal, frame):
    print("\nGracefully shutting down the server...")
    # Close all active connections before exiting
    for conn, cid, _ in active_connections:
        print(f"Connection {cid} closed due to signal.")
        conn.close()
    sys.exit(0)

def handle_client(client_socket, connection_id):
    global file_dir
    global active_connections

    print(f"Connection {connection_id} established.")

    client_socket.settimeout(10)

    data_received = b""  # Initialize data_received
    start_time = time.time()

    try:
        # Send 'accio' message
        client_socket.send(b"accio\r\n")

        while b"accio" not in data_received:
            chunk = client_socket.recv(4096)
            if not chunk:
                break

            data_received += chunk

            start_time = time.time()

        while b"FILE_SENT" not in data_received:
            chunk = client_socket.recv(4096)
            if not chunk:
                break

            data_received += chunk

        # Save the data or write an ERROR message
        save_file(connection_id, data_received)

    except socket.timeout:
        print(f"Timeout during connection {connection_id}. Closing connection and writing ERROR.")
        # Save an ERROR file
        save_file(connection_id, b"ERROR")
    except socket.error as e:
        print(f"Error during connection {connection_id}: {e}")

    finally:
        # Close the client socket
        client_socket.close()

        active_connections = [(conn, cid, st) for conn, cid, st in active_connections if cid != connection_id]

        print(f"Connection {connection_id} closed.")

def save_file(connection_id, data):
    global file_dir

    filename = os.path.join(file_dir, f"{connection_id}.file")

    if data:
        with open(filename, "wb") as file:
            file.write(data)
    else:
        # Create an empty file if no data is received
        open(filename, 'w').close()

def main():
    global connection_counter
    global file_dir
    global active_connections
    global overall_timeout

    # Check for the correct number of command-line arguments
    if len(sys.argv) != 3:
        sys.stderr.write("ERROR: Usage: python3 server.py <PORT> <FILE-DIR>\n")
        sys.exit(1)

    # Extract command-line arguments
    port = int(sys.argv[1])
    file_dir = sys.argv[2]

    # Check if the port number is in the valid range
    if not (0 <= port <= 65535):
        sys.stderr.write("ERROR: Port number must be in the range 0-65535\n")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Bind the server socket to listen on all interfaces
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(10)

        print(f"Server listening on port {port}, saving files to {file_dir}")

        while True:
            try:
                client_socket, addr = server_socket.accept()

                # Start a new thread for each connection
                connection_counter += 1
                client_thread = threading.Thread(target=handle_client, args=(client_socket, connection_counter))
                client_thread.start()

                # Add the connection to the active list
                active_connections.append((client_socket, connection_counter, time.time()))

                # Accept another connection if there are less than 10 active connections
                if len(active_connections) < 10:
                    continue

                # Check for connections that exceeded the overall timeout
                for conn, cid, start_time in active_connections:
                    if time.time() - start_time > overall_timeout:
                        print(f"Connection {cid} exceeded overall timeout. Closing connection and writing ERROR.")
                        # Save an ERROR file
                        save_file(cid, b"ERROR")
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



