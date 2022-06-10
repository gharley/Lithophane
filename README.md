# Lithophane Generator

Python app to create 3D lithophanes from a 2D image

## Overview

A [lithophane](https://en.wikipedia.org/wiki/Lithophane) is a 3D representation of a 2D image. The concept dates back 
to the early 1800's where very thin etchings or moldings were presented with a backlight. The thickest parts of the 
object would be the darkest and the thinnest parts the lightest thus displaying the image much like a photographic slide.

**litho_gen** performs the task of generating the 3D model from an image file. By default, the darkest pixels in the 
image are the lowest on the Z-axis and the lightest pixels are the highest. Inverting the image achieves the 
opposite effect.

If you only wish to 3D-print a thin object for back-lighting, almost any image should give okay results. However, 
if your intent is to carve a relief object with a CNC router, you should have an image that looks 3D to start with.

## License

I have placed my code in the public domain, so you can feel free to play with it, but be aware that the libraries 
used have their own more restrictive licenses.

## Installation

Windows users can download the .exe file in the dist folder for the latest stable version. 

Otherwise, copy or clone the repo to your system and open the folder with PyCharm. Other Python IDEs will work but 
may require some additional configuration. Make sure you have the required libraries installed and then run litho_gen.py.

### Required Libraries

 - QT5
 - PyQt5
 - pyvistaqt
 - PIL
 - PyVista
 - vtkmodules.all

## Usage

Usage is fairly straight-forward. 
 - Open an image file. `File/Load Image`
 - Select the **Units** you wish to use. (model files are always saved in millimeters) 
 - Set the desired **Output Size** and specify **width** or **height**. (the dimension not selected will be scaled)
 - Set **Max Z Height**. This determines the height of the model.
 - Set **Vectors/Pixel**. Higher numbers increase detail but take longer to generate. The default (5) is a good 
place to start. More than 10 is probably overkill (and may cause the app to crash).
 - 
