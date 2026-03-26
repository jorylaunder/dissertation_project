import asyncio #allows asynchronous running
from bleak import BleakScanner #bluetooth low energy (BLE) scanner
import tkinter as tk #gui
import threading #running of gui and scanning
from PIL import Image, ImageTk #images in gui
import time
import math #for distance calc
import json #for saving a map
from tkinter import filedialog 
from scipy.optimize import least_squares # for least squares function
from scipy.stats import wasserstein_distance # for fingerprint matching

#width and height variables of room
room_width = None
room_height = None

#keeping track if user is in edit mode
edit_mode = False

#sets for obstacle edges and obstacle cells
obstacle_edges = set()
obstacle_cells = set()

#for shortest path
current_cell = None
selected_cell = None
#to avoid spikes saying you've arrived in path finding
arrived_threshold = 3
arrived_counter = 0

#calibration variables
current_point = 1
max_point = 16
samples_per_point = 50
collecting = False

#rssi to distance models
models = None

#top left x and y of map and dimensions of map
x0 = None
y0 = None
draw_width = None
draw_height = None

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

#point coordinates using a 4x4 grid where we snake left to right top to bottom, coords are (row, col)
point_coordinates = {
    1: (0, 0),
    2: (0, 1),
    3: (0, 2),
    4: (0, 3),
    5: (1, 3),
    6: (1, 2),
    7: (1, 1),
    8: (1, 0),
    9: (2, 0),
    10: (2, 1),
    11: (2, 2),
    12: (2, 3),
    13: (3, 3),
    14: (3, 2),
    15: (3, 1),
    16: (3, 0)
}

#dictionary for calculating the distance at each point to each beacon given the room width and height
point_to_beacon_distances = {
    1: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    2: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    3: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    4: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    5: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    6: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    7: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    8: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    9: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    10: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    11: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    12: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    13: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    14: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    15: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
    16: {"Alpha": 0, "Beta": 0, "Charlie": 0, "Delta": 0},
}

#dictionary for neighbouring cells to each cell
neighbouring_cells = {
    1: [2, 7, 8],
    2: [1, 3, 6, 7, 8],
    3: [2, 4, 5, 6, 7],
    4: [3, 5, 6],
    5: [3, 4, 6, 11, 12],
    6: [2, 3, 4, 5, 7, 10, 11, 12],
    7: [1, 2, 3, 6, 8, 9, 10, 11],
    8: [1, 2, 7, 9, 10],
    9: [7, 8, 10, 15, 16],
    10: [6, 7, 8, 9, 11, 14, 15, 16],
    11: [5, 6, 7, 10, 12, 13, 14, 15],
    12: [5, 6, 11, 13, 14],
    13: [11, 12, 14],
    14: [10, 11, 12, 13, 15],
    15: [9, 10, 11, 14, 16],
    16: [9, 10, 15]
}

#dictionary of neighbours for path finding, no diagonals
neighbouring_cells_for_path = {
    1: [2, 8],
    2: [1, 3, 7],
    3: [2, 4, 6],
    4: [3, 5],
    5: [4, 6, 12],
    6: [3, 5, 7, 11],
    7: [2, 6, 8, 10],
    8: [1, 7, 9],
    9: [8, 10, 16],
    10: [7, 9, 11, 15],
    11: [6, 10, 12, 14],
    12: [5, 11, 13],
    13: [12, 14],
    14: [11, 13, 15],
    15: [10, 14, 16],
    16: [9, 15]
}

#MAC addresses of my BLE beacons and given names
wanted_devices = {"48:87:2D:9D:55:81": "Alpha",
                  "48:87:2D:9D:55:9E": "Beta",
                  "48:87:2D:9D:55:CC": "Charlie",
                  "48:87:2D:9D:55:99": "Delta",
                  "48:87:2D:9D:55:A0": "Echo" #spare beacon for now
                  
                  }

#live raw rsssi for fingerprint matching
fingerprint_rssi = {
    "Alpha": [],
    "Beta": [],
    "Charlie": [],
    "Delta": []
}
#window size
fingerprint_window = 25

#for trilateration, live window and distance smoothing
live_rssi = {
    "Alpha": [],
    "Beta": [],
    "Charlie": [],
    "Delta": []
}
distance_ema = {
    "Alpha": None,
    "Beta": None,
    "Charlie": None,
    "Delta": None
}
distance_smooth_factor = 0.3
#window size
trilateration_window = 11

#smoothing factor for calculating EMA, lower is smoother + less responsive, higher is more responsive + less smooth
smooth_factor = 0.2

#each beacon's average rssi value
alpha_rssi_avg = None
beta_rssi_avg = None
charlie_rssi_avg = None
delta_rssi_avg = None
echo_rssi_avg = None

#called whenever a BLE packet is received, fills up rssi windows and then calls fingerprint matching or trilateration, and then fuses the guesses
def processBLEpacket(device, advertisement_data):
    global alpha_rssi_avg
    global beta_rssi_avg
    global charlie_rssi_avg
    global delta_rssi_avg
    global echo_rssi_avg

    global collecting
    global current_point

    global models

    global live_rssi

    global current_cell

    fingerprint_cell = None
    distances = {}
    trilateration_x = trilateration_y = None
    fingerprint_x = fingerprint_y = None
    tri_row = None
    tri_column = None
    trilateration_cell = None


    #prints name and RSSI of my BLE beacons only
    if device.address in wanted_devices:

        #get given name and rssi value
        name = wanted_devices[device.address]
        rssi = advertisement_data.rssi

        #store sliding window of live raw rssi values for trilateration
        if name in live_rssi:
            live_rssi[name].append(rssi)
            if len(live_rssi[name]) > trilateration_window:
                live_rssi[name].pop(0)

        #same but for fingerprinting
        if name in fingerprint_rssi:
            fingerprint_rssi[name].append(rssi)
            if len(fingerprint_rssi[name]) > fingerprint_window:
                fingerprint_rssi[name].pop(0)

        #exponential moving averages (EMA), just used for testing to show beacons are still working
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

        #calibrating a room
        if (collecting == True) and name in calibration_data[current_point]:

            #get raw rssi values until full
            if len(calibration_data[current_point][name]) < samples_per_point:
                calibration_data[current_point][name].append(rssi)

            #get count for progress tracking
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
                    models = rssi_to_distance_model()

                else:
                    status.config(text=f"move to point {current_point} and press start")

        if models is not None and not collecting:
            #fingerprint matching
            fingerprint_cell = fingerprint_matching()
            if fingerprint_cell is not None:
                print("fingerprint guess: ", fingerprint_cell)
                

            #trilateration
            #translate rssi values into distances
            distances = rssi_to_distance_calculation(models)
            #once we have all 4 beacons then trilaterate
            if len(distances) == 4:
                trilateration_x, trilateration_y, trilateration_cost = trilateration(distances)
                cell_width = room_width / 4
                cell_height = room_height / 4

                # get trilateration cell
                #column
                if 0 <= trilateration_x < cell_width:
                    tri_column = 0
                elif cell_width <= trilateration_x < 2 * cell_width:
                    tri_column = 1
                elif 2 * cell_width <= trilateration_x < 3 * cell_width:
                    tri_column = 2
                elif 3 * cell_width <= trilateration_x < 4 * cell_width:
                    tri_column = 3
                else:
                    tri_column = None

                # row
                if 0 <= trilateration_y < cell_height:
                    tri_row = 0
                elif cell_height <= trilateration_y < 2 * cell_height:
                    tri_row = 1
                elif 2 * cell_height <= trilateration_y < 3 * cell_height:
                    tri_row = 2
                elif 3 * cell_height <= trilateration_y < 4 * cell_height:
                    tri_row = 3
                else:
                    tri_row = None

            trilateration_cell = None
            if tri_row is not None and tri_column is not None:
                #draw_dot_on_map(trilateration_x, trilateration_y)
                for cell, (row, col) in point_coordinates.items():
                    if row == tri_row and col == tri_column:
                        trilateration_cell = cell
                        break
            
            #for testing
            if trilateration_cell is not None:
                print("trilateration guess:", trilateration_cell)
                
            #fusion of fingerprint matching and trilateration
            if fingerprint_cell is not None and trilateration_cell is not None and len(distances) == 4:
                if trilateration_cell == fingerprint_cell:
                    #draw dot on map at this cell
                    draw_dot_on_map(trilateration_x, trilateration_y)
                else:
                    #get neighbouring cells of trilateration cell from dictionary
                    #these cells and the trilateration cells become the candidate cells, min and max
                    candidate_cells = neighbouring_cells[trilateration_cell] + [trilateration_cell]
                    if fingerprint_cell in candidate_cells:
                        #convert fingerprint cell into x y
                        row = point_coordinates[fingerprint_cell][0]
                        column = point_coordinates[fingerprint_cell][1]
                        cell_width = room_width / 4
                        cell_height = room_height / 4
                        fingerprint_x = (column + 0.5) * cell_width
                        fingerprint_y = (row + 0.5) * cell_height
                        #get average x y from fingerporint x y and trilateration x, y (use weights), based on trilateration cost
                        if trilateration_cost < 8:
                            trilateration_weight = 0.95
                            fingerprint_weight = 0.05
                        else:
                            trilateration_weight = 0.7
                            fingerprint_weight = 0.3
                        x = (fingerprint_weight * fingerprint_x) + (trilateration_weight * trilateration_x)
                        y = (fingerprint_weight * fingerprint_y) + (trilateration_weight * trilateration_y)

                        draw_dot_on_map(x, y)

                    #else run fingerprint on only candidate cells
                    else:
                        new_fingerprint_cell = fingerprint_matching(candidate_cells)
                        print("new fingerprint guess: ", new_fingerprint_cell)
                        if new_fingerprint_cell == trilateration_cell:
                            draw_dot_on_map(trilateration_x, trilateration_y)
                        else:
                            #convert fingerprint cell into x y
                            row = point_coordinates[new_fingerprint_cell][0]
                            column = point_coordinates[new_fingerprint_cell][1]
                            cell_width = room_width / 4
                            cell_height = room_height / 4
                            fingerprint_x = (column + 0.5) * cell_width
                            fingerprint_y = (row + 0.5) * cell_height
                            #get average x y from fingerporint x y and trilateration x, y (use weights), based on tri cost
                            if trilateration_cost < 8:
                                trilateration_weight = 0.95
                                fingerprint_weight = 0.05
                            else:
                                trilateration_weight = 0.7
                                fingerprint_weight = 0.3
                            x = (fingerprint_weight * fingerprint_x) + (trilateration_weight * trilateration_x)
                            y = (fingerprint_weight * fingerprint_y) + (trilateration_weight * trilateration_y)

                            draw_dot_on_map(x, y)
                    
                return

#----------------------------------------------------------------------------FINGER PRINTING-----------------------------------------------------------------------------------#

#match live rssi to recorded rssi for each cell
def fingerprint_matching(candidate_cells=None):
    #for every cell in the room, compare live window to entire calibration distribution
    most_likely_cell = None
    smallest_error = float("inf")

    if candidate_cells is None:
        cells_to_check = range(1,17)
    else:
        cells_to_check = candidate_cells

    for cell in cells_to_check:
        error_sum = 0
        beacons_used = 0

        for beacon in ["Alpha", "Beta", "Charlie", "Delta"]:
            live_values = live_rssi[beacon]
            fingerprint_values = calibration_data[cell][beacon]

            #if empty continue
            if not live_values or not fingerprint_values:
                continue
            
            #using mean
            #get live average and calibration data average of each beacon
            #live_average = sum(live_values) / len(live_values)
            #fingerprint_average = sum(fingerprint_values) / len(fingerprint_values)

            #using median
            #live_sorted = sorted(live_values)
            #fingerprint_sorted = sorted(fingerprint_values)
            #live_average = live_sorted[len(live_sorted) // 2]
            #fingerprint_average = fingerprint_sorted[len(fingerprint_sorted) // 2]
            #error = (live_average - fingerprint_average)

            #using full distribution
            error = wasserstein_distance(live_values, fingerprint_values)

            #square errors to make big differences bigger
            error_sum += error * error
            beacons_used += 1

        if beacons_used >= 3:
            average_error = error_sum / beacons_used

            if average_error < smallest_error:
                smallest_error = average_error
                most_likely_cell = cell

    return most_likely_cell

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
    #call function to show the calibration page and calculate distances from each point to each beacon
    calculate_distances(room_width, room_height)
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

#when save button is pressed
def save_map_button_pressed():
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetype=[("JSON files", "*.json")])

    if filename:
        save_map(filename)

#when load map button is pressed
def load_map_button_pressed():
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

    if filename:
        load_map(filename)
        show_calibration_page()
        show_map_page()
        draw_map()

#for toggling edit mode on and off
def edit_map_button_pressed():
    global edit_mode
    #if clicked turn it to the opposite
    edit_mode = not edit_mode
    if edit_mode:
        edit_map_button.config(text="Finish editing")
        #change function called when map clicked
        map.bind("<Button-1>", on_map_click_edit)
        map.bind("<Double-Button-1>", on_map_double_click_edit)
    else:
        edit_map_button.config(text="Edit map")
        map.bind("<Button-1>", on_map_click)
        map.unbind("<Double-Button-1>")

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

#calculating the point to beacon distances
def calculate_distances(room_width, room_height):

    #beacon positions, a top left, b top right, c bottom left, d bottom right
    beacon_coordinates = {
            "Alpha": (0.0, 0.0),
            "Beta": (room_width, 0.0),
            "Charlie": (0.0, room_height),
            "Delta": (room_width, room_height)
        }

    actual_cell_width = room_width / 4
    actual_cell_height = room_height / 4

    for point in range (1,17):
        #get coordinates of each point 
        row = point_coordinates[point][0]
        column = point_coordinates[point][1]
        #calculate centre of each square i.e. the point
        x_centre = (column + 0.5) * actual_cell_width
        y_centre = (row + 0.5) * actual_cell_height

        #get coordinates of each beacon
        for beacon in beacon_coordinates:
            beacon_x = beacon_coordinates[beacon][0]
            beacon_y = beacon_coordinates[beacon][1]

            #calculate point to beacon distances using pythagorean theorem
            point_to_beacon_distances[point][beacon] = math.sqrt((x_centre - beacon_x)**2 + (y_centre - beacon_y)**2)

        #printing for testing purposes
        print("\npoint to beacon distances:")
        for point, distances in point_to_beacon_distances.items():
            print(f"point {point}: {distances}")

        
#log distance path loss model
def rssi_to_distance_model():
        
        #model for each beacon
        global models
        models = {}

        beacons = ["Alpha", "Beta", "Charlie", "Delta"]

        for beacon in beacons:
            log_distances = []
            average_rssi = []

            #get all my calibration data
            for point in range(1,17):
                distance = point_to_beacon_distances[point][beacon]
                rssi_samples = calibration_data[point][beacon]

                #now use all samples
                for rssi in rssi_samples:
                    log_distances.append(math.log10(distance))
                    average_rssi.append(rssi)
                
            #linear regression 
            # y = Mx + C
            # RSSI = M*log10(distance) + C
            #number of calibration points for this beacon, i.e. 16
            n = len(log_distances)

            #plotting a graph where x is log distance and y is rssi
            #get averages of these
            x_mean = sum(log_distances) / n
            y_mean = sum(average_rssi) / n

            #for the gradient M
            numerator = 0
            denominator = 0

            for i in range(n):
                #essentially how far is the log distance from the x mean and how far is the rssi from the y mean, i.e. x deviation * y deviation
                numerator = numerator + (log_distances[i] - x_mean) * (average_rssi[i] - y_mean)
                #keeps the spread of x values 
                denominator = denominator + (log_distances[i] - x_mean) ** 2

            #gradient M
            distance_to_rssi_relationship = numerator / denominator

            #intercept C = y - Mx
            distance_spread = y_mean - distance_to_rssi_relationship * x_mean

            #store model for beacon
            models[beacon] = (distance_spread, distance_to_rssi_relationship)

        for beacon, (c, m) in models.items():
            print(f"{beacon}: C={c:.2f}  M={m:.2f}")       
        return models
        

#----------------------------------------------------------------------------END OF CALIBRATION--------------------------------------------------------------------------------#

#----------------------------------------------------------------------------MAP-----------------------------------------------------------------------------------------------#

def draw_map():

    global x0, y0, draw_height, draw_width

    #prevent drawing over any existing maps
    map.delete("all")

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

    cell_draw_width = draw_width / 4
    cell_draw_height = draw_height / 4

    #draw obstacle cells
    for cell in obstacle_cells:
        row, col = point_coordinates[cell]
        cell_x0 = x0 + col * cell_draw_width
        cell_y0 = y0 + row * cell_draw_height
        map.create_rectangle(cell_x0, cell_y0, cell_x0 + cell_draw_width, cell_y0 + cell_draw_height,
                             fill="#404040", outline="")

    #map.create_line(x_start, y_start, x_end, y_end)
    #vertical grid lines
    map.create_line(x0 + cell_width, y0, x0 + cell_width, y1)
    map.create_line(x0 + 2 * cell_width, y0, x0 + 2 * cell_width, y1)
    map.create_line(x0 + 3 * cell_width, y0, x0 + 3 * cell_width, y1)

    #horizontal grid lines
    map.create_line(x0, y0 + cell_height, x1, y0 + cell_height)
    map.create_line(x0, y0 + 2 * cell_height, x1, y0 + 2 * cell_height)
    map.create_line(x0, y0 + 3 * cell_height, x1, y0 + 3 * cell_height)

    #draw obstacle edges
    for edge in obstacle_edges:
        cells = list(edge)
        r1, c1 = cells[0]
        r2, c2 = cells[1]
        #if same row then it is a vertical edge between two cells
        if r1 == r2:
            col = max(c1, c2)
            edge_x = x0 + col * cell_draw_width
            edge_y_start = y0 + r1 * cell_draw_height
            edge_y_end = y0 + (r1 + 1) * cell_draw_height
            map.create_line(edge_x, edge_y_start, edge_x, edge_y_end, width=4, fill="#404040")
        #if same col then it is a horizontal edge between two cels
        else:
            row = max(r1, r2)
            edge_y = y0 + row * cell_draw_height
            edge_x_start = x0 + min(c1, c2) * cell_draw_width
            edge_x_end = x0 + (min(c1, c2) + 1) * cell_draw_width
            map.create_line(edge_x_start, edge_y, edge_x_end, edge_y, width=4, fill="#404040")

    #add beacons into corners
    label_offset = 10  #prevernt overlapping
    map.create_text(x0 + label_offset, y0 + label_offset, text="A", anchor="nw", font=("Arial", 12, "bold"), fill="blue")
    map.create_text(x1 - label_offset, y0 + label_offset, text="B", anchor="ne", font=("Arial", 12, "bold"), fill="blue")
    map.create_text(x0 + label_offset, y1 - label_offset, text="C", anchor="sw", font=("Arial", 12, "bold"), fill="blue")
    map.create_text(x1 - label_offset, y1 - label_offset, text="D", anchor="se", font=("Arial", 12, "bold"), fill="blue")

    #change click depending on edit mode
    if edit_mode:
        map.bind("<Button-1>", on_map_click_edit)
        map.bind("<Double-Button-1>", on_map_double_click_edit)
    else:
        map.bind("<Button-1>", on_map_click)

    #function to save map
def save_map(filename):

    #turn into lists of lists
    edges = [list([list(cell) for cell in edge]) for edge in obstacle_edges]
    #turn into list
    cells = list(obstacle_cells)

    data = {"room_width": room_width,
            "room_height": room_height,
            "calibration_data": calibration_data,
            "obstacle_edges": edges,
            "obstacle_cells": cells
            }
        
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Map saved to {filename}")

#function to load a saved map
def load_map(filename):
    global room_width, room_height, calibration_data, models, current_point, collecting, obstacle_edges, obstacle_cells

    #prevent calibration from runnning again
    current_point = max_point + 1
    collecting = False

    with open(filename, "r") as f:
        data = json.load(f)

    room_width = float(data["room_width"])
    room_height = float(data["room_height"])

    #rebuild the dictionary from json string
    calibration_data = {
        int(point): data["calibration_data"][point]
        for point in data["calibration_data"]
    }

    #obstacle edges
    obstacle_edges = set()
    for edge in data.get("obstacle_edges", []):
        #turn back into frozenset
        obstacle_edges.add(frozenset([tuple(cell) for cell in edge]))

    #obstacle cells
    obstacle_cells = set(data.get("obstacle_cells", []))

    #calculate all the calibration data again
    calculate_distances(room_width, room_height)
    models = rssi_to_distance_model()

    print(f"Map loaded from {filename}")

    return models

#draws dot in cell based of off position from trilateration function
def draw_dot_on_map(x_estimate, y_estimate):

    global room_width, room_height, dot_column, dot_row, current_cell, selected_cell, arrived_threshold, arrived_counter

    cell_width = room_width / 4
    cell_height = room_height / 4

    #get column its in
    if x_estimate >= 0 and x_estimate < cell_width:
        dot_column = 0
    elif x_estimate >= cell_width and x_estimate < (2*cell_width):
        dot_column = 1
    elif x_estimate >= (2*cell_width) and x_estimate < (3*cell_width):
        dot_column = 2
    elif x_estimate >= (3*cell_width) and x_estimate < (4*cell_width):
        dot_column = 3

    #get row its in
    if y_estimate >= 0 and y_estimate < cell_height:
        dot_row = 0
    elif y_estimate >= cell_height and y_estimate < (2*cell_height):
        dot_row = 1
    elif y_estimate >= (2*cell_height) and y_estimate < (3*cell_height):
        dot_row = 2
    elif y_estimate >= (3*cell_height) and y_estimate < (4*cell_height):
        dot_row = 3

    if dot_column != None and dot_row != None:

        cell_draw_width = draw_width / 4
        cell_draw_height = draw_height / 4

        #get centre of cell dot should be in
        centre_x = x0 + (dot_column + 0.5) * cell_draw_width
        centre_y = y0 + (dot_row + 0.5) * cell_draw_height

        radius = 5

        map.delete("position_dot")

        map.create_oval(
            centre_x - radius,
            centre_y - radius, 
            centre_x + radius,
            centre_y + radius,
            fill = "red",
            outline = "",
            tags = "position_dot"
        )

        #update current cell
        for cell, (row, col) in point_coordinates.items():
            if row == dot_row and col == dot_column:
                current_cell = cell
                break
        
        #skip of obstacle cell
        if current_cell in obstacle_cells:
            return
        
        #once arrived unselect cell and show message
        #make sure we have been there for the trheshold to avoid spikes 
        if current_cell == selected_cell and selected_cell is not None:
            arrived_counter += 1
            if arrived_counter >= arrived_threshold:
                selected_cell = None
                arrived_counter = 0
                map.create_text(map_width / 2, 20, text="You have arrived!", 
                                font=("Arial", 12, "bold"), fill="green", tags="arrived_text")
                root.after(5000, lambda: map.delete("arrived_text"))
        else:
            #reset counter if we leave the cell before reaching threshold
            arrived_counter = 0

        draw_shortest_path()

#when a cell is clicked
def on_map_click(event):
    global selected_cell
    
    cell_draw_width = draw_width / 4
    cell_draw_height = draw_height / 4

    #check map exists and click is inside it
    if None in (x0, y0, draw_width, draw_height) or not (x0 <= event.x <= x0 + draw_width and y0 <= event.y <= y0 + draw_height):
        return
    
    #figure out where the click was
    col = int((event.x - x0) / cell_draw_width)
    row = int((event.y - y0) / cell_draw_height)
    col = max(0, min(col, 3))
    row = max(0, min(row, 3))

    #get cell number
    clicked_cell = None
    for cell, (r, c) in point_coordinates.items():
        if r == row and c == col:
            clicked_cell = cell
            break

    #deselect or select
    if clicked_cell == selected_cell:
        selected_cell = None
    elif clicked_cell not in obstacle_cells:
        selected_cell = clicked_cell

    print("Cell clicked: ", clicked_cell)
    draw_shortest_path()

#breadth first search for shortest path
def bfs_shortest_path(start, end):
    #if cell we're in is the end cell return
    if start == end:
        return [start]
        
    #store cells weve visited
    visited = {start}
    #store potential paths
    paths = [[start]]

    while paths:
        #get path from paths
        path = paths.pop(0)
        #get the last cell in the path
        current = path[-1]
        current_row, current_col = point_coordinates[current]

        for neighbour in neighbouring_cells_for_path[current]:
            #skip obstacle cells
            if neighbour in obstacle_cells:
                continue

            #skip if obstacle edge between current cell and this neighbour
            neighbour_row, neighbour_col = point_coordinates[neighbour]
            edge = frozenset({(current_row, current_col), (neighbour_row, neighbour_col)})
            if edge in obstacle_edges:
                continue
            #if the neighbour is the end then we have our path
            if neighbour == end:
                return path + [neighbour]
            #if not add it to visited and path and carry on
            if neighbour not in visited:
                visited.add(neighbour)
                paths.append(path + [neighbour])

    #catch if not path found for some reason
    return None
    
def draw_shortest_path():
    

    #remove previous path
    map.delete("path")
    
    cell_draw_width = draw_width / 4
    cell_draw_height = draw_height / 4

    #highlight destination cell
    if selected_cell is not None:
        row = point_coordinates[selected_cell][0]
        column = point_coordinates[selected_cell][1]
        #get boundaries of cell
        centre_x = x0 + (column + 0.5) * cell_draw_width
        centre_y = y0 + (row + 0.5) * cell_draw_height
        radius = 5
        map.create_oval(centre_x - radius, centre_y - radius, centre_x + radius, centre_y + radius,
                        fill="green", outline="", tags="path")

    #draw path
    if current_cell is not None and selected_cell is not None and current_cell != selected_cell:
        #get path
        path = bfs_shortest_path(current_cell, selected_cell)

        if path:
            #highlight each cell in path
            for cell in path:
                #skip if current cell or destination
                if cell == current_cell or cell == selected_cell:
                    continue
                row = point_coordinates[cell][0]
                column = point_coordinates[cell][1]
                #get boundaries of cell
                centre_x = x0 + (column + 0.5) * cell_draw_width
                centre_y = y0 + (row + 0.5) * cell_draw_height
                radius = 4
                map.create_oval(centre_x - radius, centre_y - radius, centre_x + radius, centre_y + radius,
      
                                fill="lightgreen", outline="", tags="path")
                
#when edit mode is on and map is clicked
def on_map_click_edit(event):
    global obstacle_edges

    cell_draw_width = draw_width / 4
    cell_draw_height = draw_height / 4

    #if click outside map
    if not (x0 <= event.x <= x0 + draw_width and y0 <= event.y <= y0 + draw_height):
        return

    #distance at which clicks snap to an edge
    snap_distance = 20

    closest_edge = None
    closest_distance = float("inf")

    #looping through every cell
    for row in range(4):
        for col in range(4):
            #check vertical edge to right of each cell, except last one
            if col + 1 < 4:
                #x coord
                edge_x = x0 + (col + 1) * cell_draw_width
                #y coords
                edge_y_start = y0 + row * cell_draw_height
                edge_y_end = y0 + (row + 1) * cell_draw_height
                #check if click was in this vertical span
                if edge_y_start <= event.y <= edge_y_end:
                    #horizontal distance from click to edge
                    distance = abs(event.x - edge_x)
                    #if its the closest edge then keep it
                    if distance < closest_distance:
                        closest_distance = distance
                        #store in frozenset as the two cells (row, col) edge seperates
                        closest_edge = frozenset({(row, col), (row, col + 1)})

            #check horizontal edge below all cells except bottom
            if row + 1 < 4:
                #y coord
                edge_y = y0 + (row + 1) * cell_draw_height
                #x coords
                edge_x_start = x0 + col * cell_draw_width
                edge_x_end = x0 + (col + 1) * cell_draw_width
                #check if click was in this vertical span
                if edge_x_start <= event.x <= edge_x_end:
                    #vertical distance from click to edge
                    distance = abs(event.y - edge_y)
                    #if its the closest edge then keep it
                    if distance < closest_distance:
                        closest_distance = distance
                        #store in frozenset as the two cells (row, col) edge seperates
                        closest_edge = frozenset({(row, col), (row + 1, col)})

    #edge found
    if closest_edge is not None and closest_distance <= snap_distance:
        #if obstacle then remove
        if closest_edge in obstacle_edges:
            obstacle_edges.remove(closest_edge) 
        #otherwise add
        else:
            obstacle_edges.add(closest_edge)

        #redraw map and path with changes
        draw_map()
        draw_shortest_path()

#double click for creating an obstacle cell
def on_map_double_click_edit(event):
    global obstacle_cells

    cell_draw_width = draw_width / 4
    cell_draw_height = draw_height / 4

    #prevent click being outside map
    if not (x0 <= event.x <= x0 + draw_width and y0 <= event.y <= y0 + draw_height):
        return

    #get row and col
    col = int((event.x - x0) / cell_draw_width)
    row = int((event.y - y0) / cell_draw_height)
    col = max(0, min(col, 3))
    row = max(0, min(row, 3))

    clicked_cell = None
    for cell, (r, c) in point_coordinates.items():
        if r == row and c == col:
            clicked_cell = cell
            break

    if clicked_cell in obstacle_cells:
        obstacle_cells.remove(clicked_cell)
    else:
        obstacle_cells.add(clicked_cell)

    draw_map()
    draw_shortest_path()
#----------------------------------------------------------------------------END OF MAP----------------------------------------------------------------------------------------#

#----------------------------------------------------------------------------TRILATERATION-------------------------------------------------------------------------------------#

#use models and rearrange equation to get distance
def rssi_to_distance_calculation(models):

    global distance_ema

    distances = {}

    #set max distance using actual max distance and tolerance
    tolerance = 1.2
    max_distance = math.sqrt(room_height**2 + room_width**2) * tolerance

    for beacon in ["Alpha", "Beta", "Charlie", "Delta"]:
        rssi_samples = live_rssi[beacon]

        if not rssi_samples or beacon not in models:
            continue

        # get model parameters
        distance_spread = models[beacon][0]
        distance_to_rssi_relationship = models[beacon][1]

        # convert each rssi to distance
        distance_samples = []
        for rssi in rssi_samples:
            distance = 10 ** ((rssi - distance_spread) / distance_to_rssi_relationship)
            distance_samples.append(distance)

        #get median distance
        distance_samples.sort()
        median_distance = distance_samples[len(distance_samples)//2]

        if median_distance > max_distance:
            median_distance = max_distance

        #put EMA smoothing on distance
        if distance_ema[beacon] is None:
            distance_ema[beacon] = median_distance
        else: 
            distance_ema[beacon] = (distance_smooth_factor * median_distance + (1 - distance_smooth_factor) * distance_ema[beacon])
        
        distances[beacon] = distance_ema[beacon]

    return distances

#actual trilateration function
def trilateration(distances):
    #once we have the estimated distance from each beacon, this becomes the radius of a circle we draw around each beacon
    dA = distances["Alpha"]
    dB = distances["Beta"]
    dC = distances["Charlie"]
    dD = distances["Delta"]
    print("dA:", dA)
    print("dB:", dB)
    print("dC:", dC)
    print("dD:", dD)
    #the point at which these intersect is our estimated area
    #where dA is radius of A circle etc

    # Alpha: (x)^2 + (y)^2 = dA^2

    # Beta: (x - width)^2 + (y)^2 = dB^2

    # Charlie: (x)^2 + (y - height)^2 = dC^2

    # Delta: (x - width)^2 + (y - height)^2 = dD^2

    # we want to get x and y
    # so expand every equation

    # Alpha: x^2 + y^2 = dA^2

    # Beta: x^2 - 2x(width) + width^2 + y^2 = dB^2

    # Charlie: x^2 + y^2 - 2y(height) + height^2 = dC^2

    # Delta: x^2 - 2x(width) + width^2 +y^2 - 2y(height) + height^2 = dD^2

    # now solve for x and y by combining equations to get rid of x^2 and y^2
    # and then reaarange for x or y respectively, we would get x1, y1 and x2, y2 

    # equation 1 (Beta - Alpha): -2x(width) + width^2 = dB^2 - dA^2
    # equation 1: 
    x1 = (dA**2 - dB**2 + room_width**2) / (2*room_width)

    # equation 2 (Charlie - Alpha): -2y(hieght) + height^2 = dC^2 - dA^2
    # equation 2: 
    y1 = (dA**2 - dC**2 + room_height**2) / (2*room_height)

    # equation 3 (Delta - Alpha): -2x(width) -2y(height) + width^2 + height^2 - dD^2 - dA^2
    # equation 3: 
    x2 = (dA**2 - dD**2 + room_width**2 + room_height**2 - (2*y1*room_width)) / (2*room_width)
    y2 = (dA**2 - dD**2 + room_width**2 + room_height**2 - (2*x1*room_height)) / (2*room_height)

    #now that we have x1, x2 and y1, y2 we average these to find an x and y
    x = (x1 + x2) / 2
    y = (y1 + y2) / 2

    #clamp x and y in room
    x = max(0.0, min(x, room_width))
    y = max(0.0, min(y, room_height))

    # this becomes our initial guess for least squares function
    position = [x,y]

    #calculates difference between the guessed position and measured distance from each beacon
    def distance_errors(position):

        #weights added in as further beacons become more noisy, so add more weight to closer beacons
        weight_power = 0.25

        wA = 1 / (dA**weight_power + 0.1)
        wB = 1 / (dB**weight_power + 0.1)
        wC = 1 / (dC**weight_power + 0.1)
        wD = 1 / (dD**weight_power + 0.1)

        return [
            (math.sqrt((position[0] - 0)**2 + (position[1] - 0)**2) - dA) * wA,        
            (math.sqrt((position[0] - room_width)**2 + (position[1] - 0)**2) - dB) * wB,        
            (math.sqrt((position[0] - 0)**2 + (position[1] - room_height)**2) - dC) * wC,        
            (math.sqrt((position[0] - room_width)**2 + (position[1] - room_height)**2) - dD) * wD        
        ]

    #run least squares function, set minx miny and max x max y
    result = least_squares(distance_errors, position, bounds=([0.0, 0.0], [room_width, room_height]))

    #cost of least squares so how much error there was from each beacon
    tri_cost = result.cost
    print("cost: ", result.cost)

    #assign x and y estimates from returned object
    x_estimate = float(result.x[0])
    y_estimate = float(result.x[1])

    print("X:", x_estimate)
    print("Y:", y_estimate)

    return x_estimate, y_estimate, tri_cost

#----------------------------------------------------------------------------END OF TRILATERATION------------------------------------------------------------------------------#

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

#load map button
load_map_button = tk.Button(WidthHeight_frame, text="Load map", activebackground="grey", width="10", height="1", bd="2", command=load_map_button_pressed)
load_map_button.grid(row=3, column=1, padx=5, pady=5)

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

#save map button 
save_map_frame = tk.Frame(map_page)
save_map_frame.pack(pady=10)
save_map_button = tk.Button(save_map_frame, text="Save map", activebackground="grey", width="10", height="1", bd="2", command=save_map_button_pressed)
save_map_button.grid(row=0, column=0, padx=10)
#edit map button
edit_map_button = tk.Button(save_map_frame, text="Edit map", activebackground="grey", width="10", height="1", bd="2", command=edit_map_button_pressed)
edit_map_button.grid(row=0, column=1, padx=10)

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