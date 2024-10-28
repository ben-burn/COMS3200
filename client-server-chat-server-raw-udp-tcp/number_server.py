from echo_server import EchoServer
import socket
import sys


class NumberServer(EchoServer):
    """
    Inherit from echo_server.py
    """
    def __init__(self):
        super().__init__()

    def convert_message(self, recv_data):
        """
        Convert numerical digits into their verbal equivalents
        :param recv_data: data received from the client
        :return: the converted verbal equivalents if numerical
        digits is provided, otherwise return "Invalid message"
        """
        num_dict = {
            "0": "zero", "1": "one", "2": "two", "3": "three",
            "4": "four", "5": "five", "6": "six", "7": "seven",
            "8": "eight", "9": "nine"
        }
        num = recv_data.decode().strip()
        if num not in num_dict or not num:
            return "Invalid message"
        else:
            return num_dict[num]

    def receive_and_send_messages(self):
        """
        Use a while loop to continuously receive, convert and
        send messages to the client.
        :return: None
        """
        while True:
                data = self.receive_message()
                if not data:
                    break  # Client closed connection
                converted_message = self.convert_message(data)
                self.send_message(converted_message)
        self.conn.close()
        self.socket.close()

    def run_number_server(self):
        """
        Start the number server to receive, convert and
        send back messages to the client
        :return: None
        """
        self.read_port_number()
        self.listen_on_port()
        self.receive_and_send_messages()


if __name__ == '__main__':
    number_server = NumberServer()
    number_server.run_number_server()