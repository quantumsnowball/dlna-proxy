import argparse
import logging
import socket
import struct
import uuid

# logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('ssdp.py')


# main class Server
class Server:
    # SSDP default broadcasting ip and port
    ssdp_ip = "239.255.255.250"
    ssdp_port = 1900
    # rclone dlna default xml document
    document = 'rootDesc.xml'
    # dlna media type
    media_type = "urn:schemas-upnp-org:device:MediaServer:1"
    # dlna server type (follow rclone)
    server_type = "Linux/3.4 DLNADOC/1.50 UPnP/1.0 DMS/1.0"
    # random uuid
    uuid = uuid.uuid4()

    def __init__(self, host: str, port: str) -> None:
        # more attributes based on args
        self.host = host
        self.port = port
        self.location = f'http://{host}:{port}/{self.document}'

    # auto advertise itself (referencing rclone)
    def advertise(self) -> None:
        # message format
        def message(nt: str) -> bytes:
            # each line separated by '\r\n'
            return '\r\n'.join((
                'NOTIFY * HTTP/1.1',
                f'HOST: {self.ssdp_ip}:{self.ssdp_port}',
                f'NT: {nt}',
                'NTS: ssdp:alive',
                f'SERVER: {self.server_type}',
                f'USN: uuid:{self.uuid}::{self.media_type}',
                'CACHE-CONTROL: max-age=1800',
                f'LOCATION: {self.location}',
                '\r\n',  # important empty line at the end, otherwise syntax error
            )).encode("utf-8")

        # default use ipv4 UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # set socket to multicast
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        # broadcast NT field values as follows (referencing rclone)
        for nt in (
            'urn:microsoft.com:service:X_MS_MediaReceiverRegistrar:1',
            f'uuid:{self.uuid}',
            'urn:schemas-upnp-org:service:ConnectionManager:1',
            'upnp:rootdevice',
            'urn:schemas-upnp-org:service:ContentDirectory:1',
            'urn:schemas-upnp-org:device:MediaServer:1',
        ):
            sock.sendto(message(nt), (self.ssdp_ip, self.ssdp_port))

        logger.info('Python custom SSDP server started')

    # listen to discovery SSDP query and answer them
    def listen(self) -> None:
        # message format
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
                '\r\n',  # important empty line at the end, otherwise syntax error
            )).encode('utf-8')

        # default use ipv4 UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # allow address reuse
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # convert to binary format addr
        mreq = socket.inet_aton(self.ssdp_ip)
        # listen on any interface
        mreq += struct.pack(b"@I", socket.INADDR_ANY)
        # join the SSDP multicast group
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # also receive multicast packet sent by myself
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        try:
            # list on all interface on port 1900
            sock.bind(('0.0.0.0', self.ssdp_port))
            logger.info(f"Listening for SSDP M-SEARCH requests on port {self.ssdp_port}...")

            # keep receiving message from socket
            while True:
                data, addr = sock.recvfrom(1024)
                # but only reponse to m-search request
                if data.startswith(b"M-SEARCH"):
                    sock.sendto(message(), addr)
                    logger.debug(f'sock.sendto(message, {addr=})')

        except Exception as e:
            logger.error(e)
        finally:
            # clean up
            sock.close()


# run as a python script
if __name__ == "__main__":
    # accept host and port as command line args
    parser = argparse.ArgumentParser(description='Start the server.')
    parser.add_argument('host', type=str, help="server's ip address")
    parser.add_argument('port', type=int, help="server's port")
    args = parser.parse_args()

    # ssdp server
    server = Server(args.host, args.port)
    # advertise itself on launch
    server.advertise()
    # keep listening forever until keyboard interrupt
    server.listen()
