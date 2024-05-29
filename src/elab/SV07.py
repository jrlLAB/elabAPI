from .main import instrument
import time

class SV07(instrument):
    '''
    '''
    def __init__(self, com_port, **kwargs):
        super().__init__(com_port, **kwargs)

        self.model = 'SV07'
        self.type = 'valve'
        self.address = 0x00
        self.ports = 16
        if 'address' in kwargs:
            self.address = kwargs.get('address')

        if self.verbose == True:
            print(f'{self.model} connected on {com_port} at {self.baud_rate} bits/s')
            
    def compile_cmd(self, command, **kwargs):

        ##define possible command codes
        command_dict = {'query_address' : 0x20, 'query_position' : 0x3E,
                    'query_version' : 0x3F, 'change_port' : 0x44, 
                    'reset' : 0x45, 'origin_reset' : 0x4F, 'strong_stop' : 0x49}
        command_hex = command_dict[command]

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
            print('command SV07: ',packet.hex())
            print('response SV07:',self.response.hex())
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
    
    def reset(self):
        self.compile_cmd('reset')
        self.check_movement()
        time.sleep(1)

    def origin_reset(self):
        self.compile_cmd('origin_reset')
        self.check_movement()
        time.sleep(1)

    def port(self, port):
        if port in range(1,(self.ports+1)):
            if self.verbose == True:
                print(f'Moving to port {port}!')
            self.compile_cmd(command='change_port', parameter1=port)
            self.check_movement()
            time.sleep(1)
        else:
            raise ValueError(f"Selected port must be between 1 and {self.ports+1}")       
