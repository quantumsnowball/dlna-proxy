import socket
import time


# SSDP Multicast address and port
class Server:
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    DLNA_LOCATION = "http://192.168.1.88:7879/"  # Replace with your rclone serve DLNA location
    MEDIA_TYPE = "urn:schemas-upnp-org:device:MediaServer:1"

    def __init__(self) -> None:
        pass

    def advertise(self) -> None:
        message = (
            'NOTIFY * HTTP/1.1'
            f'HOST: {self.SSDP_ADDR}:{self.SSDP_PORT}'
            'CACHE-CONTROL: max-age=1800'
            f'LOCATION: {self.DLNA_LOCATION}'
            'SERVER: Linux/3.10 UPnP/1.0 DLNA/1.5'
            f'ST: {self.MEDIA_TYPE}'
            f'USN: uuid:my-rclone-dlna::{self.MEDIA_TYPE}'
        ).replace("\n", "\r\n").encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        for _ in range(5):
            sock.sendto(message, (self.SSDP_ADDR, self.SSDP_PORT))
            print("Broadcasted SSDP NOTIFY message.")

# def broadcast_ssdp():
#     message = f"""NOTIFY * HTTP/1.1
# HOST: {SSDP_ADDR}:{SSDP_PORT}
# CACHE-CONTROL: max-age=1800
# LOCATION: {DLNA_LOCATION}
# SERVER: Linux/3.10 UPnP/1.0 DLNA/1.5
# ST: {MEDIA_TYPE}
# USN: uuid:my-rclone-dlna::{MEDIA_TYPE}
# """.replace("\n", "\r\n").encode("utf-8")
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
#     for _ in range(5):
#         sock.sendto(message, (SSDP_ADDR, SSDP_PORT))
#         print("Broadcasted SSDP NOTIFY message.")
#
#
# # Function to listen for M-SEARCH requests and reply
# def listen_for_msearch():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#     try:
#         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         sock.bind(('0.0.0.0', SSDP_PORT))
#         print(f"Listening for SSDP M-SEARCH requests on port {SSDP_PORT}...")
#
#         while True:
#             data, addr = sock.recvfrom(1024)
#             # if b"M-SEARCH" in data:
#             if addr[0] == '192.168.1.56':
#                 print(f"Received M-SEARCH from {addr}, sending reply...")
#                 response = f"""HTTP/1.1 200 OK
# CACHE-CONTROL: max-age=1800
# DATE: {time.strftime('%a, %d %b %Y %H:%M:%S GMT')}
# EXT:
# LOCATION: {DLNA_LOCATION}
# SERVER: Linux/3.10 UPnP/1.0 DLNA/1.5
# ST: {MEDIA_TYPE}
# USN: uuid:my-rclone-dlna::{MEDIA_TYPE}
#
# """
#                 sock.sendto(response.encode(), addr)
#                 print(f'sendto() {addr=}')
#     except Exception as e:
#         print(e)
#     finally:
#         sock.close()
#

# Run broadcast once at startup
# broadcast_ssdp()

# Start listening for M-SEARCH
# listen_for_msearch()


if __name__ == "__main__":
    server = Server()
    server.advertise()
