import asyncio
from bleak import BleakScanner

async def main():
    #scans for all devices emitting bluetooth signals
    devices = await BleakScanner.discover()
    for device in devices:
        print(device)

asyncio.run(main())
