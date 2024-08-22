'''
This class implements serial communication with the Runze multichannel syringe pump, model SY-01B, using ASCII commands assuming DT protocol.
'''
from .main import instrument
import time
import re

class SY01B(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, **kwargs)

        self.model = 'SY01B'
        self.type = 'pumpvalve'
        self.address = '1'
        self.total_volume = 500 #define total volume, for our model it is 500 uL
        self.current_position = 0 #setting a fake starting position
        self.ports = 9
        self.mode = 0 #store motor mode
        self.position_range = 12001 
        self.unit = 'uL'

        if 'address' in kwargs:
            self.address = kwargs.get('address')

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')
        

    def compile_cmd(self, command, **kwargs):
        ## Define user input variables with kwargs
        parameter1 = kwargs.get('parameter1', '')  ##If not found, default parameter = ''

        ## Define useful command codes
        command_dict = {
            'set_mode' : f'N{parameter1}R',              ## 0,1,2 = Normal, fine and microstep mode
            'set_backlash_increments':f'K{parameter1}R', ## 0-1600, helps compensate for mechanical play to ensure correct position for dispensing
            'init_pump' : 'N2Z1R',                       ## Initializes pump-valve to be in microstep mode, backlash of 3200, at half force, default speed. Sets valve to change in CW manner.
            'set_port' : f'I{parameter1}R',              ## Sets valve position to port [parameter1]
            'set_position' : f'A{parameter1}R',          ## Sets absolute plunger position, 0-96000 for microstep mode, 0-12000 in standard mode
            'relative_pickup' : f'P{parameter1}R',       ## Moves plunger down specified number of increments
            'relative_dispense' : f'D{parameter1}R',     ## Moves plunger up specified number of increments
            'set_acceleration' : f'L{parameter1}R',      ## Sets speed ramp of plunger, [parameter1] * 2500 pulses/sec^2, 1-20, default=14
            'set_start_speed' : f'v{parameter1}R',       ## Sets start speed of plunger in pulses/sec, 1-1000, default=900, must be less than top speed, will ramp up to start speed
            'set_top_speed' : f'V{parameter1}R',         ## Set top speed of plunger, 1-6000, default=4000
            'set_speed' : f'V{parameter1}R',             ## Use top speed to set speed, if top speed is lower than start and cutoff speed, auto sets speed to this
            'set_preset_speed' : f'S{parameter1}R',      ## A list of 41 preset speed modes, 0-40, 40 being the slowest and 0 being the fastest
            'set_cutoff_speed' : f'c{parameter1}R',      ## Speed at which the plunger ends its movement, 1-1500 in microstep, default = 900, only valid during dispense
                                                         ## start speed <= cutoff speed <= top speed, speed values are in half-steps or microsteps/second (each pulse is one half/microstep)
            'repeat' : 'XR',                             ## The device repeats the last executed command
            'repeat_sequence' : f'G{parameter1}R',       ## Repeat the last executed command n number of times, n = 0-48000
            'delay' : f'M{parameter1}R',                 ## Delay execution of a command in milliseconds rounded to nearest multiple of 5. Allows for liquid to stop oscillating in syringe
            'stop' : 'HR',                               ## Halts execution of string command
            'strong_stop' : 'TR',                        ## Terminates plunger movement, reinitialization is recommended
            'reset' : 'A0R',                              ## Reset pump to position 0
            'origin_reset' : 'A0A150R',

            ## Report commands below, do not require R exection commands
            'query_position' : '?',             ## Reports absolute position of plunger in microsteps
            'query_start_speed' : '?1',         ## Report start speed in pulses/sec
            'query_top_speed' : '?2',
            'query_cutoff_speed' : '?3',
            'query_actual_position' : '?4',     ##Reports plunger encoder position
            'query_valve' : '?6',
            'query_command_status' : '?10',     ## Returns 0 if buffer empty, 1 if not
            'query_backlash_increments' : '?12',
            'query_input_1_status' : '?13',     ## Returns 0 or 1, 0 = low, 1 = high
            'query_input_2_status' : '?14',     ## ^
            'query_movement' : '?16',           ## Returns number of plunger moves
            'query_valve_movement' : '?17',     ## Returns number of valve movements
            'query_acceleration' : '?25',
            'query_mode' : '?28',               ## Reports mode set by N (0,1,2 = normal, fine, microstep)
            'query_device_status' : '?29',      ## Reports device status (error code)
            'query_status' : 'Q',               ## Reports error codes and pump status, bits 0-3 = error code, bit 5 = status bit, 0 = busy, 1 = not
            'query_version' : '#',
            'query_max_speed' : '?2'}               


        ## Use kwargs to define if you want to print the command hex for troubleshoot
        if 'show_cmd' in kwargs:
            self.show_cmd = kwargs.get('show_cmd')

        ## Compile and send command, read out instrument response
        packet = self.build_packet(command_dict[command])
        self.response = self.write_read(packet)
        if self.response == b'':
            time.sleep(0.3)
            self.response = self.ser.read_all()
        if self.verbose == True:
            print('command SY01B: ',packet)
            print('response SY01B:',self.response)

        ## Always run error check, only print there was no error if verbose ==True, otherwise only print if there is a fundamental error

        return self.response
    
    def check_error(self,response):  ## Need to test this out
        ## Error checking

        #Need to parse the response string, identify where the error bytes are going to end up
        split_res = response.decode().strip().split('/')
        print(split_res)
        error_byte = split_res[2].split('`')
        print(error_byte)
        #Then strip and split the string after decoding it, then place the error bit into the error dictionary and return the response
        error_dict = {0:'Error free',
                      1:'Initialization Error. Pump failed to initialize. Check for blockages or loose connections. Clear by successfully initializing the pump',
                      2:'Invalid command',
                      3:'Invalid operand. Check the input command parameter',
                      6:'EEPROM failure. Call Runze technical services',
                      7:'Device not initialized. Initialize the pump',
                      8:'Internal failure. Call Runze technical services',
                      9:'Plunger overlaod. Excessive backpressure, reinitialize the pump',
                      10:'Valve overload. Excess backpressure or blockage. Reinitialize the pump or send another valve command. Continual valve errors indicate that the valve should be replaced.',
                      11:'Plunger move not allowed. Vavle is in bypass or throughput psotion',
                      12:'Internal failure. Call technical services',
                      14:'A/D converter failure. Internal A/D converter is fault. Call technical services',
                      15:'Command overflow. Pump is either currently in action or has unexecuted commands in its buffer.'}
        
        ## Evalute response for error
        try:
            error_dict[error_byte]
            return error_dict[error_byte]
        except KeyError:
            print('No error key found')
            return
        
    def build_packet(self,command_ascii,**kwargs): ##
        parameter1,parameter2 = [kwargs.get(param,'') for param in ('parameter1','parameter2')]
        ## Required packet for DT protocol is: start command ('/'), pump address, data block (length n), carriage return ('\r')
        packet = f'/{self.address}{command_ascii}{parameter1}{parameter2}\r'.encode()  #Some commands require an input variable as well as a 'R' character before \r to execute properly
        return packet

    def write_read(self,packet): ##
        self.ser.write(packet)
        response = self.ser.read_all()
        if response == b'':
            time.sleep(0.1)
            response = self.ser.read_all()
        return response
    
    def init_pump(self): ##
        return self.compile_cmd('init_pump')
    
    def set_mode(self,mode): ##
        if mode in range(3):
            self.compile_cmd('set_mode',parameter1=str(mode))
            if mode == 0:
                self.position_range = 12001
            if mode == 1 or mode == 2:
                self.position_range = 96001
            self.mode=mode
        else:
            raise ValueError('Mode must be 0, 1, or 2: denoting normal, fine, or micropositioning modes')
        
    def decode_response(self,response):
        cleaned_response = re.sub(r'[^\x20-\x7E]','',response.decode('latin-1').strip()) #Get rid of all non convertable hex, decode the byte array, strip the response
        return cleaned_response
        
    def check_movement(self):  
        packet = self.build_packet('Q')
        movement_status = self.write_read(packet)
        response = self.decode_response(movement_status)
        while not response.startswith('/0`'):
            response = self.decode_response(self.write_read(packet))
        return
    
    def stop(self):
        self.compile_cmd('stop')
        return 
    
    def query_position(self):  ## Query plunger position
        query_result = self.compile_cmd('query_position')
        while query_result == '':
            query_result = self.ser.read_all() 
        position = int(self.decode_response(query_result).split('`')[1])  
        if self.verbose == True:
            print(f'query: {query_result}, position: {position}')
        return position
    
    def reset(self): ##
        self.compile_cmd('reset')
        self.check_movement()
        time.sleep(1)

    def full_reset(self):  ##
        self.compile_cmd('init_pump')

    def origin_reset(self): ##
        self.compile_cmd('origin_reset')

    def port(self, port): ##
        if port not in range(1,(self.ports+1)):
            raise ValueError(f"Selected port must be between 1 and {self.ports+1}")       
        if self.verbose == True:
            print(f'Moving to port {port}!')
        self.compile_cmd(command='set_port', parameter1=port)
        self.check_movement()
        time.sleep(1)
    

    def set_speed(self, speed): ##
        if speed in range(12001):
            if self.verbose == True:
                rate = self.total_volume/96000*speed*60
                print(f'Speed set to {speed} steps/sec! Flow rate is {rate} uL/min')
            self.compile_cmd(command='set_speed', parameter1=speed)
        else:
            raise ValueError("Speed is too fast!")

    def set_rate(self, rate): ##
        if rate in range(3751):
            speed = int(rate/60*96000/self.total_volume)
            if self.verbose == True:
                print(f'Flow rate set to {rate:.2f} {self.unit}/min. Speed set to {speed} microsteps/sec')
            self.set_speed(speed)
        else:
            raise ValueError("Flow rate is too fast!")
        

    def move_to_position(self, position, **kwargs): ##
        #check kwargs for speed first, adjust if desired
        if 'speed' in kwargs:
            speed = kwargs.get('speed')
            self.set_speed(speed)
        #move to position based on instrument mode
        if position in range(self.position_range):
            if self.verbose == True:
                print(f'Moving syringe to step {position} out of {self.position_range-1}!')
            self.compile_cmd(command='set_position', parameter1=position)
            self.check_movement()   
        else:
            raise ValueError("Beyond stroke limits!")
        

    def reset_no_check(self): ##
        self.compile_cmd(command = 'reset')


    def aspirate(self, volume, **kwargs): #This is to pull liquid into the syringe
        #check movement to ensure pump is free
        self.check_movement()
        #check kwargs for speed, adjust if desired
        if 'speed' in kwargs:
            speed = kwargs.get('speed')
            self.set_speed(speed)
        if self.verbose == True:
            print(f'Aspirating {volume}')
        #query current position
        self.current_position = self.query_position()
        #convert from uL to steps
        steps_to_move = int(volume*((self.position_range-1)/self.total_volume))
        #aspirate
        if (steps_to_move + self.current_position) in range(self.position_range):
            self.compile_cmd(command='relative_pickup', parameter1=steps_to_move)
            self.check_movement()
            self.current_position = self.query_position()
            time.sleep(volume/1000+0.5)
        else:
            #driver will not move if command is beyond limits so no need to raise Value error
            raise ValueError("Beyond stroke limits!")


    def discharge(self, volume, **kwargs): #This is to push liquid out of the syringe
        #check movement to ensure pump is free
        self.check_movement()
        #check kwargs for speed, adjust if desired
        if 'speed' in kwargs:
            speed = kwargs.get('speed')
            self.set_speed(speed)
        #query current position
        self.current_position = self.query_position()
        #allow for string 'all' to dispense everything in syringe
        if volume == 'all':
            self.compile_cmd('set_position',parameter1=0)
            self.check_movement()
            self.current_position = self.query_position()
        #if not string 'all' then dispense whatever volume was input
        else:
            #dispense time!
            steps_to_move = int(volume*((self.position_range-1)/self.total_volume))
            if (self.current_position - steps_to_move) in range(self.position_range):
                self.compile_cmd(command='relative_dispense', parameter1=steps_to_move)
                self.check_movement()
                self.current_position = self.query_position()
            elif (self.current_position - steps_to_move) < 0:
                self.compile_cmd(command='set_position',parameter1=0)
                self.check_movement()
                self.current_position = self.query_position()
        time.sleep(0.5)

def set_total_volume(self,vol):
    if type(vol) == int:
        self.total_volume = vol
    else:
        raise TypeError('Volume must be an integer')