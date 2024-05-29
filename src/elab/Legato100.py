from .main import instrument

class Legato100(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port,baud_rate=115200, **kwargs)

        self.model = 'Legato100'
        self.type = 'pump'
        self.address = 0
        self.unit = 'mL'

        if 'address' in kwargs:
            self.address = kwargs.get('address')

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')


    def compile_cmd(self, command, **kwargs):
        ## Define user input variables
        parameter1, parameter2 = [kwargs.get(param, '') for param in ('parameter1', 'parameter2')]

        ## Define useful command codes
        command_dict = {'query_address' : f'address {parameter1}', 
                        'query_catalog' : 'cat',
                        'delete_program' : f'delmethod {parameter1}', 
                        'set_brightness' : f'dim {parameter1}',
                        'set_force' : f'force {parameter1}',
                        'set_rate' : f'irate {parameter1} {parameter2}',
                        'calibrate_tilt' : 'tilt',
                        'set_run_mode' : 'run',
                        'stop' : 'stop',
                        'display_config' : 'Config',
                        'display_syringe' : 'syrm',
                        'set_syringe_volume' : f'svolume {parameter1}',
                        'set_syringe_diameter' : f'diameter {parameter1}',
                        'set_target_volume' : f'tvolume {parameter1} {parameter2}',
                        'set_time' :f'ttime {parameter1}'
                        }
        
        ## Use kwargs to define if you want to print the command hex for troubleshoot
        if 'show_cmd' in kwargs:
            self.show_cmd = kwargs.get('show_cmd')

        command_packet = command_dict[command]+'\r'
        packet = command_packet.encode()

        self.ser.write(packet)
        self.response = self.ser.read_all()
        if self.response == '':
            self.response = self.ser.read_all()
        if self.verbose == True:
            print('command Legato100: ',packet)
            print('response Legato100:',self.response)
        return self.response
    
    def query_address(self):
        return self.compile_cmd(command = 'query_address', parameter1=self.address)
    
    def set_address(self,address):
        self.address=address
        return self.compile_cmd(command = 'query_address', parameter1 = address)
    
    def set_brightness(self,brightness):
        if type(brightness) != int:
            raise TypeError('Value must be an integer')
        if brightness <= 0:
            raise ValueError('Brightness too low')
        if brightness in range(101):
            if self.verbose == True:
                print(f'Brightness set to {brightness}')
            self.compile_cmd(command = 'set_brightness', parameter1 = brightness)
        else:
            raise ValueError("Brightness too high!")
        
    def set_force(self,force,**kwargs):
        if type(force) != int:
            raise TypeError('Value must be an integer between 1 and 100')
        if force <= 0:
            raise ValueError('Force too low. Value must be an integer between 1 and 100')
        if force in range(101):
            if self.verbose == True:
                print(f'Force set to {force}%')
            self.compile_cmd(command = 'set_force', parameter1 = force)
        else:
            raise ValueError("Force too high!")
        
    def set_run_mode(self):
        self.compile_cmd(command = 'set_run_mode')

    def stop(self):
        self.compile_cmd(command = 'stop')

    def display_config(self):
        self.compile_cmd(command = 'config')

    def calibrate_tilt(self):
        self.compile_cmd(command = 'calibrate_tilt')
        
    def display_syringe(self):
        return self.compile_cmd(command = 'display_syringe')

    def set_syringe(self,**kwargs):
        if 'volume' in kwargs: 
            if 'volume_unit' not in kwargs:
                raise KeyError('Need to define the volume units!')
            self.compile_cmd(command = 'set_syringe_volume', parameter1 = kwargs.get('volume'))
        if 'diameter' in kwargs:
            self.compile_cmd(command = 'set_syringe_diameter', parameter1 = kwargs.get('diameter'))

    def set_target_volume(self,target,unit):
        self.compile_cmd(command = 'set_target_volume', parameter1 = target, parameter2 = unit)

    def set_rate(self,rate,unit):
        response = self.compile_cmd(command = 'set_rate', parameter1 = rate, parameter2 = unit)
        if response == b'\nArgument error: 20\r\n   Out of range\r\n:':
            return('Rate out of range!')
    
    def set_target_time(self,time):
        self.compile_cmd(command = 'set_time', parameter1 = time)

    def dispense(self,volume,**kwargs):
        if 'unit' in kwargs:
            self.unit=kwargs.get('unit')
        self.set_target_volume(volume, unit = self.unit)
        if 'rate' in kwargs:
            self.set_rate(kwargs.get('rate'))
        if 'target_time' in kwargs:
            self.set_target_time(kwargs.get('target_time'))
        self.set_run_mode()

    