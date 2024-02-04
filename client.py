import sys
import socket
import time
import random
import logging

class AccioClient:
    BUFFER_SIZE = 10000
    ERROR_PROBABILITY = 0.1

    def __init__(self, host, port, file_path):
        self.host = host
        self.port = port
        self.file_path = file_path
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger("AccioClient")
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def connect_tcp(self):
        try:
            client_socket = socket.create_connection((self.host, self.port), timeout=10)
            self.set_socket_options(client_socket)
            return client_socket
        except socket.timeout:
            self.handle_error("Connection timed out. Make sure the server is reachable.", exit_code=1)
        except (socket.error, OSError) as e:
            self.handle_error(f"Error connecting to the server: {e}", exit_code=1)
            return None

    def handle_error(self, message, exit_code=1):
        self.logger.error(message)
        sys.exit(exit_code)

    def receive_data_until(self, sock, expected_data):
        received_data = b''
        try:
            while expected_data not in received_data:
                data_chunk = sock.recv(1)
                if not data_chunk:
                    raise ConnectionError("Server disconnected unexpectedly.")
                received_data += data_chunk
        except (socket.error, OSError, ConnectionError, socket.timeout) as e:
            self.logger.error(f"Error receiving data: {e}")
        return received_data

    def set_socket_options(self, sock):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1)
        except socket.error as e:
            self.handle_error(f"Error setting socket options: {e}", exit_code=1)

    def send_response(self, sock, response):
        try:
            sock.sendall(response.encode())
        except (socket.error, OSError) as e:
            self.logger.error(f"Error sending response: {e}")

    def read_file_content(self):
        try:
            with open(self.file_path, 'rb') as file:
                return file.read()
        except FileNotFoundError:
            self.handle_error(f"File '{self.file_path}' not found.", exit_code=1)
        except Exception as e:
            self.handle_error(f"Error reading file: {e}", exit_code=1)
        return b''

    def send_file_content(self, sock):
        file_content = self.read_file_content()
        for chunk in self.chunk_data(file_content, self.BUFFER_SIZE):
            self.emulate_delay()
            if random.random() < self.ERROR_PROBABILITY:
                self.logger.warning("Simulated transmission error occurred.")
                continue
            sock.sendall(chunk)

    def emulate_delay(self):
        # Dynamic sleep delay based on buffer size
        time.sleep(min(0.1, self.BUFFER_SIZE / 100000))

    def chunk_data(self, data, chunk_size):
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.host, self.port))
                self.receive_and_send_commands(client_socket)
                self.send_file_content(client_socket)
            except (socket.timeout, socket.error, ConnectionError, socket.gaierror) as e:
                self.logger.error(f"Error during the communication: {e}")
                sys.exit(1)

    def receive_and_send_commands(self, client_socket):
        self.receive_and_send(client_socket, b'accio\r\n', "confirm-accio\r\n")
        self.receive_and_send(client_socket, b'accio\r\n', "confirm-accio-again\r\n\r\n")

    def receive_and_send(self, client_socket, expected_data, response):
        self.receive_data_until(client_socket, expected_data)
        self.send_response(client_socket, response)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <host> <port> <file>")
        sys.exit(1)

    host = sys.argv[1]

    try:
        port = int(sys.argv[2])
    except ValueError:
        print("Invalid port number. Please provide a valid integer port.")
        sys.exit(1)

    file_path = sys.argv[3]

    accio_client = AccioClient(host, port, file_path)
    accio_client.run()

