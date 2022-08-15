import pandas as pd
import numpy as np
import h5py

#create dataframe from h5py 
def getDF(f):
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

