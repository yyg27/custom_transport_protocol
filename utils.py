import time
import random
import string


def generate_client_id():
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"client_{timestamp}_{random_str}"


def format_bytes(data: bytes, max_len=60) -> str:
    hex_str = data.hex()
    if len(hex_str) > max_len:
        return hex_str[:max_len] + "..."
    return hex_str


def calculate_throughput(bytes_sent: int, duration: float) -> float:
    if duration <= 0:
        return 0.0
    return (bytes_sent / 1024) / duration


def print_header(title: str, width=60):
    print("=" * width)
    print(f"{title.center(width)}")
    print("=" * width)


def print_section(title: str, width=60):
    print("-" * width)
    print(f"  {title}")
    print("-" * width)


def simulate_packet_loss(loss_rate=0.1):
    return random.random() < loss_rate


def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class PerformanceMonitor:
    
    def __init__(self):
        self.start_time = None
        self.packets_sent = 0
        self.packets_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.retransmissions = 0
    
    def start(self):
        self.start_time = time.time()
    
    def record_send(self, size: int):
        self.packets_sent += 1
        self.bytes_sent += size
    
    def record_receive(self, size: int):
        self.packets_received += 1
        self.bytes_received += size
    
    def record_retransmission(self):
        self.retransmissions += 1
    
    def get_stats(self):
        duration = time.time() - self.start_time if self.start_time else 0
        
        return {
            'duration': duration,
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'retransmissions': self.retransmissions,
            'throughput_kb_s': calculate_throughput(self.bytes_sent, duration),
            'packet_loss_rate': self.retransmissions / self.packets_sent if self.packets_sent > 0 else 0
        }
    
    def print_stats(self):
        stats = self.get_stats()
        
        print_section("Performance Statistics")
        print(f"Duration:          {stats['duration']:.2f} seconds")
        print(f"Packets sent:      {stats['packets_sent']}")
        print(f"Packets received:  {stats['packets_received']}")
        print(f"Bytes sent:        {stats['bytes_sent']} ({stats['bytes_sent']/1024:.2f} KB)")
        print(f"Bytes received:    {stats['bytes_received']} ({stats['bytes_received']/1024:.2f} KB)")
        print(f"Retransmissions:   {stats['retransmissions']}")
        print(f"Throughput:        {stats['throughput_kb_s']:.2f} KB/s")
        print(f"Loss rate:         {stats['packet_loss_rate']:.2%}")


#test code
if __name__ == "__main__":
    print("### Utils Test ###\n")
    
    #test 1: Client ID generation
    print("Test 1: Client ID")
    for i in range(3):
        print(f"  {generate_client_id()}")
    print()
    
    #test 2: Format bytes
    print("Test 2: Format bytes")
    data = b"Hello, World!" * 10
    print(f"  Original: {len(data)} bytes")
    print(f"  Formatted: {format_bytes(data)}")
    print()
    
    #test 3: Throughput
    print("Test 3: Throughput")
    throughput = calculate_throughput(10240, 2.5)
    print(f"  10240 bytes in 2.5s = {throughput:.2f} KB/s")
    print()
    
    #test 4: Performance monitor
    print("Test 4: Performance Monitor")
    monitor = PerformanceMonitor()
    monitor.start()
    
    #simulate some activity
    for i in range(10):
        monitor.record_send(512)
        time.sleep(0.1)
        monitor.record_receive(512)
    
    monitor.record_retransmission()
    monitor.record_retransmission()
    
    monitor.print_stats()