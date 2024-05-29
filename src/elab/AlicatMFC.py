from .main import instrument

class AlicatMFC(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port,baud_rate=19200, **kwargs)

        self.model = 'Alicat'
        self.type = 'controller'
        self.address = 'A'

        if 'address' in kwargs:
            self.address = kwargs.get('address')

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')


    def compile_cmd(self, command, **kwargs):
        ## Define user input variables
        parameter1, parameter2, parameter3 = [kwargs.get(param, '') for param in ('parameter1', 'parameter2', 'parameter3')]

        ## Define useful command codes
        command_dict = {'query_dataframe' : f'A??D*',
                        'query_data' : 'A',
                        'query_avg_data' : f'ADV {parameter1} {parameter2} {parameter3}',
                        'start_streaming' : 'A@ @',
                        'stop_streaming' : '@@ A',
                        'set_gas' : f'AGS {parameter1}',
                        'query_gas' : 'AGS',
                        'list_gases' : 'A??G*',
                        'set_startup_gas' : f'AGS {parameter1} 1',
                        'change_setpoint' : f'AS {parameter1}',
                        'query_setpoint' : 'ALS',
                        'set_setpoint' : f'ALS {parameter1} {parameter2}',
                        'set_units' : f'ADCU {parameter1} 1 {parameter2}',
                        #'tare_absolute_pressure' : 'APC,  #requires an internal barometer, unclear if we have this or not atm
                        'set_setpoint_mode' : f'ALSS {parameter1}',
                        'query_setpoint_range' : 'ALR',
                        'tare_flow' : 'AV',
                        'set_pressure_limit' : f'AOPL {parameter1}',
                        'query_max_ramp_rate' : 'ASR',
                        
                        }
        
        ## Use kwargs to define if you want to print the command hex for troubleshoot
        if 'show_cmd' in kwargs:
            self.show_cmd = kwargs.get('show_cmd')

        command_packet = command_dict[command]+'\r'
        packet = command_packet.encode()

        self.ser.write(packet)
        self.response = self.ser.read(100)
        if self.response == '':
            self.response = self.ser.read(100)
        if self.verbose == True:
            print('command Alicat: ',packet)
            print('response Alicat:',self.response)
        return self.response
    

    def query_dataframe(self):
        self.compile_cmd(command = 'query_dataframe')

    def query_data(self):
        self.compile_cmd(command = 'query_data')
        
    def query_avg_data(self, time, statistic, **kwargs):
        if len(kwargs)== 1:
            self.compile_cmd(command = 'query_avg_data', parameter1 = time, parameter2 = statistic, parameter3 = kwargs.get(kwargs[0]))
        else:
            self.compile_cmd(command = 'query_avg_data', parameter1 = time, parameter2 = statistic)

    def start_streaming(self):
        self.compile_cmd(command = 'start_streaming')

    def stop_streaming(self):
        self.compile_cmd(command = 'stop_streaming')
        
    def set_gas(self,gas_num):
        if type(gas_num) != int:
            raise TypeError('Value must be an integer between 0 and 210. Call list_gases() for more info.')
        else:
            self.compile_cmd(command = 'set_gas', parameter1 = gas_num)

    def query_gas(self):
        self.compile_cmd(command = 'query_gas')

    def list_gases(self):   #will have to adjust for response length
        self.compile_cmd(command = 'list_gases')

    def set_startup_gas(self,gas_num):
        self.compile_cmd(command = 'set_startup_gas', parameter1 = gas_num)

    def change_setpoint(self,value):
        self.compile_cmd(command = 'change_setpoint', parameter1 = value)

    def set_unit(self,statistic,unit_value):
        if type(statistic) or type(unit_value) != int:
            raise TypeError('Values must be integers')
        else:
            self.compile_cmd(command = 'set_unit', parameter1 = statistic, parameter2 = unit_value)

    def query_setpoint(self):
        self.compile_cmd(command = 'query_setpoint')
    
    def set_setpoint(self,setpoint_val, **kwargs):
        if 'unit_val' in kwargs:
            self.compile_cmd(command = 'set_setpoint', parameter1 = setpoint_val, parameter2 = kwargs.get('unit_val'))
        self.compile_cmd(command = 'set_setpoint', parameter1 = setpoint_val)
    
    def set_setpoint_mode(self,setpoint_mode):
        if type(setpoint_mode) != int:
            raise TypeError('Value must be an integer. Call list_setpoint_modes() for more info')
        else:
            self.compile_cmd(command = 'set_unit', parameter1 = setpoint_mode)
    
    def list_setpoint_mode(self):
        mode_dict = {'Statistic' : 'Value',
                     'Absolute pressure' : 34,
                     'Volumetric flow' : 36,
                     'Mass flow' : 37,
                     'Gauge pressure' : 38,
                     'Pressure differential' : 39
                     }
        print(mode_dict)

    def query_setpoint_range(self):
        self.compile_cmd(command = 'query_setpoint_range')

    def tare_flow(self):
        self.compile_cmd(command = 'tare_flow')

    def set_pressure_limit(self, pressure_limit):
        if pressure_limit == 0:
            raise ValueError('Do not remove pressure limit.')
        self.compile_cmd(command = 'set_pressure_limit', parameter1 = pressure_limit)

    def query_max_ramp_rate(self):
        self.compile_cmd(command = 'query_max_ramp_rate')
