# ================================
# Motion Detection & Alert System
# Raspberry Pi + Sense HAT + PiCamera2 + Telegram
# ================================

#import essential libraries
from sense_hat import SenseHat # For accelerometer, orientation, LED matrix, etc.
from time import sleep # library to enable delay which is the sleep function
from datetime import datetime #to enable time stamps
from picamera2 import Picamera2, Preview # camera library to activate camera
import requests # For sending HTTP requests (to Telegram API)
import schedule
import os
from telegram import Bot

#***INITIALIZATIONS***
sense = SenseHat()  # Create a Sense HAT object
camera = Picamera2() # Create a PiCamera2 object
sleep(2) # Give devices a moment to initialize

# Telegram bot credentials
BOT_TOKEN = "8388268362:AAG5XhOI5MP4hd4UsIxg434Q409uWiSjK3I"
CHAT_ID = "8388268362"

# Save the initial orientation of the device (baseline pitch, roll, yaw in degrees)
initial_orientation = sense.get_orientation()
initial_pitch = initial_orientation["pitch"]
initial_roll = initial_orientation["roll"]
initial_yaw = initial_orientation["yaw"]

# Save the initial accelerometer readings (baseline acceleration on x, y, z axes)
initial_acceleration = sense.get_accelerometer_raw()
initial_acceleration_x = initial_acceleration["x"]
initial_acceleration_y = initial_acceleration["y"]
initial_acceleration_z = initial_acceleration["z"]

# Messages to display based on device movement
msg1 = "DEVICE IS STILL"
msg2 = "DEVICE MOVED"

run_interval = 5

# Colors for LED blinking
red = [255, 0, 0]
white = [255, 255, 255]


#**DEFINE FUNCTIONS**
## The accel function takes number of iterations we want to average and interval
## of each sample as arguement and compares the new acceleration value with the new 
## average value and returns the difference in the 3 axis of acceleration

def accel(samples, delay):
    # creates empty list to store all the values of acceleration in the 3 different axis
    Reading_x = []
    Reading_y = []
    Reading_z = []
# iterates through to get the values of new acceleration with the interval as delay
    for sample in range(samples):
        new_acceleration = sense.get_accelerometer_raw()

        new_acceleration_x = new_acceleration["x"]
        new_acceleration_y = new_acceleration["y"]
        new_acceleration_z = new_acceleration["z"]

        Reading_x.append(new_acceleration_x)
        Reading_y.append(new_acceleration_y)
        Reading_z.append(new_acceleration_z)
        
        sleep(delay)
# sums the average of the iterated acceleration
    avg_acceleration_x = sum(Reading_x)/len(Reading_x)
    avg_acceleration_y = sum(Reading_y)/len(Reading_y)
    avg_acceleration_z = sum(Reading_z)/len(Reading_z)
# gets the absolute difference in new and old readings of acceleration 
# to keep all values positive
    change_in_acceleration_x = abs(initial_acceleration_x - avg_acceleration_x)
    change_in_acceleration_y = abs(initial_acceleration_y - avg_acceleration_y)
    change_in_acceleration_z = abs(initial_acceleration_z - avg_acceleration_z)
# returns change in acceleration
    return change_in_acceleration_x, change_in_acceleration_y, change_in_acceleration_z

#Reads the current orientation of the Sense HAT.
#Returns pitch, roll, and yaw (in degrees).

def orient():
    ot = sense.get_orientation()
    new_pitch = ot["pitch"]
    new_roll = ot["roll"]
    new_yaw = ot["yaw"]
    return new_pitch, new_roll, new_yaw


#Configures and starts the camera
#Captures a series of images with the PiCamera2, 
#saves them with timestamped filenames, and returns a list of filenames.

def camera_capture(number,interval):
    config = camera.create_preview_configuration(main={"size": (1280, 720)})
    camera.configure(config)
    camera.start()
    filenames = []
    for i in range(number):
        filename = "/home/pi/bakel/captured/image_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        camera.capture_file(filename)
        filenames.append(filename)
        sleep(interval)
    camera.stop()
    return filenames

def send_video():
    camera.video_configuration.size = (1640, 1232)
    camera.video_configuration.controls.FrameRate = 25.0
    camera.start_and_record_video("video.h264", duration=3)
    os.system("ffmpeg -y -r 25 -i video.h264 -vcodec copy video.mp4")
    bot = Bot(token=BOT_TOKEN)
    with open("video.mp4", "rb") as f:
        bot.send_video(chat_id=CHAT_ID, video=f)
    
#Sends a given image file to the specified Telegram chat via bot API.

def send_to_telegram(photo_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        payload = {"chat_id": CHAT_ID}
        files = {"photo": photo}
        response = requests.post(url, data=payload, files=files)
    return response.json()



def run_all():
    dx, dy, dz = accel(10, 0.01)
    p, r, yaw = orient()  # orient() returns (pitch, roll, yaw)

    if dx > 0.03 or dy > 0.03 or dz > 0.03:
        print("DEVICE MOVED")
        # Assignment wants roll, pitch, yaw (in that order)
        print(f"Roll = {r:.1f}°  Pitch = {p:.1f}°  Yaw = {yaw:.1f}°")

        # Optional extra (not required by the assignment)
        # send_video()

        # Capture 3 images, 1 second apart
        capture = camera_capture(3, 1.0)

        # Send each image to Telegram
        for photo in capture:
            result = send_to_telegram(photo)
            print("Sent to Telegram:", result)

        # Blink red/white every 0.5 s for a total of 3 s
        for i in range(6):  # 6 * 0.5 s = 3 s
            sense.clear(red if i % 2 == 0 else white)
            sleep(0.5)
        sense.clear()
    else:
        print("DEVICE IS STILL")
        sense.clear()



# *** MAIN PROGRAM LOOP ***
def main():
    schedule.every(run_interval).seconds.do(run_all)

    print("Starting periodic execution... Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        sleep(1)

if __name__ == "__main__":
    main()