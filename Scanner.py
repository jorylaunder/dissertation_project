import asyncio #allows asynchronous running
from bleak import BleakScanner #bluetooth low energy (BLE) scanner

#MAC addresses of my BLE beacons and given name
wanted_devices = {"48:87:2D:9D:55:81": "Beacon Alpha"
                  #more to add
                  }

#called whenever a BLE packet is received
def processBLEpacket(device, advertisement_data):
    #prints name and RSSI of my BLE beacons only
    if device.address in wanted_devices:
        name = wanted_devices[device.address]
        print(f"{name} - RSSI: {advertisement_data.rssi}")

async def main():
    #create scanner object
    #whenever a BLE signal is received call detection_callback
    scanner = BleakScanner(processBLEpacket)
    await scanner.start()
    #continuously scan
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
