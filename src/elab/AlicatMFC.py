from .main import instrument
import time

class AlicatMFC(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port,baud_rate=57600, **kwargs)

        self.model = 'Alicat_MFC'
        self.type = 'MFC'
        self.address = 'A'

        if 'address' in kwargs:
            self.address = kwargs.get('address')

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')


    def compile_cmd(self, command, **kwargs):
        ## Define user input variables
        parameter1, parameter2, parameter3 = [kwargs.get(param, '') for param in ('parameter1', 'parameter2', 'parameter3')]

        ## Define useful command codes
        command_dict = {
                        'query_dataframe' : 'A??D*',
                        'query_data' : 'A',
                        'query_avg_data' : f'ADV {parameter1} {parameter2} {parameter3}',
                        'query_gas' : 'AGS',
                        'query_setpoint_range' : 'ALR',
                        'query_max_ramp_rate' : 'ASR',
                        'query_setpoint' : 'ALS',
                        'start_streaming' : 'A@ @',
                        'stop_streaming' : '@@ A',
                        'set_gas' : f'AGS {parameter1}',
                        'set_startup_gas' : f'AGS {parameter1} 1',
                        'change_setpoint' : f'AS {parameter1}',
                        'set_setpoint' : f'ALS {parameter1} {parameter2}',
                        'set_units' : f'ADCU {parameter1} 1 {parameter2}',
                        #'tare_absolute_pressure' : 'APC,  #requires an internal barometer, unclear if we have this or not atm
                        'set_setpoint_mode' : f'ALV {parameter1}',
                        'tare_flow' : 'AV',
                        'set_pressure_limit' : f'AOPL {parameter1}'
                        }
        
        query_dict = {'query_dataframe' : True,'query_data' : True,
                      'query_avg_data' : True,'query_gas' : True,
                      'query_setpoint_range' : True,'query_max_ramp_rate' : True,
                      'query_setpoint' : True, 'tare_flow' : True}
        
        ## Use kwargs to define if you want to print the command hex for troubleshoot
        if 'show_cmd' in kwargs:
            self.show_cmd = kwargs.get('show_cmd')

        command_packet = command_dict[command]+'\r'
        packet = command_packet.encode()
        self.ser.write(packet)

        try:
            if query_dict[command] == True:
                time.sleep(1)
        except KeyError: 
            pass

        self.response = self.ser.read_all()
        if self.response == b'':
            time.sleep(0.1)
            self.response = self.ser.read_all()
        if self.verbose == True:
            print('command Alicat: ',packet)
            print('response Alicat:',self.response)
        return self.response

    def query_dataframe(self):
        return self.compile_cmd(command = 'query_dataframe')

    def query_data(self):
        return self.compile_cmd(command = 'query_data')
        
    def query_avg_data(self, time, statistic, **kwargs):
        if len(kwargs)== 1:
            return self.compile_cmd(command = 'query_avg_data', parameter1 = time, parameter2 = statistic, parameter3 = kwargs.get(kwargs[0]))
        else:
             return self.compile_cmd(command = 'query_avg_data', parameter1 = time, parameter2 = statistic)

    def query_gas(self):
        return self.compile_cmd(command = 'query_gas')
    
    def query_setpoint(self):
        return self.compile_cmd(command = 'query_setpoint')
    
    def list_setpoint_mode(self):
        mode_dict = {'Statistic' : 'Value',
                     'Absolute pressure' : 34,
                     'Volumetric flow' : 36,
                     'Mass flow' : 37,
                     'Gauge pressure' : 38,
                     'Pressure differential' : 39
                     }
        return mode_dict

    def query_setpoint_range(self):
        return self.compile_cmd(command = 'query_setpoint_range')
    
    def query_max_ramp_rate(self):
        return self.compile_cmd(command = 'query_max_ramp_rate')
    
    def list_gases(self):
        packet = 'A??G*\r'
        self.ser.write(packet.encode())
        time.sleep(1)
        return self.ser.read_all()
        #return self.compile_cmd(command = 'list_gases')
    
    def start_streaming(self):
        self.compile_cmd(command = 'start_streaming')

    def stop_streaming(self):
        self.compile_cmd(command = 'stop_streaming')
        
    def set_gas(self,gas_num):
        if type(gas_num) != int:
            raise TypeError('Value must be an integer between 0 and 210. Call list_gases() for more info.')
        else:
            self.compile_cmd(command = 'set_gas', parameter1 = gas_num)

    def set_startup_gas(self,gas_num):
        return self.compile_cmd(command = 'set_startup_gas', parameter1 = gas_num)

    def change_setpoint(self,value):
        self.compile_cmd(command = 'change_setpoint', parameter1 = value)

    def set_unit(self,statistic,unit_value):
        if type(statistic) or type(unit_value) != int:
            raise TypeError('Values must be integers')
        else:
            self.compile_cmd(command = 'set_unit', parameter1 = statistic, parameter2 = unit_value)
    
    def set_setpoint(self,setpoint_val, **kwargs):
        if 'unit_val' in kwargs:
            self.compile_cmd(command = 'set_setpoint', parameter1 = setpoint_val, parameter2 = kwargs.get('unit_val'))
        self.compile_cmd(command = 'set_setpoint', parameter1 = setpoint_val)
    
    def set_setpoint_mode(self,setpoint_mode):
        if type(setpoint_mode) != int:
            raise TypeError('Value must be an integer. Call list_setpoint_modes() for more info')
        else:
            return self.compile_cmd(command = 'set_setpoint_mode', parameter1 = setpoint_mode)
    
    def tare_flow(self):
        return self.compile_cmd(command = 'tare_flow')

    def set_pressure_limit(self, pressure_limit):
        if pressure_limit == 0:
            raise ValueError('Do not remove pressure limit.')
        self.compile_cmd(command = 'set_pressure_limit', parameter1 = pressure_limit)


