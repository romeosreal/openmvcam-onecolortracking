import sensor, image, micropython, time
DEBUG = True

# NOISE = +- 2

H_ERROR = 0.4

def dot(x, y, color=(255, 0, 0), sz = 3): # Set dot on point coordinate
    if DEBUG:
        for i in range(sz * sz):
            img.set_pixel(int(x) + (i % sz) - 1, int(y) + int(i / sz) - 1, color)

@micropython.native
def sgn(a:int) -> int:
    if a > 0:
        return 1
    if a < 0:
        return -1
    return 0

@micropython.native
def hsv(r:int, g:int, b:int) -> object: # Hyper fast transform rgb to hsv (0.013ms)
    if r > b:
        if r > g:
            mx = r

            if b > g:
                df = mx - g
            else:
                df = mx - b

            h = ((g - b) / df) % 6
            s = df / mx

        else:
            mx = g

            if r > b:
                df = mx - b
            else:
                df = mx - r

            h = (((b - r) / df) + 2) % 6
            s = df / mx
    else:
        if b > g:
            mx = b

            if r > g:
                df = mx - g
            else:
                df = mx - r

            h = (((r - g) / df) + 4) % 6
            s = df / mx
        else:
            mx = g

            if r > b:
                df = mx - b
            else:
                df = mx - r

            if df == 0:
                h = 0
            else:
                h = (((b - r) / df) + 2) % 6

            if mx == 0:
                s = 0
            else:
                s = df / mx

    return h, s, mx # 0-6 : 0-1 : 0-255 - range of output value(small transform for hsv)

micropython.opt_level(3)            # Set maxium optimization level
sensor.reset()
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB
sensor.set_framesize(sensor.QVGA)   # Optimised solution for quality
sensor.skip_frames(time = 3000)     # Wait for calibrate
sensor.set_auto_gain(False)         # Disable auto gain control
sensor.set_auto_whitebal(False)     # Disable white balance
sensor.set_auto_exposure(False)     # Disable auto exposure correction

W = sensor.width()                  # Get width of camera
H = sensor.height()                 # Get height of camera

lcx = int(W / 2)
lcy = int(H / 2)
last_height = 20
last_width = 120
w_step = last_width / 4
h_step = last_height / 4

tt = time.ticks()
while time.ticks() - tt < 3000:
    img = sensor.snapshot() # Get camera image
    for x in range(50):
        img.set_pixel(int(W / 2 - 25 + x), int(H / 2 + 25), (255, 0, 0))
        img.set_pixel(int(W / 2 - 25 + x), int(H / 2 - 25), (255, 0, 0))
h = 0
img = sensor.snapshot()
mnS = 1
mnV = 255
for x in range(50):
    for y in range(50):
        clr = img.get_pixel(int(W / 2 - 25 + x), int(H / 2 - 25 + y)) # Get pixel
        print(clr)
        hclr = hsv(clr[0], clr[1], clr[2])  # Transform to hsv
        h += hclr[0] / 2500              # Sum for median value
        if mnS > hclr[1]:
            mnS = hclr[1]
        if mnV > hclr[2]:
            mnV = hclr[2]

if mnS > 0.65:
    mnS = 0.65

if mnV > 130:
    mnV = 130

blue = (h, mnS * 0.9, mnV * 0.9)
print(blue)

stepX = 30
stepY = 10

lw = W * 2
lh = H * 2

right = left = W >> 1
top = bottom = H >> 1

while(True):
    tt = time.ticks()       # Start timer
    img = sensor.snapshot() # Get camera image

    x, y, i, _x, _y = 0, 0, 0, 0, 0
    foundPix = False
    while i < (W * 8 / stepX):   # check nearest star-form pixels
        stp = i % 8

        if stp == 0:    # Its bad solution... But mb work) Its star, if you need understood it
            x = _x
            y = _y
            _x += stepX
        elif stp == 1:
            x = _x
            y = 0
        elif stp == 2:
            x = _x
            y = -_y
        elif stp == 3:
            x = 0
            y = _y
        elif stp == 4:
            x = -_x
            y = -_y
            _y += stepY
        elif stp == 5:
            x = -_x
            y = 0
        elif stp == 6:
            x = -_x
            y = _y
        elif stp == 7:
            x = 0
            y = -_y

        if (x + lcx) < 0 or (x + lcx) >= W: # If pixel go out of camera width
            x = 0
        if (y + lcy) < 0 or (y + lcy) >= H: # If pixel go out of camera height
            y = 0
        pix = img.get_pixel(int(lcx + x), int(lcy + y)) # Get pixel
        if pix == None:
            continue
        pixH = hsv(pix[0], pix[1], pix[2])              # Transform rgb to hsv
        dot(lcx + x, lcy + y)                           # Create dot on coord of check pixel
        if (abs(pixH[0] - blue[0]) < H_ERROR and pixH[1] > blue[1] and pixH[2] > blue[2]): # Check..
            lcx += int(x)
            lcy += int(y)
            foundPix = True
            dot(lcx, lcy, (0, 255, 0), 7)
            break
        i += 1

    if not foundPix: # If pixel not found - scan all display - take many time
        for x in range(int(stepX) >> 1, W, stepX):
            for y in range(int(stepY) >> 1, H, stepY):
                pix = img.get_pixel(x, y)     # Get pixel
                pixH = hsv(pix[0], pix[1], pix[2])      # Transform rgb to hsv
                dot(x, y)
                if (abs(pixH[0] - blue[0]) < H_ERROR and pixH[1] > blue[1] and pixH[2] > blue[2]):
                    lcx = x
                    lcy = y
                    foundPix = True
                    dot(lcx, lcy, (0, 255, 0), 7)
                    break
            if foundPix:
                break

    if not foundPix:
        continue

    lht = lh
    if lcy + lh >= H:   # Set stopper for last object width
        lht = H - lcy
    bi = bni = lht >> 1
    while not bni == 0: # Radial binary search
        bni = bni >> 1
        pix = img.get_pixel(lcx, lcy + bi)    # Get pixel
        if pix == None:
            continue
        pixH = hsv(pix[0], pix[1], pix[2])              # Transform rgb to hsv
        if abs(pixH[0] - blue[0]) < H_ERROR and pixH[1] > blue[1] and pixH[2] > blue[2]:
            bi += bni
        else:
            bi -= bni
    top = lcy + bi
    dot(lcx, top, (255, 0, 0), 9)

    lht = lh
    if lcy - lh < 0:   # Set stopper for last object width
        lht = lcy
    bi = bni = lht >> 1
    while not bni == 0: # Radial binary search
        bni = bni >> 1
        pix = img.get_pixel(lcx, lcy - bi)    # Get pixel
        if pix == None:
            continue
        pixH = hsv(pix[0], pix[1], pix[2])              # Transform rgb to hsv
        if abs(pixH[0] - blue[0]) < H_ERROR and pixH[1] > blue[1] and pixH[2] > blue[2]:
            bi += bni
        else:
            bi -= bni
    bottom = lcy - bi
    dot(lcx, bottom, (255, 0, 0), 9)
    lcy = (bottom + top) >> 1

    lwt = lw
    if lcx + lw >= W:   # Set stopper for last object width
        lwt = W - lcx
    bi = bni = lwt >> 1
    while not bni == 0: # Radial binary search
        bni = bni >> 1
        pix = img.get_pixel(lcx + bi, lcy)    # Get pixel
        if pix == None:
            continue
        pixH = hsv(pix[0], pix[1], pix[2])              # Transform rgb to hsv
        if abs(pixH[0] - blue[0]) < H_ERROR and pixH[1] > blue[1] and pixH[2] > blue[2]:
            bi += bni
        else:
            bi -= bni
    left = lcx + bi
    dot(left, lcy, (255, 0, 0), 9)

    lwt = lw
    if lcx - lw < 0:    # Set stopper for last object width
        lwt = lcx
    bi = bni = lwt >> 1
    while not bni == 0:      # Radial binary search
        bni = bni >> 1
        pix = img.get_pixel(lcx - bi, lcy)    # Get pixel
        if pix == None:
            continue
        pixH = hsv(pix[0], pix[1], pix[2])              # Transform rgb to hsv
        if abs(pixH[0] - blue[0]) < H_ERROR and pixH[1] > blue[1] and pixH[2] > blue[2]:
            bi += bni
        else:
            bi -= bni
    right = lcx - bi
    dot(right, lcy, (255, 0, 0), 9)

    lcx = (left + right) >> 1
    print(bottom)
    #print(time.ticks() - tt) # End timer
