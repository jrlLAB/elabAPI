from .main import instrument
import time

class SY08(instrument):

    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, **kwargs)

        self.model = 'SY08'
        self.type = 'pump'
        self.address = 0x00
        self.total_volume = 5 #define total volume, for our model it is 5 mL
        self.current_position = 0 #setting a fake starting position

        if 'address' in kwargs:
            self.address = kwargs.get('address')

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')
        

    def compile_cmd(self, command, **kwargs):
        ##define useful command codes
        command_dict = {'query_address' : 0x20, 'query_subdivision' : 0x25,
                    'query_max_speed' : 0x27, 'query_version' : 0x3F,
                    'query_motor_status' : 0x4A, 'query_position' : 0x66,
                    'set_speed' : 0x4B, 'aspirate' : 0x4D,
                    'discharge' : 0x42,'set_position' : 0x4E, 
                    'reset' : 0x45, 'forced_reset' : 0x4F, 
                    'strong_stop' : 0x49, 'device_reset' : 0xAA}
        command_hex = command_dict[command]
        #use kwargs to define if you want to print the command hex for troubleshoot
        if 'show_cmd' in kwargs:
            self.show_cmd = kwargs.get('show_cmd')
        ##use kwargs to define parameter1
        if 'parameter1' in kwargs:
            parameter1 = kwargs.get('parameter1')
        else:
            parameter1 = 0x00
        ##use kwargs to define parameter2
        if 'parameter2' in kwargs:
            parameter2 = kwargs.get('parameter2')
        else:
            parameter2 = 0x00
        # compile: B0 frame header, B1 address byte, B2 command byte, B3 parameter byte 1, B4 parameter byte 2, B5 end of frame, B6 checksum MSB, B7 checksum LSB
        packet = bytearray([0xCC,self.address,command_hex,parameter1,parameter2,0xDD])
        #Make sure checksum is little end, here the bytearray goes: [Least significant bit, Most significant bit]
        checksum = bytearray([(sum(packet) & 0xFF), (sum(packet) >> 8)])
        packet.extend(checksum)
        self.ser.write(packet)
        self.response = self.ser.read(8)
        if self.response == '':
            self.response = self.ser.read(8)
        if self.verbose == True:
            print('command SY08: ',packet.hex())
            print('response SY08:',self.response.hex())
        return self.response
        
       
    def check_movement(self):
        # some bloat here that could be cut down, but a faster check movement script
        packet = bytearray([0xCC,self.address,0x4A,0x00,0x00,0xDD])
        checksum = bytearray([(sum(packet) & 0xFF), (sum(packet) >> 8)])
        packet.extend(checksum)
        self.ser.write(packet)
        movement_status = self.ser.read(8)
        while movement_status[2] != 0x00:
            self.ser.write(packet)
            movement_status = self.ser.read(8)
        return self.response


    def query_position(self):
        # some bloat here that could be cut down, but a faster check movement script
        packet = bytearray([0xCC,self.address,0x66,0x00,0x00,0xDD])
        checksum = bytearray([(sum(packet) & 0xFF), (sum(packet) >> 8)])
        packet.extend(checksum)
        self.ser.write(packet)
        query_result = self.ser.read(8)
        while query_result == '':
            query_result = self.ser.read(8)
        position = (query_result[4]<<8)|(query_result[4])
        if self.verbose == True:
            print(f'query hex: {query_result.hex()}, position: {position}')
        return position
    

    def set_speed(self, speed):
        if speed in range(601):
            if self.verbose == True:
                print(f'Speed set to {speed/600*800:.1f} rpm!')
            self.compile_cmd(command='set_speed', parameter1=speed.to_bytes(2,'little')[0], parameter2 = speed.to_bytes(2,'little')[1])
        else:
            raise ValueError("Speed is too fast!")
        

    def move_to_position(self, position, **kwargs):
        #check kwargs for speed first, adjust if desired
        if 'speed' in kwargs:
            speed = kwargs.get('speed')
            self.set_speed(speed)
        #move to position
        if position in range(12001):
            if self.verbose == True:
                print(f'Moving syringe to step {position} out of 12000!')
            self.compile_cmd(command='set_position', parameter1=position.to_bytes(2,'little')[0], parameter2 = position.to_bytes(2,'little')[1])
            self.check_movement()   
        else:
            raise ValueError("Beyond stroke limits!")
        

    def full_reset(self):
        self.compile_cmd(command = 'forced_reset')
        self.check_movement()


    def reset(self):
        self.compile_cmd(command = 'reset')
        self.check_movement()
    

    def reset_no_check(self):
        self.compile_cmd(command = 'reset')


    def aspirate(self, volume, **kwargs):
        #check kwargs for speed first, adjust if desired
        if 'speed' in kwargs:
            speed = kwargs.get('speed')
            self.set_speed(speed)
        #query current position
        self.current_position = self.query_position()
        #convert from mL to steps
        steps_to_move = int(volume*(12000/5))
        #aspirate
        if (steps_to_move + self.current_position) in range(12001):
            self.compile_cmd(command='aspirate', parameter1=steps_to_move.to_bytes(2,'little')[0], parameter2 = steps_to_move.to_bytes(2,'little')[1])
            self.check_movement()
            self.current_position = self.query_position()
            time.sleep(volume+0.5)
        else:
            #driver will not move if command is beyond limits so no need to raise Value error
            raise ValueError("Beyond stroke limits!")


    def discharge(self, volume, **kwargs):
        #check kwargs for speed, adjust if desired
        if 'speed' in kwargs:
            speed = kwargs.get('speed')
            self.set_speed(speed)
        #query current position
        self.current_position = self.query_position()
        #allow for string 'all' to dispense everything in syringe
        if volume == 'all':
            self.reset()
            self.check_movement()
            self.current_position = self.query_position()
        #if not string 'all' then dispense whatever volume was input
        else:
            #dispense time!
            steps_to_move = int(volume*(12000/5))
            if (self.current_position - steps_to_move) in range(12001):
                self.compile_cmd(command='discharge', parameter1=steps_to_move.to_bytes(2,'little')[0], parameter2 = steps_to_move.to_bytes(2,'little')[1])
                self.check_movement()
                self.current_position = self.query_position()
            elif (self.current_position - steps_to_move) < 0:
                self.reset()
                self.current_position = self.query_position()
        time.sleep(0.5)
                
    
