import socket
import sys
import signal
import select

def sig_handler(signo, _):
    if signo in [signal.SIGQUIT, signal.SIGTERM, signal.SIGINT]:
        sys.exit(0)

def accio_server(port):
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Bind the socket to any available interface and the specified port
        server_socket.bind(('0.0.0.0', port))

        # Set the server socket to non-blocking mode
        server_socket.setblocking(0)

        # Listen for incoming connections with a maximum of 10 pending connections
        server_socket.listen(10)

        print(f"Accio Server listening on 0.0.0.0:{port}")

        # Register signal handlers
        signal.signal(signal.SIGQUIT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT, sig_handler)

        while True:
            # Accept a connection or handle a timeout if no data received
            conn, addr = None, None
            try:
                conn, addr = server_socket.accept()
            except socket.error as e:
                pass

            if conn:
                print(f"Connection from {addr}")

                # Send the first accio command
                conn.sendall(b'accio\r\n')

                # Receive confirmation
                readable, _, _ = select.select([conn], [], [], 10)
                if not readable:
                    sys.stderr.write("ERROR: Timeout waiting for data from the client\n")
                    conn.close()
                    continue

                confirmation = conn.recv(1024)
                print(f"First confirmation received: {confirmation}")

                # Send the second accio command
                conn.sendall(b'accio\r\n')

                # Receive the second confirmation
                readable, _, _ = select.select([conn], [], [], 10)
                if not readable:
                    sys.stderr.write("ERROR: Timeout waiting for data from the client\n")
                    conn.close()
                    continue

                second_confirmation = conn.recv(1024)
                print(f"Second confirmation received: {second_confirmation}")

                # Receive and process the binary file
                data = b''
                while True:
                    readable, _, _ = select.select([conn], [], [], 10)
                    if not readable:
                        sys.stderr.write("ERROR: Timeout waiting for data from the client\n")
                        conn.close()
                        break

                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk

                # Calculate and print the number of bytes received
                header_size = len(b'accio\r\naccio\r\n')
                num_bytes_received = len(data) - header_size
                print(f"Number of bytes received: {num_bytes_received}")

                # Close the connection
                conn.close()

    except Exception as e:
        print(f"Error in server: {str(e)}")

    finally:
        # Close the server socket
        server_socket.close()

if __name__ == "__main__":
    # Check for the correct number of command-line arguments
    if len(sys.argv) != 2:
        sys.stderr.write("ERROR: Invalid number of arguments. Usage: python server-s.py <port>\n")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if not (0 <= port <= 65535):
            raise ValueError("Invalid port number")
    except ValueError as e:
        sys.stderr.write(f"ERROR: {str(e)}\n")
        sys.exit(1)

    # Start the server
    accio_server(port)

def accio_client(host, port, file_path):
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((host, port))

        # Receive the first accio command
        first_accio = client_socket.recv(1024)
        print(f"Received first accio command: {first_accio.decode()}")

        # Send confirmation for the first accio command
        client_socket.sendall(b'ACK\r\n')

        # Receive the second accio command
        second_accio = client_socket.recv(1024)
        print(f"Received second accio command: {second_accio.decode()}")

        # Send confirmation for the second accio command
        client_socket.sendall(b'ACK\r\n')

        # Send binary file
        with open(file_path, 'rb') as file:
            file_data = file.read()
            client_socket.sendall(file_data)

    except Exception as e:
        print(f"Error in client: {str(e)}")

    finally:
        # Close the connection
        client_socket.close()

# Example usage
accio_client('127.0.0.1', 12345, 'path/to/your/file.bin')

