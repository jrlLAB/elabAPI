from .main import instrument
import time
import numpy as np
from sklearn.linear_model import LinearRegression

class pH_arduino(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, **kwargs)
        self.delay = 30
        self.average = 10
        self.model = 'Arduino pH meter'
        self.type = 'pH'
        self.cal_curve = False
        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')

    def send_comm(self):
        self.ser.write(bytes('<pH>', 'utf-8'))
        msg = self.ser.readline()
        return int(msg.decode('utf-8'))
    
    #measure the voltage output from the pH meter
    def voltage(self, **kwargs):
        if 'delay' in kwargs:
            self.delay = kwargs.get('delay')
        if 'average' in kwargs:
            self.average = kwargs.get('average') 
        time.sleep(self.delay)
        return np.mean([self.send_comm() for i in range(self.average)])

    #measure pH. Uses the estimator in load_cal() to predict pH from voltage() output. cannot be ran prior to load_cal
    def measure(self, **kwargs):
        if self.cal_curve == False:
            raise ValueError('No calibration curve loaded')
        X = np.array(self.voltage(**kwargs)).reshape(-1,1)
        return float(self.cal_curve.predict(X))