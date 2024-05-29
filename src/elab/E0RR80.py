from .main import instrument
import time

class E0RR80(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, **kwargs)

        self.model = 'E0RR80'
        self.type = 'balance'

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')


    def query_mass(self):
        self.ser.setRTS(False)
        self.ser.read_all()
        time.sleep(1)
        packet = 'P\r'
        self.ser.write(packet.encode('ascii'))
        output, mass = self.ser.readline().decode().split('g')[0].split(' '), []
        for x in output:
            if x != '':
                mass.append(x)
        mass = float(''.join(mass))
        return mass
    
    def tare(self):
        packet = 'T\r'
        self.ser.write(packet.encode('ascii'))

    def on(self):
        packet = 'ON\r'
        self.ser.write(packet.encode('ascii'))

    def on(self):
        packet = 'ON\r'
        self.ser.write(packet.encode('ascii'))