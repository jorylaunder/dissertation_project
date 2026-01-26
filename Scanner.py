import asyncio #allows asynchronous running
from bleak import BleakScanner #bluetooth low energy (BLE) scanner
import tkinter as tk #gui
import threading #running of gui and scanning
from PIL import Image, ImageTk #images in gui
import time

#width and height variables of room
room_width = None
room_height = None

#calibration variables
current_point = 1
max_point = 13
samples_per_point = 25
collecting = False

#calibration points dictionary
calibration_data = {
    1: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    2: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    3: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    4: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    5: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    6: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    7: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    8: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    9: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    10: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    11: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    12: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    13: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
}

#MAC addresses of my BLE beacons and given name
wanted_devices = {"48:87:2D:9D:55:81": "Alpha",
                  "48:87:2D:9D:55:9E": "Beta",
                  "48:87:2D:9D:55:CC": "Charlie",
                  "48:87:2D:9D:55:99": "Delta",
                  "48:87:2D:9D:55:A0": "Echo" #spare beacon for now
                  
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

    global collecting
    global current_point

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

#----------------------------------------------------------------------------FINGER PRINTING-----------------------------------------------------------------------------------#
        #only get the name beacons we want
        if (collecting == True) and name in calibration_data[current_point]:

            #get raw rssi values rather than EMA until full
            if len(calibration_data[current_point][name]) < samples_per_point:
                calibration_data[current_point][name].append(rssi)

            #get count for progress
            count = sum(len(calibration_data[current_point][i]) for i in ["Alpha", "Beta", "Charlie", "Delta"])
            #update gui
            counter.config(text=f"Samples collected: {count}/100")

            #check to see if each name at that current point is full
            all_done = True
            for i in ["Alpha", "Beta", "Charlie", "Delta"]:
                sample_count = len(calibration_data[current_point][i])
                if sample_count < samples_per_point:
                    all_done = False
                    break
            
            #increment current_point amd print confirmation
            if all_done == True:
                collecting = False
                status.config(text=f"Finished point {current_point}")

                current_point = current_point + 1

                time.sleep(2)

                if current_point > max_point:
                    status.config(text=f"Calibration complete")

                else:
                    status.config(text=f"move to point {current_point} and press start")

#----------------------------------------------------------------------------END OF FINGER PRINTING----------------------------------------------------------------------------#

#----------------------------------------------------------------------------MAIN----------------------------------------------------------------------------------------------#

async def main():
    #create scanner object
    #whenever a BLE signal is received call processBLEpacket
    scanner = BleakScanner(processBLEpacket)
    await scanner.start()
    #continuously scan
    while True:
        await asyncio.sleep(1)

def start_ble_loop():
    asyncio.run(main())

#----------------------------------------------------------------------------END OF MAIN---------------------------------------------------------------------------------------#

#----------------------------------------------------------------------------CHANGING PAGES------------------------------------------------------------------------------------#

#calibration button pressed on first page
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

#----------------------------------------------------------------------------END OF CHANGING PAGES-----------------------------------------------------------------------------#

#----------------------------------------------------------------------------CALIBRATION---------------------------------------------------------------------------------------#

#when start button is pressed on calibration page
def cal_start_button_pressed():
    global collecting, current_point

    if current_point > max_point:
        status.config(text="calibration already complete")
        return
    
    #clear current point if it happens to have any in it
    for i in ["Alpha", "Beta", "Charlie", "Delta"]:
        calibration_data[current_point][i].clear()

    # reset calibration status labels
    counter.config(text="Samples collected: 0/100")
    status.config(text="")

    collecting = True


#----------------------------------------------------------------------------END OF CALIBRATION--------------------------------------------------------------------------------#


#----------------------------------------------------------------------------GUI-----------------------------------------------------------------------------------------------#

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
calibration_page_title = tk.Label(calibration_page, text="Calibration", font=("Arial", 12, "normal"), pady=20)
calibration_page_title.pack()
#calibration image
calibration_image = Image.open("C:/Users/joryl/Downloads/calibration image.png")
calibration_image = calibration_image.resize((280, 200))
calibration_image_tk = ImageTk.PhotoImage(calibration_image)
calibration_image_label = tk.Label(calibration_page, image=calibration_image_tk)
calibration_image_label.image = calibration_image_tk
calibration_image_label.pack()
#calibration buttons frame
calibration_buttons_frame = tk.Frame(calibration_page)
calibration_buttons_frame.pack()
#calibration start button
cal_start_button = tk.Button(calibration_buttons_frame, text="Start", activebackground="grey", width="6", height="1", bd="2", command=cal_start_button_pressed)
cal_start_button.grid(row=0, column=0, padx=5, pady=5)
#calibration progress text
counter = tk.Label(calibration_buttons_frame, text="Samples collected: 0/100", font=("Arial", 10))
counter.grid(row=1, column=0, padx=5, pady=5)
status = tk.Label(calibration_buttons_frame, text="", font=("Arial", 10))
status.grid(row=2, column=0, pady=5)

"""cal_button_2 = tk.Button(calibration_buttons_frame, text="2", activebackground="grey", width="3", height="1", bd="2")
cal_button_2.grid(row=0, column=1, padx=5, pady=5)
cal_button_3 = tk.Button(calibration_buttons_frame, text="3", activebackground="grey", width="3", height="1", bd="2")
cal_button_3.grid(row=0, column=2, padx=5, pady=5)
cal_button_4 = tk.Button(calibration_buttons_frame, text="4", activebackground="grey", width="3", height="1", bd="2")
cal_button_4.grid(row=0, column=3, padx=5, pady=5)
cal_button_5 = tk.Button(calibration_buttons_frame, text="5", activebackground="grey", width="3", height="1", bd="2")
cal_button_5.grid(row=0, column=4, padx=5, pady=5)
cal_button_6 = tk.Button(calibration_buttons_frame, text="6", activebackground="grey", width="3", height="1", bd="2")
cal_button_6.grid(row=0, column=5, padx=5, pady=5)
cal_button_7 = tk.Button(calibration_buttons_frame, text="7", activebackground="grey", width="3", height="1", bd="2")
cal_button_7.grid(row=0, column=6, padx=5, pady=5)
cal_button_8 = tk.Button(calibration_buttons_frame, text="8", activebackground="grey", width="3", height="1", bd="2")
cal_button_8.grid(row=0, column=7, padx=5, pady=5)
cal_button_9 = tk.Button(calibration_buttons_frame, text="9", activebackground="grey", width="3", height="1", bd="2")
cal_button_9.grid(row=0, column=8, padx=5, pady=5)
cal_button_10 = tk.Button(calibration_buttons_frame, text="10", activebackground="grey", width="3", height="1", bd="2")
cal_button_10.grid(row=0, column=9, padx=5, pady=5)
cal_button_11 = tk.Button(calibration_buttons_frame, text="11", activebackground="grey", width="3", height="1", bd="2")
cal_button_11.grid(row=0, column=10, padx=5, pady=5)
cal_button_12 = tk.Button(calibration_buttons_frame, text="12", activebackground="grey", width="3", height="1", bd="2")
cal_button_12.grid(row=0, column=12, padx=5, pady=5)
cal_button_13 = tk.Button(calibration_buttons_frame, text="13", activebackground="grey", width="3", height="1", bd="2")
cal_button_13.grid(row=0, column=13, padx=5, pady=5)"""

#----------------------------------------------------------------------------END OF GUI----------------------------------------------------------------------------------------#
threading.Thread(target=start_ble_loop, daemon=True).start()
root.mainloop()