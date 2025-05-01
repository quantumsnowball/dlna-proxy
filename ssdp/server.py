import socket
import struct
import time


# SSDP Multicast address and port
class Server:
    ssdp_ip = "239.255.255.250"
    ssdp_port = 1900
    location = "http://192.168.1.88:7879/rootDesc.xml"
    media_type = "urn:schemas-upnp-org:device:MediaServer:1"
    uuid = 'rclone-serve-dlna'

    def __init__(self) -> None:
        pass

    def advertise(self) -> None:
        def message(nt: str) -> bytes:
            return '\r\n'.join((
                'NOTIFY * HTTP/1.1',
                f'HOST: {self.ssdp_ip}:{self.ssdp_port}',
                f'NT: {nt}',
                'NTS: ssdp:alive',
                'SERVER: Linux/3.10 UPnP/1.0 DLNA/1.5',
                f'USN: uuid:{self.uuid}::{self.media_type}',
                'CACHE-CONTROL: max-age=1800',
                f'LOCATION: {self.location}',
            )).encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        for nt in (
            'urn:microsoft.com:service:X_MS_MediaReceiverRegistrar:1',
            f'uuid:{self.uuid}',
            'urn:schemas-upnp-org:service:ConnectionManager:1',
            'upnp:rootdevice',
            'urn:schemas-upnp-org:service:ContentDirectory:1',
            'urn:schemas-upnp-org:device:MediaServer:1',
        ):
            sock.sendto(message(nt), (self.ssdp_ip, self.ssdp_port))

    def listen(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mreq = socket.inet_aton(self.ssdp_ip)
        mreq += struct.pack(b"@I", socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        def message() -> bytes:
            return '\r\n'.join((
                'HTTP/1.1 200 OK',
                'CACHE-CONTROL: max-age=1800',
                f'DATE: {time.strftime('%a, %d %b %Y %H:%M:%S GMT')}',
                'EXT:',
                f'LOCATION: {self.location}',
                'SERVER: Linux/3.10 UPnP/1.0 DLNA/1.5',
                f'ST: {self.media_type}',
                f'USN: uuid:my-rclone-dlna::{self.media_type}',
            )).encode('utf-8')
        try:
            sock.bind(('0.0.0.0', self.ssdp_port))
            print(f"Listening for SSDP M-SEARCH requests on port {self.ssdp_port}...")

            while True:
                data, addr = sock.recvfrom(1024)
                if data.startswith(b"M-SEARCH"):
                    sock.sendto(message(), addr)
                    print(f"Received M-SEARCH from {addr}, replied")
        except Exception as e:
            print(e)
        finally:
            sock.close()


if __name__ == "__main__":
    server = Server()
    server.advertise()
    server.listen()
