from .main import instrument

class MUX8(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, baud_rate=115200, **kwargs)
        self.model = 'Arduino MUX'
        self.type = 'MUX'
        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')

    def electrode(self,n):
        n += 10
        if n not in range(11,19):
            raise ValueError('Electrode n must be between 1 and 8')
        self.send_comm(n)
        
    def ida(self,n):
        if n not in range(1,5):
            raise ValueError('IDA n must be between 1 and 4')
        self.send_comm(n)

    def gen(self,n):
        n_gen = [14,13,12,11]
        if n not in range(1,5):
            raise ValueError('Generator n must be between 1 and 4')
        self.send_comm(n_gen[n-1])

    def coll(self,n):
        n_coll = [15,16,17,18]
        if n not in range(1,5):
            raise ValueError('Collector n must be between 1 and 4')
        self.send_comm(n_coll[n-1])

    def send_comm(self,n):
        self.ser.write(bytes(f'<{n}>', 'utf-8'))
        msg = self.ser.readline()
        if self.verbose == True:
            print(msg.decode('utf-8'))

    def gen_all(self):
        self.send_comm(30)
    
    def coll_all(self):
        self.send_comm(20)

    def all(self):
        self.send_comm(40)