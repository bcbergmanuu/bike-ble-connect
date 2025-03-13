import asyncio
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
import logging
import logging


logger = logging.getLogger(__name__)
CSC_Measurement_UUID =  "00002A5B-0000-1000-8000-00805f9b34fb" 
BATTERY_LEVEL_UUID =    "00002A19-0000-1000-8000-00805f9b34fb"


class uutrack_reader:
    
    def __init__(self):
        self.CSC = 0
        self.semaphore = asyncio.Semaphore(0)
        
    def decode_csc_measurement(self, data_bin : bytearray):
        flags = data_bin[0]
        crank_revolution_present = flags & 0b10
        last_crank_event_time_present = flags & 0b10

        crank_revolution = None
        last_crank_event_time = None
        
        if crank_revolution_present:
            crank_revolution = int.from_bytes(data_bin[1:3], byteorder='little')
            
        if last_crank_event_time_present:
            last_crank_event_time = int.from_bytes(data_bin[4:6], byteorder='little')
        
        return crank_revolution, last_crank_event_time
    
    async def notification_handler(self, sender, data : bytearray):        
        crank_revolution, last_crank_event_time = self.decode_csc_measurement(data)
        print(f"Crank Revolutions: {crank_revolution}")
        #print(f"Last Crank Event Time: {last_crank_event_time}")
        #print(f"rawdata: {data.hex()}")
        

    def on_disconnect(self, client):
        print("ble disconnect detected")
        self.semaphore.release()
              
    async def makeconnectiontodevice(self, device):
        client = BleakClient(device.address, timeout=30, disconnected_callback=self.on_disconnect)
        
        try:
            await client.connect()
            print("connected to device")
            battery_level_byte = await client.read_gatt_char(BATTERY_LEVEL_UUID)
            
            print(f'battery level {int.from_bytes(battery_level_byte, byteorder="little")}')
            await client.start_notify(CSC_Measurement_UUID, self.notification_handler)
            await self.semaphore.acquire()
                
        except Exception as e:
            print(e)
        finally:
            await client.disconnect()
            print(f'disconnected ')
    

class datacollector:
    async def app(self):
        while(1):
            print("scanning devices")
            devices = await BleakScanner.discover(timeout=20)
            for d in devices:
                if(d.name == "deskbike9198"):                            
                    print(f'device found:{d}')                
                    the_reader = uutrack_reader()
                    await the_reader.makeconnectiontodevice(d)
                
                    

def main(): 
    collectior = datacollector()
    asyncio.run(collectior.app())

if __name__ == "__main__":
    main()
