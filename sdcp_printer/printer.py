class Printer:
    def __init__(self, discovery_data):
        self.ip_address = discovery_data['Data']['MainboardIP']
