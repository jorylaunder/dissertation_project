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
max_point = 16
samples_per_point = 50
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
    14: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    15: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
    16: {"Alpha": [], "Beta": [], "Charlie": [], "Delta": []},
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
            counter.config(text=f"Samples collected: {count}/200")

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
                    time.sleep(2)
                    show_map_page()

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
def cal_page_button_pressed():
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
    #get rid of previous frames 
    WidthHeight_frame.pack_forget()
    image_frame.pack_forget()
    #put calibration page into window
    calibration_page.pack(fill="both", expand=True)

def show_map_page():
    #get rid of previous frames
    calibration_page.pack_forget()
    calibration_buttons_frame.pack_forget()
    #show map page
    map_page.pack(fill="both", expand=True)
    #draw map
    draw_map()

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
    counter.config(text="Samples collected: 0/200")
    status.config(text="")

    collecting = True


#----------------------------------------------------------------------------END OF CALIBRATION--------------------------------------------------------------------------------#

#----------------------------------------------------------------------------MAP-----------------------------------------------------------------------------------------------#

def draw_map():

    #add padding 
    padding = 20
    usable_width = map_width - 2 * padding
    usable_height = map_height - 2 * padding

    #get scale room
    scale = min(usable_width / room_width, usable_height / room_height)

    draw_width = room_width * scale
    draw_height = room_height * scale

    #centre map in canvas, leftover space from grid
    x0 = (map_width - draw_width) / 2    #left edge
    y0 = (map_height - draw_height) / 2   #top edge
    x1 = x0 + draw_width   #right edge
    y1 = y0 + draw_height    #bottom edfe

    #draw map outline
    map.create_rectangle(x0, y0, x1, y1, width=2)

    #draw 4x4 grid
    cell_width = draw_width / 4  #width of a column or cell
    cell_height = draw_height / 4  #height of a row or cell

    #map.create_line(x_start, y_start, x_end, y_end)
    #vertical grid lines
    map.create_line(x0 + cell_width, y0, x0 + cell_width, y1)
    map.create_line(x0 + 2 * cell_width, y0, x0 + 2 * cell_width, y1)
    map.create_line(x0 + 3 * cell_width, y0, x0 + 3 * cell_width, y1)

    #horizontal grid lines
    map.create_line(x0, y0 + cell_height, x1, y0 + cell_height)
    map.create_line(x0, y0 + 2 * cell_height, x1, y0 + 2 * cell_height)
    map.create_line(x0, y0 + 3 * cell_height, x1, y0 + 3 * cell_height)

    #add beacons into corners
    label_offset = 10  #prevernt overlapping
    map.create_text(x0 + label_offset, y0 + label_offset, text="A", anchor="nw", font=("Arial", 12, "bold"), fill="blue")
    map.create_text(x1 - label_offset, y0 + label_offset, text="B", anchor="ne", font=("Arial", 12, "bold"), fill="blue")
    map.create_text(x0 + label_offset, y1 - label_offset, text="C", anchor="sw", font=("Arial", 12, "bold"), fill="blue")
    map.create_text(x1 - label_offset, y1 - label_offset, text="D", anchor="se", font=("Arial", 12, "bold"), fill="blue")
#----------------------------------------------------------------------------END OF MAP----------------------------------------------------------------------------------------#

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
calibrate_button = tk.Button(WidthHeight_frame, text="Calibrate", activebackground="grey", width="8", height="1", bd="2", command=cal_page_button_pressed)
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

#calibration page
calibration_page = tk.Frame(root)
calibration_page_title = tk.Label(calibration_page, text="Calibration", font=("Arial", 12, "normal"), pady=20)
calibration_page_title.pack()
#calibration image
calibration_image = Image.open("C:/Users/joryl/Downloads/updated_calibration_example_image.png")
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
counter = tk.Label(calibration_buttons_frame, text="Samples collected: 0/200", font=("Arial", 10))
counter.grid(row=1, column=0, padx=5, pady=5)
status = tk.Label(calibration_buttons_frame, text="", font=("Arial", 10))
status.grid(row=2, column=0, pady=5)

#map page
map_page = tk.Frame(root)
map_page_title = tk.Label(map_page, text="Map", font=("Arial", 12, "normal"), pady=20)
map_page_title.pack()

#canvas dimensions for map
map_width = 450
map_height = 450
#map
map = tk.Canvas(map_page, width=map_width, height=map_height, bg="white")
map.pack(pady=10)

#test button DELETE
test_button = tk.Button(calibration_buttons_frame, text="Skip", activebackground="grey", width="6", height="1", bd="2", command=show_map_page)
test_button.grid(row=1, column=1, padx=5, pady=5)

#----------------------------------------------------------------------------END OF GUI----------------------------------------------------------------------------------------#
threading.Thread(target=start_ble_loop, daemon=True).start()
root.mainloop()