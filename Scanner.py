import asyncio #allows asynchronous running
from bleak import BleakScanner #bluetooth low energy (BLE) scanner
import tkinter as tk

#window creation
#root = tk.Tk()
#root.title("BLE Location Tracker")
#root.geometry("800x600")
#tk.Label(root, text="blah blah blah").pack()
#root.mainloop()

#MAC addresses of my BLE beacons and given name
wanted_devices = {"48:87:2D:9D:55:81": "Alpha",
                  "48:87:2D:9D:55:9E": "Beta",
                  "48:87:2D:9D:55:CC": "Charlie",
                  "48:87:2D:9D:55:99": "Delta",
                  "48:87:2D:9D:55:A0": "Echo"
                  
                  }

#smoothing factor for calculating EMA, lower is smoother + less responsive, higher is more responsive + less smooth
smooth_factor = 0.1
#each beacon's average rssi value
alpha_rssi_avg = 0.1
beta_rssi_avg = 0.1
charlie_rssi_avg = 0.1
delta_rssi_avg = 0.1
echo_rssi_avg = 0.1

#called whenever a BLE packet is received
def processBLEpacket(device, advertisement_data):
    global alpha_rssi_avg
    global beta_rssi_avg
    global charlie_rssi_avg
    global delta_rssi_avg
    global echo_rssi_avg

    #prints name and RSSI of my BLE beacons only
    if device.address in wanted_devices:
        #get given name and rssi value
        name = wanted_devices[device.address]
        rssi = advertisement_data.rssi

        #exponential moving averages (EMA)
        if name == 'Alpha':
            if alpha_rssi_avg is None:
                alpha_rssi_avg = rssi
            else:
                alpha_rssi_avg = smooth_factor * rssi + (1 - smooth_factor) * alpha_rssi_avg
            print(f"{name} - RSSI: {alpha_rssi_avg:.1f}")

        elif name == 'Beta':
            if beta_rssi_avg is None:
                beta_rssi_avg = rssi
            else:
                beta_rssi_avg = smooth_factor * rssi + (1 - smooth_factor) * beta_rssi_avg
            print(f"{name} - RSSI: {beta_rssi_avg:.1f}")

        elif name == 'Charlie':
            if charlie_rssi_avg is None:
                charlie_rssi_avg = rssi
            else:
                charlie_rssi_avg = smooth_factor * rssi + (1 - smooth_factor) * charlie_rssi_avg
            print(f"{name} - RSSI: {charlie_rssi_avg:.1f}")

        elif name == 'Delta':
            if delta_rssi_avg is None:
                delta_rssi_avg = rssi
            else:
                delta_rssi_avg = smooth_factor * rssi + (1 - smooth_factor) * delta_rssi_avg
            print(f"{name} - RSSI: {delta_rssi_avg:.1f}")

        elif name == 'Echo':
            if echo_rssi_avg is None:
                echo_rssi_avg = rssi
            else:
                echo_rssi_avg = smooth_factor * rssi + (1 - smooth_factor) * echo_rssi_avg
            print(f"{name} - RSSI: {echo_rssi_avg:.1f}")

async def main():
    #create scanner object
    #whenever a BLE signal is received call processBLEpacket
    scanner = BleakScanner(processBLEpacket)
    await scanner.start()
    #continuously scan
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
