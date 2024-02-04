import sys
import socket
import time
import random

class AccioClient:
    def __init__(self, host, port, file_path):
        self.host = host
        self.port = port
        self.file_path = file_path

    def connect_tcp(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_socket_options(sock)
            sock.settimeout(10)  # Set a 10-second timeout for the connection
            sock.connect((self.host, self.port))
            return sock
        except (socket.error, OSError) as e:
            print(f"Error connecting to the server: {e}")
            return None

    def receive_data_until(self, sock, expected_data):
        received_data = b''
        try:
            while expected_data not in received_data:
                data_chunk = sock.recv(1)
                if not data_chunk:
                    raise ConnectionError("Server disconnected unexpectedly.")
                received_data += data_chunk
        except (socket.error, OSError, ConnectionError, socket.timeout) as e:
            print(f"Error receiving data: {e}")
        return received_data

    def set_socket_options(self, sock):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1)
        except socket.error as e:
            print(f"Error setting socket options: {e}")

    def send_response(self, sock, response):
        try:
            sock.sendall(response.encode())
        except (socket.error, OSError) as e:
            print(f"Error sending response: {e}")

    def send_file_content(self, sock):
        buffer_size = 10000
        error_probability = 0.1  # Example: 10% probability of error

        try:
            with open(self.file_path, 'rb') as file:
                while True:
                    file_chunk = file.read(buffer_size)
                    if not file_chunk:
                        break  # Break the loop if the entire file has been read

                    # Introduce a sleep delay (emulated delay)
                    time.sleep(0.1)  # 100 milliseconds delay

                    # Simulated transmission error based on probability
                    if random.random() < error_probability:
                        print("Simulated transmission error occurred.")
                        continue  # Skip sending this chunk and try the next one

                    sock.sendall(file_chunk)

        except FileNotFoundError:
            print(f"File '{self.file_path}' not found.")
        except Exception as e:
            print(f"Error sending file: {e}")

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.host, self.port))

                # Wait for the first "accio\r\n" command
                self.receive_data_until(s, b'accio\r\n')

                # Send the first response
                self.send_response(s, "confirm-accio\r\n")

                # Wait for the second "accio\r\n" command
                self.receive_data_until(s, b'accio\r\n')

                # Send the second response
                self.send_response(s, "confirm-accio-again\r\n\r\n")

                # Send the binary content of the file
                self.send_file_content(s)
            except (socket.error, OSError, ConnectionError, socket.timeout) as e:
                print(f"Error during the communication: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <host> <port> <file>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    file_path = sys.argv[3]

    accio_client = AccioClient(host, port, file_path)
    accio_client.run()

