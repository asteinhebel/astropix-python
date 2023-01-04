import pandas as pd
import numpy as np
import h5py


def getDF(f):
	"""Create dataframe from input analog h5py
	Return: dataframe containing time of trigger, peak height, ToT proxy"""
	f=h5py.File(f, 'r')
	labels=[key for key in f.keys()]
	labels.remove('run1')#remove full traces
	labels.remove('run1_scaling')
	labels.remove('run1_triggerSettings')
	labels.remove('run1_metaData')
	totEls=len(f[labels[0]])
	#print(labels)

	time=np.array(f['run1_trigTime'])
	peaks=np.array(f['run1_peaks'])
	tot=np.array(f['run1_analogToT'])
	dataArr=np.vstack((peaks,time,tot)).T
	
	df = pd.DataFrame(dataArr, columns=['Peaks','Time', 'AnalogToT'])
	return df

def new_i(arr):
	"""Identify each different setting in run
		if more than 1s between triggers, then it's a new setting
	Return: array of array indices where new setting begins"""
	diffArr=np.diff(arr)
	indexArray=np.where(diffArr>1)
	indexArray=np.insert(indexArray,0,0)
	return indexArray

def get_average_traces( filename , smoothing:int=50):
	"""Average traces together to find average response
	Return: array of points that draw the average trace, length of array defined by smoothing variable
			oscilloscope x increment in us"""
	#smoothing = how many points from original curve are skipped before plotting the next one. 
	#			 Original curve has 10k points
	#			 Smaller value of 'smoothing' leads to noisier curve 

	f = h5py.File(filename, 'r')
	traces = f['run1'] #baseline subtracted already
	time = f['run1_trigTime']
	scalingDict = f['run1_scaling']
	mean=[]

	newRun=new_i(time)
	for i in range(1,len(newRun)):
		#smooth curve
		mean.append(np.mean(traces[newRun[i-1]:newRun[i]], axis = 0)[0::smoothing])
		
	#Remove sections that do not have recorded traces (ie when number of recorded traces was exceeded during data taking but pulse heights were still recorded)
	mean=np.array(mean)
	noNan=np.array([~np.isnan(i[0]) for i in mean])
	
	return mean[noNan], scalingDict[1] #xincrement in us