from .main import instrument

class HS7(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, **kwargs)

        self.model = 'C-MAG HS7'
        self.type = 'hotplate'
        self.max_temp = 50

        if 'max_temp' in kwargs:
            self.max_temp = kwargs.get('max_temp')

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')

    def query_temp(self):
        packet = 'IN_PV_1\r\n'
        self.ser.write(packet.encode('utf-8'))
        return float(self.ser.read_until().decode().split(' ')[0])
    
    def set_temp(self, temp, **kwargs):
        if (self.max_temp >= temp > 0) == True:
            packet = f'OUT_SP_1 {temp}\r\n'
        else:
            packet = f'OUT_SP_1 {self.max_temp}\r\n'
            print(f'Value out of range! Set to {self.max_temp}')
        self.ser.write(packet.encode('utf-8'))
        
    def start_temp(self):
        packet = f'START_1\r\n'
        self.ser.write(packet.encode('utf-8'))

    def stop_temp(self):
        packet = f'STOP_1\r\n'
        self.ser.write(packet.encode('utf-8'))
    
    def set_spin(self, spin):
        if (1500 >= spin  > 0) == True:
            packet = f'OUT_SP_4 {spin}\r\n'
        else:
            packet = f'OUT_SP_1 {1500}\r\n'
            print(f'Value out of range! Set to {1500}')
        self.ser.write(packet.encode('utf-8'))

    def start_spin(self):
        packet = f'START_4\r\n'
        self.ser.write(packet.encode('utf-8'))
        
    def stop_spin(self):
        packet = f'STOP_4\r\n'
        self.ser.write(packet.encode('utf-8'))
