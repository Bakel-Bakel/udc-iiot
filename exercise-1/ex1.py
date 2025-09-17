from sense_hat import SenseHat
from time import sleep, time

sense = SenseHat()

R = [255, 0, 0]
W = [255, 255, 255]
B = [0, 0, 0]
G = [0,255,0]

question = [
G, G, G, W, W, G, G, G,
G, G, G, W, W, G, G, G,
G, G, G, W, W, G, G, G,
G, G, G, W, W, G, G, G,
G, G, G, W, W, G, G, G,
G, G, G, W, W, G, G, G,
G, G, G, W, W, G, G, G,
G, G, G, W, W, G, G, G
]
sense.set_pixels(question)
