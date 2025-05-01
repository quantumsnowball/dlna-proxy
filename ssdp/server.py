import socket
import struct
import time


# SSDP Multicast address and port
class Server:
    ssdp_ip = "239.255.255.250"
    ssdp_port = 1900
    location = "http://192.168.1.88:7879/rootDesc.xml"
    media_type = "urn:schemas-upnp-org:device:MediaServer:1"

    def __init__(self) -> None:
        pass

    def advertise(self) -> None:
        def message() -> bytes:
            return '\r\n'.join((
                'NOTIFY * HTTP/1.1',
                f'HOST: {self.ssdp_ip}:{self.ssdp_port}',
                'NT:',
                'NTS: ssdp:alive',
                'SERVER: Linux/3.10 UPnP/1.0 DLNA/1.5',
                f'USN: uuid:rclone-serve-dlna::{self.media_type}',
                'CACHE-CONTROL: max-age=1800',
                f'LOCATION: {self.location}',
            )).encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        for _ in range(5):
            sock.sendto(message(), (self.ssdp_ip, self.ssdp_port))
            print("Broadcasted SSDP NOTIFY message.")

    def listen(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mreq = socket.inet_aton(self.ssdp_ip)
        mreq += struct.pack(b"@I", socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        try:
            sock.bind(('0.0.0.0', self.ssdp_port))
            print(f"Listening for SSDP M-SEARCH requests on port {self.ssdp_port}...")

            while True:
                data, addr = sock.recvfrom(1024)
                # if b"M-SEARCH" in data:
                print(f"Received M-SEARCH from {addr}, sending reply...")
                response = (
                    'HTTP/1.1 200 OK'
                    'CACHE-CONTROL: max-age=1800'
                    f'DATE: {time.strftime('%a, %d %b %Y %H:%M:%S GMT')}'
                    'EXT:'
                    f'LOCATION: {self.location}'
                    'SERVER: Linux/3.10 UPnP/1.0 DLNA/1.5'
                    f'ST: {self.media_type}'
                    f'USN: uuid:my-rclone-dlna::{self.media_type}'
                ).encode('utf-8')

                sock.sendto(response, addr)
                print(f'sendto() {addr=}')
        except Exception as e:
            print(e)
        finally:
            sock.close()


if __name__ == "__main__":
    server = Server()
    server.advertise()
    server.listen()
