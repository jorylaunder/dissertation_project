import asyncio #allows asynchronous running
from bleak import BleakScanner #bluetooth low energy (BLE) scanner
import statistics #for median

#MAC addresses of my BLE beacons and given name
wanted_devices = {"48:87:2D:9D:55:81": "Alpha"
                  #more to add
                  }

Alpha_avg = None
smooth_factor = 0.1

#called whenever a BLE packet is received
def processBLEpacket(device, advertisement_data):
    global Alpha_avg
    #prints name and RSSI of my BLE beacons only
    if device.address in wanted_devices:
        #get name and rssi value
        name = wanted_devices[device.address]
        rssi = advertisement_data.rssi

        #exponential moving average (EMA)
        if name == 'Alpha':
            if Alpha_avg is None:
                Alpha_avg = rssi
            else:
                Alpha_avg = smooth_factor * rssi + (1 - smooth_factor) * Alpha_avg
            print(f"{name} - RSSI: {Alpha_avg:.1f}")
        #elif beta etc...

async def main():
    #create scanner object
    #whenever a BLE signal is received call processBLEpacket
    scanner = BleakScanner(processBLEpacket)
    await scanner.start()
    #continuously scan
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
