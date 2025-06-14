# #!/usr/bin/env python
# from time import sleep
# import sys
# from spotify import get_track, get_art

# # from rgbmatrix import RGBMatrix, RGBMatrixOptions
# from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
# from PIL import Image

# # Configuration for the matrix
# options = RGBMatrixOptions()
# options.rows = 32
# options.chain_length = 1
# options.parallel = 1
# options.hardware_mapping = "regular"  # If you have an Adafruit HAT: 'adafruit-hat'

# matrix = RGBMatrix(options=options)

# # Make image fit our screen.
# art_url, artist, title = get_track()
# image = get_art(art_url)
# # image.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)

# matrix.SetImage(image.convert("RGB"))

# last_track = None
# try:
#     print("Press CTRL-C to stop.")
#     while True:
#         sleep(5)
# except KeyboardInterrupt:
#     sys.exit(0)
