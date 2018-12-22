#!/bin/python
#Creates a graph for all data in a given CSV, using the first column as the x-values, and all other columns as the y-values for the plots. Change the sizing and plotting to suit your needs. 
import sys,re,os
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import csv
import argparse

class Plotter:
  def __init__(self, ax, s=20, linewidth=1.0):
    self.ax = ax
    self.s = s
    self.linewidth = linewidth

  #plots scatterplot and logarithmic regression
  def log_plot(self, x, y, label="", d=1, c="black", scatter=True, plot=True): #x data, y data, the axis to plot on, label, the degree of the polynomial, and the color
    l = min([len(x), len(y)])
    fit = np.polyfit(np.log(x[:l]), y[:l], deg=d) #seems to work whether or not set_yscale is 'log'
    fity = []
    for t in x[:l]:
      val = 0
      for i, b in enumerate(fit):
	val = val + fit[i] * ((np.log(t)) ** (len(fit)-1-i))
      fity.append(val)
    if scatter:
      self.ax.scatter(x[:l], y[:l], c=c, s=self.s) #change s to make the dots on the scatterplot bigger
    if plot:
      self.ax.plot(x[:l], fity, color=c, label=label, linewidth=self.linewidth) #change linewidth to make the line for the plot thicker
    
  #plots scatterplot and polynomial regression
  def poly_plot(self, x, y, label="", d=1, c="black", scatter=True, plot=True):
    l = min([len(x), len(y)])
    if self.ax.get_yscale() == 'log':
      fit = np.polyfit(x[:l], [np.log10(z) for z in y[:l]], deg=d)
    else:
      fit = np.polyfit(x[:l], y[:l], deg=d)
    fity = []
    for t in x[:l]:
      val = 0
      for i, b in enumerate(fit): #build the y-value from the polynomial
	val = val + fit[i] * (t ** (len(fit)-1-i))
      if self.ax.get_yscale() == 'log':
	fity.append(10 ** val)
      else:
	fity.append(val)
    if scatter:
      self.ax.scatter(x[:l], y[:l], c=c, s=self.s) #change s to make the dots on the scatterplot bigger
    if plot:
      self.ax.plot(x[:l], fity, color=c, label=label, linewidth=self.linewidth) #change linewidth to make the line for the plot thicker
  
#transposes a data frame, assuming the data is float
def reverse_frame(data):
  newdata = [[] for col in data[0]]
  for row in data:
    for i in range(len(newdata)):
      try:
	yval = float(row[i])
	newdata[i].append(yval)
      except:
	pass
  return(newdata)

#returns an array containing the current min and max
def compare_range(xval, xran):
  if len(xran) == 0:
    xran.append(xval)
  elif len(xran) == 1:
    if xval > xran[0]:
      xran = [xran[0], xval]
    else:
      xran = [xval, xran[0]]
  elif xval > xran[1]:
    xran[1] = xval
  elif xval < xran[0]:
    xran[0] = xval
  return(xran)

def eval_str_f(string): #defaults to false if it doesn't find true
    string = (string.strip()).lower()
    if string == "true" or string == "1" or string == "t":
      return(True)
    else: 
      return(False)

def parse_args(sysargv):
  parser = argparse.ArgumentParser()
  parser.add_argument("--csv", metavar='FILE', type=str, default=None, action="store", help="file containing the data to graph")
  parser.add_argument("--header", metavar='BOOL', type = str, default="false", action="store", help="whether or not the first row of the CSV file contains column headers")
  return(parser.parse_args())
  
def main(sysargv=[]):
  args = parse_args(sysargv)
  
  #range of minimum and maximum values for x and y variables
  #could be useful when defining xlim and ylim
  xran = []
  yran = []
  
  #read the data from the CSV
  x = []
  y = []
  labels = []
  with open(args.csv, "r") as csvfile:
    reader = csv.reader(csvfile, delimiter=",",quotechar="\'")
    for i,row in enumerate(reader):
      if i == 0 and eval_str_f(args.header):
	labels = row
      else:
	try: #skips row if data is not numeric
	  xval = float(row[0])
	  x.append(xval)
	  
	  #find the x minimum and maximum
	  xran = compare_range(xval, xran)
	  
	  if len(y) == 0:
	    y = [[] for z in row[1:]]
	  for j,yval in enumerate(row[1:]):
	    yval = float(yval)
	    y[j].append(yval)
	    
	    #find the y minimum and maximum
	    yran = compare_range(yval, yran)
	except Exception as e:
	  print(str(e))

  #################################################
  #################################################
  #CHANGE THIS PART TO SUIT YOUR NEEDS
  fig,ax=plt.subplots(figsize=(20, 10)) #adjusts the figure size
  My_Plotter = Plotter(ax, 75, 3.0) #adjusts the scatterplot point size and regression line width
  ax.set_yscale('log') #creates a logarithmic scale for the y-axis

  matplotlib.rcParams.update({'font.size': 30}) #adjusts the font size

  plt.xlim(xran[0]-0.02*(xran[1]-xran[0]), xran[1]+0.02*(xran[1]-xran[0])) #limits for the x-axis
  plt.ylim(yran[0]-1, yran[1]+300) #limits for the y-axis
  plt.xlabel("Time (seconds)")
  plt.ylabel("Hydrodynamic Radius (nm); Volume")
  
  #this part actually plots the data, using a scatterplot and a best fit polynomial or logarithmic
  #arguments are the x data array, the y data array, the label, the degree of the polynomial, and the color on the graph
  My_Plotter.log_plot(x, y[0], "2000 $\mu$M ATP", 3, "red") 
  My_Plotter.log_plot(x, y[1], "500 $\mu$M ATP", 4, "blue")
  My_Plotter.poly_plot(x, y[2], "250 $\mu$M ATP", 8, "orange")
  My_Plotter.poly_plot(x, y[3], "100 $\mu$M ATP", 3, "green")
  My_Plotter.poly_plot(x, y[4], "50 $\mu$M ATP", 2, "magenta")
  My_Plotter.poly_plot(x, y[5], "0 $\mu$M ATP", 1, "black")

  #put the legend in the right side of the graph
  box = ax.get_position()
  ax.set_position([box.x0, box.y0, box.width * 0.78, box.height]) #change box.width scaling so that legend fits
  ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
  #################################################
  #################################################

  #create and save the graph
  fig.savefig(os.path.join(os.path.dirname(args.csv), "figure")) #saves the figure in the same directory as the data source
  plt.close()

if __name__ == "__main__":
  main(sys.argv[1:])
