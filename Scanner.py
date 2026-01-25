import asyncio #allows asynchronous running
from bleak import BleakScanner #bluetooth low energy (BLE) scanner
import tkinter as tk #gui
import threading
from PIL import Image, ImageTk

#width and height variables of room
room_width = None
room_height = None

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

def calibrate_button_pressed():
    global room_width, room_height

    try:
        #get values inputted into form fields
        room_width = float(width_entry.get())
        room_height = float(height_entry.get())
    except ValueError:
        #catch invalid inputs
        print("Invalid inputs")
        return
    print(room_width, "x", room_height)
    #call function to show the calibration page
    show_calibration_page()

def show_calibration_page():
    #get rid of previous frames and title
    WidthHeight_frame.pack_forget()
    image_frame.pack_forget()
    #put calibration page into window
    calibration_page.pack(fill="both", expand=True)

def start_ble_loop():
    asyncio.run(main())

#---------------------------------------------GUI---------------------------------------------#

#window creation
root = tk.Tk()
root.title("BLE Location Tracker")
root.geometry("800x600")
page_title = tk.Label(root, text="BLE Location Tracker", font=("Arial", 16, "bold"), pady=20).pack()
#width and height inputs frame 
WidthHeight_frame = tk.Frame(root)
WidthHeight_frame.pack(pady=20)

#width and height inputs
width_label = tk.Label(WidthHeight_frame, text="Width")
width_label.grid(row=0, column=0, padx=10, pady=5)

width_entry = tk.Entry(WidthHeight_frame)
width_entry.grid(row=0, column=1, padx=10, pady=5)

height_label = tk.Label(WidthHeight_frame, text="Height")
height_label.grid(row=1, column=0, padx=10, pady=5)

height_entry = tk.Entry(WidthHeight_frame)
height_entry.grid(row=1, column=1, padx=10, pady=5)

#calibrate button
calibrate_button = tk.Button(WidthHeight_frame, text="Calibrate", activebackground="grey", width="8", height="1", bd="2", command=calibrate_button_pressed)
calibrate_button.grid(row=1, column=3, padx=10, pady=5)

#image frame
image_frame = tk.Frame(root)
image_frame.pack(pady=20)

#image
img = Image.open("C:/Users/joryl/Downloads/widthHeightDiss.png")
img = img.resize((450, 300))
img_tk = ImageTk.PhotoImage(img)
image_label = tk.Label(image_frame, image=img_tk)
image_label.image = img_tk
image_label.pack()

"""#button frame
button_frame = tk.Frame(root)
button_frame.pack(expand=True)
#buttons
CreateNewMap_button = tk.Button(button_frame, text="Create new map", activebackground="grey", width="20", height="2", bd="3")
CreateNewMap_button.pack(pady=0)
LoadStoredMap_button = tk.Button(button_frame, text="Load stored map", activebackground="grey", width="20", height="2", bd="3")
LoadStoredMap_button.pack(pady=15)"""

#calibration page
calibration_page = tk.Frame(root)
tk.Label(calibration_page, text="Calibration", font=("Arial", 12, "normal"), pady=20).pack()

threading.Thread(target=start_ble_loop, daemon=True).start()
root.mainloop()