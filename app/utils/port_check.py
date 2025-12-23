import socket

class PortChecker:
    @staticmethod
    def is_port_open(port: int, host: str = '127.0.0.1', timeout: float = 0.5) -> bool:
        """纯 Socket 检测端口是否开启"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
