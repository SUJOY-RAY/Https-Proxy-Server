import socket
import threading

brave-browser --proxy-server="http://127.0.0.1:8888"




# Define constants for the proxy server
HOST = '127.0.0.1'  # Proxy server will run locally
PORT = 8888         # Port to listen on

# Blocklist for content filtering
BLOCKED_DOMAINS = ['blockedwebsite.com', 'badcontent.com']
BLOCKED_KEYWORDS = ['gambling', 'malware']

# Function to handle client requests
def handle_client(client_socket, client_address):
    # Receive client request
    request = client_socket.recv(4096)

    # Parse the request to get the target server's host and port
    request_lines = request.split(b'\r\n')
    first_line = request_lines[0].decode('utf-8')
    print(f"Request from {client_address}: {first_line}")
    
    # Extract the URL from the HTTP request
    url = first_line.split(' ')[1]
    http_pos = url.find('://')  # Find 'http://' or 'https://'
    if http_pos != -1:
        url = url[(http_pos + 3):]  # Remove protocol

    port_pos = url.find(':')  # Find the port (if specified)
    path_pos = url.find('/')
    
    if path_pos == -1:
        path_pos = len(url)

    web_server = url[:path_pos]  # Extract host
    port = 80  # Default HTTP port

    # If the port is specified in the URL, use it
    if port_pos != -1 and port_pos < path_pos:
        port = int(url[(port_pos + 1):path_pos])
        web_server = url[:port_pos]

    # Content filtering: Check if the URL or domain is blocked
    if any(domain in web_server for domain in BLOCKED_DOMAINS):
        print(f"[!] Blocked access to {web_server}")
        client_socket.send(b"HTTP/1.1 403 Forbidden\r\n\r\nBlocked by proxy server.")
        client_socket.close()
        return

    # Check for blocked keywords in the URL path
    if any(keyword in url for keyword in BLOCKED_KEYWORDS):
        print(f"[!] Blocked content with keyword in {url}")
        client_socket.send(b"HTTP/1.1 403 Forbidden\r\n\r\nBlocked content by proxy server.")
        client_socket.close()
        return

    # Create a socket to connect to the target server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((web_server, port))
        # Forward the client's request to the target server
        server_socket.send(request)

        # Receive the response from the server and forward it back to the client
        while True:
            response = server_socket.recv(4096)
            if len(response) > 0:
                client_socket.send(response)
            else:
                break
    except Exception as e:
        print(f"[!] Error connecting to {web_server}: {e}")
        client_socket.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    finally:
        server_socket.close()
        client_socket.close()

# Main function to start the proxy server
def start_proxy():
    # Create a server socket to accept client connections
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((HOST, PORT))
    proxy_socket.listen(5)
    print(f"[*] Proxy Server running on {HOST}:{PORT}")

    while True:
        # Accept incoming client connection
        client_socket, client_address = proxy_socket.accept()
        print(f"[+] Received connection from {client_address}")

        # Handle the client request in a new thread
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

# Start the proxy server
if __name__ == '__main__':
    start_proxy()
