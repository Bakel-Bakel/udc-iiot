from sense_hat import SenseHat
#from sense_emu import SenseHat
from time import sleep

sense = SenseHat()

# Set LEDs' values
X = [255, 0, 0] # Red
O = [255, 255, 255] # White
question = [
O, O, O, X, X, O, O, O,
O, O, X, O, O, X, O, O,
O, O, O, O, O, X, O, O,
O, O, O, O, X, O, O, O,
O, O, O, X, O, O, O, O,
O, O, O, X, O, O, O, O,
O, O, O, O, O, O, O, O,
O, O, O, X, O, O, O, O
]
sense.set_pixels(question)

# Change LEDs’ color
sense.clear() # Turn off all LEDs
sleep(1)
red = (255, 0, 0)
sense.clear(red) # Red
sleep(1)
sense.clear(255, 255, 255) # White
# Muestra un mensaje
sense.show_message("Hello world!", text_colour=[255, 0, 0])