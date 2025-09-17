from sense_hat import SenseHat
from time import sleep, time

sense = SenseHat()

R = [255, 0, 0]
W = [255, 255, 255]
B = [0, 0, 0]

question = [
W, W, W, R, R, W, W, W,
W, W, R, W, W, R, W, W,
W, W, W, W, W, R, W, W,
W, W, W, W, R, W, W, W,
W, W, W, R, W, W, W, W,
W, W, W, R, W, W, W, W,
W, W, W, W, W, W, W, W,
W, W, W, R, W, W, W, W
]
sense.set_pixels(question)
