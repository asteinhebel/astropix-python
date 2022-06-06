import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os,sys

import digitalDataHelpers as ddh


#################################################################
# helper functions
#################################################################


#################################################################
# main
#################################################################

if __name__ == "__main__":
	dirPath=os. getcwd()[:-15] #go one directory above the current one where only scripts are held
	
	# For NOISE: Use files of the style *_beamDigital_*.txt (*.log files are only bitstreams)
	fileIn="logInj/chip1_1min_1.8V_analogPaired_dac16_1.8_injection_20220526-153421.log"
	
	readFile=ddh.reduceFile(dirPath+fileIn)
	df=ddh.getDF(readFile)
	
	plt.plot( df["ToT(us)_row"], df['ToT(us)_col'], ".", alpha=0.5  )
	plt.xlabel('row ToT duration [us]')
	plt.ylabel('column ToT duration [us]')
	x=np.arange(40)
	plt.plot(x, 'b')
	plt.show()
	plt.clf()
    
	plt.plot(df['ToT(us)_row']/df['ToT(us)_col'],"o")
	plt.xlabel('Triggered point')
	plt.ylabel('Ratio row/col ToT')
	plt.axhline(y=1, color='r')
	plt.show()
	plt.clf()
	ratio=np.array(df['ToT(us)_row']/df['ToT(us)_col'])
	outliers=np.where((ratio<0.5)|(ratio>1.5))
	print(df.loc[outliers])
    
	plt.hist(df['ToT(us)_row'].append(df['ToT(us)_col']),40,fc=(0,0,1,1), label="All")
	plt.hist(df['ToT(us)_row'],40,fc=(1,0,0,0.5),label="Row")
	plt.hist(df['ToT(us)_col'],40,fc=(0,1,0,0.5),label="Col")
	plt.xlabel('ToT (us)')
	plt.ylabel('Counts')
	plt.legend(loc="best")
	plt.show()