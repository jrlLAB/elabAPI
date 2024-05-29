import numpy as np
import pandas as pd
import serial
import time
from sklearn.linear_model import LinearRegression

class instrument():

    def __init__(self, com_port, **kwargs):

        self.com_port = com_port
        self.baud_rate = 9600 #bits/, default for most devices, may need to be changed 
        self.timeout = 1 #1 second timeout
        self.verbose = False #verbose is used by children to either print detailed info or not during operation

        # redefining the below variables if they are found in kwargs
        if 'baud_rate' in kwargs:
            self.baud_rate = kwargs.get('baud_rate')

        if 'verbose' in kwargs:
            self.verbose = kwargs.get('verbose')

        if 'timeout' in kwargs:
            self.timeout = kwargs.get('timeout')

        self.ser = serial.Serial(port=com_port, baudrate=self.baud_rate, timeout=1, rtscts=False)

    def close(self):
        self.ser.close()

class bundle():
    
    def __init__(self, inst_list, **kwargs):
        self.pH_bool, self.plate_bool, self.pump_bool, self.valve_bool, self.port_dict_bool, self.balance_bool = False, False, False, False, False, False
        self.mix_volume = 0
        self.verbose = False

        if 'verbose' in kwargs:
            self.verbose = kwargs.get('verbose')

        self.inst_enabled = [x.model for x in inst_list]

        for x in inst_list:
            if x.type == 'pH':
                self.pH = x
                self.pH_bool = True
            elif x.type == 'hotplate':
                self.plate = x
                self.plate_bool = True
            elif x.type == 'pump':
                self.pump = x
                self.pump_bool = True
            elif x.type == 'valve':
                self.valve = x
                self.valve_bool = True
            elif x.type == 'balance':
                self.balance = x
                self.balance_bool = True

        self.cell_name = 'cell'
        self.waste_name = 'waste'
        self.air_name = 'air'
        self.flush_name = 'flush'

    def change_default_ports(self,cell_name='cell',waste_name='waste',air_name='air',flush_name='flush'):
        self.cell_name = cell_name
        self.waste_name = waste_name
        self.air_name = air_name
        self.flush_name = flush_name
        
    def check_types(self,inst_list):
        if all(inst_list):
            pass
        else:
            raise ValueError('Missing instrument!')

    def load_ports(self, filepath=None):
        if type(filepath) == dict:
            self.port_dict = filepath
            self.port_dict_bool = True
        elif (type(filepath) == str) & ('.csv' in filepath):
            self.check_types([self.valve_bool])
            self.soln_df, self.port_dict  = pd.read_csv(filepath), {}
            for n, x in enumerate(self.soln_df['title'].values):
                self.port_dict[x] = self.soln_df['port'].values[n]
            self.port_dict_bool = True
        if filepath == None:
            raise ValueError('No port dictionary provided')

    def change_cell(self,cell_name):
        self.cell_name = cell_name

    def conc(self,solution):
        title_header = 'title'
        conc_header = 'conc'
        return float(self.soln_df.loc[self.soln_df[title_header] == solution, conc_header].values)
    
    def from_to(self, line_from, line_to, vol):
        self.valve.port(self.port_dict[line_from])
        self.pump.aspirate(vol)
        self.valve.port(self.port_dict[line_to])
        self.pump.discharge(vol)

    def from_to_all(self,line_from,line_to):
        self.valve.port(self.port_dict[line_from])
        self.pump.aspirate(self.pump.total_volume)
        self.valve.port(self.port_dict[line_to])
        self.pump.discharge('all')
    
    def init_line(self,solution):
        self.check_types([self.valve_bool,self.pump_bool])
        if self.verbose == True:
            print(f'initializing line {solution}')
        self.from_to_all(solution,self.waste_name)
        self.from_to_all(self.air_name,self.waste_name)

    def reset_to_waste(self):
        self.check_types([self.valve_bool,self.pump_bool])
        if self.verbose == True:
            print(f'Resetting to waste')
        self.valve.port(self.port_dict[self.waste_name])
        self.pump.reset()


    def light_dispense(self,solution,volume, **kwargs):
        self.check_types([self.valve_bool,self.pump_bool])
        if self.verbose == True:
            print(f'Dispensing {solution}')
    
        self.air_volume = 1
        if 'air_volume' in kwargs:
            self.air_volume = kwargs.get('air_volume')

        self.from_to(solution, self.cell_name, volume)
        self.from_to(self.air_name, self.cell_name, self.air_volume)


    def dispense(self,solution,volume,**kwargs):
        self.check_types([self.valve_bool,self.pump_bool])
        if self.verbose == True:
                print(f'dispensing a total of {volume} mL of {solution}')
        
        self.prime_volume = 0.1
        self.aspirate_volume = self.pump.total_volume

        if 'prime_volume' in kwargs:
            self.prime_volume = kwargs.get('prime_volume')
        if 'aspirate_volume' in kwargs:
            self.aspirate_volume = kwargs.get('aspirate_volume')

        if volume == 0:
            pass
        else:
            self.reset_to_waste()
            volume_counter = volume
            self.from_to(solution, self.waste_name, self.prime_volume)
            if volume > self.aspirate_volume:
                for x in range(int(volume//self.aspirate_volume)):
                    self.light_dispense(solution,self.aspirate_volume)
                    volume_counter -= self.aspirate_volume
                self.light_dispense(solution,volume_counter)
            else:
                self.light_dispense(solution,volume)

    def remove_cell_contents(self,volume):
        self.check_types([self.valve_bool,self.pump_bool])

        volume_counter = volume
        if volume > self.pump.total_volume:
            for x in range(int(volume//self.pump.total_volume)):
                self.from_to_all(self.cell_name,self.waste_name)
                volume_counter -= self.pump.total_volume
            self.from_to(self.cell_name,self.waste_name,volume_counter)
        else:
            self.from_to(self.cell_name,self.waste_name,volume_counter)

    def clean_cell(self, volume, **kwargs):
        self.check_types([self.valve_bool,self.pump_bool])
        if self.verbose == True:
            print('cleaning cell')

        self.extra_volume = 5
        if 'extra_volume' in kwargs:
            self.extra_volume = kwargs.get('extra_volume')

        self.reset_to_waste()
        self.remove_cell_contents(volume+self.extra_volume)
        self.dispense('flush',volume)
        self.remove_cell_contents(volume+self.extra_volume)


    def clear_line(self,solution,**kwargs):
        self.check_types([self.valve_bool,self.pump_bool])
        
        self.air_volume = 1
        if 'air_volume' in kwargs:
            self.air_volume = kwargs.get('air_volume')
        self.from_to_all(self.flush_name,solution)
        self.from_to(self.air_name,solution,self.air_volume)

    def bubble(self,**kwargs):
        self.check_types([self.valve_bool,self.pump_bool])
        
        self.air_volume = 1
        if 'air_volume' in kwargs:
            self.air_volume = kwargs.get('air_volume')
    
        self.from_to(self.air_name,self.cell_name,self.air_volume)

    def calibrate_pH(self,pH_list,**kwargs):
        self.check_types([self.valve_bool,self.pump_bool,self.pH_bool])
        
        self.pH_list = pH_list
        self.voltages = []
        self.extra_volume = 2
        self.buff_volume = 5

        if 'buff_volume' in kwargs:
            self.buff_volume = kwargs.get('buff_volume')
        if 'extra_volume' in kwargs:
            self.extra_volume = kwargs.get('extra_volume')
        
        for x in pH_list:
            pH_dispense = f'pH{x}'
            self.clean_cell(self.buff_volume+self.extra_volume)
            self.prime(pH_dispense,self.buff_volume)
            self.dispense(pH_dispense,self.buff_volume)
            self.bubble(air_volume=5)
            self.voltages.append(self.pH.voltage(**kwargs))
            self.clean_cell(self.buff_volume+1)
        
        
        self.clean_cell(self.buff_volume+self.extra_volume)

        y = np.array(self.pH_list).reshape(-1,1)
        X = np.array(self.voltages).reshape(-1,1)
        self.pH.cal_curve = LinearRegression().fit(X,y)
    


    ##### below is experimental -- everything needs refactored anyways
    ###
    ####
    ###
    ####
    ###
    ####
    ###
        
    def mix_component(self,solution,volume,**kwargs):
        while True:
            self.dispense(solution, volume, **kwargs)
            yield volume
        
    def mix_dispense(self,components):
        volume = sum([x.send(None) for x in components])
        return volume

    def mix_prime(self,components,**kwargs):
        volume = self.mix_dispense(components)
        self.extra_volume = 5
        if 'extra_volume' in kwargs:
            self.extra_volume = kwargs.get('extra_volume')
        self.remove_cell_contents(volume+self.extra_volume)

    def prime(self, solution, volume, **kwargs):
        self.extra_volume = 5
        if 'extra_volume' in kwargs:
            self.extra_volume = kwargs.get('extra_volume')
        self.dispense(solution,volume,**kwargs)
        self.remove_cell_contents(volume+self.extra_volume)
