# openmvcam-onecolortracking

In this project, using openMV and microPython cameras, certain positions and contours are implemented for a single-color, in the HSV model image. 

The problem of the openMV solution built in is a low speed, which I optimized by creating a radial binary search algorithm for finding boundaries, which allows us to win dozens of times in speed, but imposes some restrictions on the image itself.

There is also a translation function from the RGB to HSV color model, which makes this transfer extremely fast, by using @native
