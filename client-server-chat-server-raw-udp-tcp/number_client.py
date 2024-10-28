from echo_client import EchoClient
import socket
import sys


class NumberClient(EchoClient):
    pass


if __name__ == "__main__":
    number_client = NumberClient()
    number_client.run_client()
