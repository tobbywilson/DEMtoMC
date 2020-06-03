# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:55:53 2020

@author: Toby
"""

#Data import and manipulation
import numpy as np
import pandas as pd

#Data visualisation
import matplotlib.pyplot as plt


#GUI
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk


def flex_round(number,quantisation=0.5):
    return round(number*(1/quantisation))/(1/quantisation)


win = gtk.Window()
win.connect("destroy", gtk.main_quit)


win.show_all()

data = pd.read_csv(file,delim_whitespace=True,header=None,skiprows=6)

x_len = len(data)
y_len = len(data[0])

Data = data.applymap(flex_round)

plt.imshow(Data)