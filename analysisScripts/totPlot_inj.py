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
def getDF(f):
	df=pd.read_csv(f) 
	#Drop any hit from count 0 - FPGA dump
	df=df[df['Count']!=0]
	#put matching row and column info in one line
	df_row = df[df["Row/Col"] == "Row"]
	df_col = df[df["Row/Col"] == "Col"]
	df = df_row.merge( df_col, how="outer", on = ["tStamp","Count"], suffixes = ["_row", "_col"] )
	#Drop duplicates
	df.drop_duplicates(subset=["tStamp", "Count"], keep=False, inplace=True, ignore_index=True)
	#Remove entries if any pixel other than (0,0) is measured - only (0,0) is enabled
	df=df[df['Locatn_row']==0]
	df=df[df['Locatn_col']==0]
	print(df.describe().T)
	return df.reset_index()


#################################################################
# main
#################################################################

if __name__ == "__main__":
	dirPath=os. getcwd()[:-15] #go one directory above the current one where only scripts are held
	
	fileIn="logInj/chip1_1min_1.0V_analogPaired_dac16_1.0_injection_20220526-153245.log"
	
	readFile=reduceFile(dirPath+fileIn)
	df=getDF(readFile)
	
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
	plt.axhline(y=1)
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