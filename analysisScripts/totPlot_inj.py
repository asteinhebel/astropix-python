import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os,sys


#################################################################
# helper functions
#################################################################

#Eliminates lines in original txt file that are not properly formatted
## Removes header
## If bitstream saved, removes bitstream 
## Save output as csv to local dir
def reduceFile(f, outDir="./"):
	
	fileName=f.split('/')[-1][:-3]
	outFileName=outDir+fileName+"csv"
	
	with open(f, 'r') as fileIn:
		with open(outFileName, 'w') as fileOut:
			for line in fileIn:
				if len(line.split("\t"))>1:
					if len(line.split("\t"))==9:
						line="Count\t"+line
					csvline=[sub.replace("\t",",") for sub in line]
					csvline=''.join(csvline)
					fileOut.write(csvline)
	return outFileName

#pull dataframe from CSV and read ToT information
def getToT(f):
	df=pd.read_csv(f)
	print(df.info())
	print(df.head(10))
	return df


#################################################################
# main
#################################################################

if __name__ == "__main__":
	dirPath=os. getcwd()[:-15] #go one directory above the current one where only scripts are held
	
	fileIn="logInj/chip1_1min_1.0V_analogPaired_dac16_1.0_injection_20220526-153245.log"
	
	readFile=reduceFile(dirPath+fileIn)
	df=getToT(readFile)
	
	n,bins,patches=plt.hist(df['ToT(us)'],40)
	plt.xlabel('ToT duration [us]')
	plt.ylabel("Counts")
	plt.show()