import socket
from typing import Optional


def find_available_port(start_port: int = 8080, max_attempts: int = 100) -> Optional[int]:
    """
    Find an available port starting from start_port.

    Args:
        start_port: The port to start searching from
        max_attempts: Maximum number of ports to try

    Returns:
        An available port number, or None if no port is found
    """
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None


def is_port_available(port: int) -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: The port number to check

    Returns:
        True if the port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
            return True
    except OSError:
        return False
