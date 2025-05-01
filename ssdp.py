import argparse
import socket
import struct
import uuid


class Server:
    ssdp_ip = "239.255.255.250"
    ssdp_port = 1900
    document = 'rootDesc.xml'
    media_type = "urn:schemas-upnp-org:device:MediaServer:1"
    server_type = "Linux/3.4 DLNADOC/1.50 UPnP/1.0 DMS/1.0"
    uuid = uuid.uuid4()

    def __init__(self, host: str, port: str) -> None:
        self.host = host
        self.port = port
        self.location = f'http://{host}:{port}/{self.document}'

    def advertise(self) -> None:
        def message(nt: str) -> bytes:
            return '\r\n'.join((
                'NOTIFY * HTTP/1.1',
                f'HOST: {self.ssdp_ip}:{self.ssdp_port}',
                f'NT: {nt}',
                'NTS: ssdp:alive',
                f'SERVER: {self.server_type}',
                f'USN: uuid:{self.uuid}::{self.media_type}',
                'CACHE-CONTROL: max-age=1800',
                f'LOCATION: {self.location}',
                '\r\n',
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

        print('Python custom SSDP server started\n')

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
                'Cache-Control: max-age=1800',
                'Ext: ',
                f'Location: {self.location}',
                f'Server: {self.server_type}',
                f'St: {self.media_type}',
                f'Usn: uuid:{self.uuid}::{self.media_type}',
                'Content-Length: 0',
                '\r\n',
            )).encode('utf-8')
        try:
            sock.bind(('0.0.0.0', self.ssdp_port))
            print(f"Listening for SSDP M-SEARCH requests on port {self.ssdp_port}...")

            while True:
                data, addr = sock.recvfrom(1024)
                if data.startswith(b"M-SEARCH"):
                    sock.sendto(message(), addr)

        except Exception as e:
            print(e)
        finally:
            sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start the server.')
    parser.add_argument('host', type=str, help="server's ip address")
    parser.add_argument('port', type=int, help="server's port")
    args = parser.parse_args()

    server = Server(args.host, args.port)
    server.advertise()
    server.listen()
