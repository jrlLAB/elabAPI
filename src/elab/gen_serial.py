from .main import instrument
import time
import numpy as np

class gen_serial(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, **kwargs)
        self.model = 'gen_serial'
        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')

    def send(self,comm):
        self.ser.write(bytes(comm, 'utf-8'))

    def readline(self):
        return self.ser.readline().decode('utf-8')
