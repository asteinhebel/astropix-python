import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#Eliminates lines in original txt file that are not properly formatted
## Removes header
## If bitstream saved, removes bitstream 
## Save output as csv to local dir
def reduceFile(f, outDir="./csv/"):
	fileName=f.split('/')[-1][:-3]
	outFileName=outDir+fileName+"csv"
	
	with open(f, 'r') as fileIn:
		with open(outFileName, 'w') as fileOut:
			for line in fileIn:
				if len(line.split("\t"))>1:
					if len(line.split("\t"))==9:
						line="NEvent\t"+line
					csvline=[sub.replace("\t",",") for sub in line]
					csvline=''.join(csvline)
					fileOut.write(csvline)
	return outFileName

#pull dataframe from CSV and read ToT information
#ASSUMES A SINGLE PIXEL IS ENABLED
def getDF_singlePix(f, pix=[0,0]):
	df=pd.read_csv(f)
	#print(f'Input DF length: {len(df)}')
	#Drop any hit from count 0 - FPGA dump
	try:
		df=df[df['NEvent']!=0]
	except KeyError: #more modern files change the variable names, no FPGA dump
		df.rename(columns={"readout": "NEvent", "timestamp": "tStamp","location": "Locatn","tot_us": "ToT(us)", "isCol":"Row/Col", "hittime":"RealTime"},inplace=True)
		df.drop(columns=['dec_order'], inplace=True)	
		#convert boolean column to Row/Col structure
		df['Row/Col'] = df['Row/Col'].replace({True: 'Col', False: 'Row'})
	#put matching row and column info in one line
	df_row = df[df["Row/Col"] == "Row"]
	df_col = df[df["Row/Col"] == "Col"]	
	df = df_row.merge( df_col, how="outer", on = ["tStamp","NEvent"], suffixes = ["_row", "_col"] )
	df.dropna(inplace=True)
	#Drop duplicates	
	df.drop_duplicates(subset=["tStamp", "NEvent"], keep=False, inplace=True, ignore_index=True)
	#Check whether pix argument contains ints. If not, convert to ints
	if not isinstance(pix[0], int):
		pix=[int(pix[0]),int(pix[1])]
	#Remove entries if any pixel other than pix is measured - only one pixel enabled at a time
	df=df[df['Locatn_row']==pix[0]]
	df=df[df['Locatn_col']==pix[1]]
	#print(df.describe().T)
	return df.reset_index()
	
def getDF_singlePix_extraVars(f, pix=[0,0]):
	df=pd.read_csv(f)
	lenIn=len(df)
	#Drop any hit from count 0 - FPGA dump
	try:
		df=df[df['NEvent']!=0]
	except KeyError: #more modern files change the variable names, no FPGA dump
		df.rename(columns={"readout": "NEvent", "timestamp": "tStamp","location": "Locatn","tot_us": "ToT(us)", "isCol":"Row/Col", "hittime":"RealTime"},inplace=True)
		df.drop(columns=['dec_order'], inplace=True)	
		#Record values from original DF before selecting row/col matches
		lenC=df['Row/Col'].sum()
		lenR=lenIn-lenC
		#convert boolean column to Row/Col structure
		df['Row/Col'] = df['Row/Col'].replace({True: 'Col', False: 'Row'})
		
	#Record values from original DF before selecting row/col matches
		
	#put matching row and column info in one line
	df_row = df[df["Row/Col"] == "Row"]
	df_col = df[df["Row/Col"] == "Col"]	
	df = df_row.merge( df_col, how="outer", on = ["tStamp","NEvent"], suffixes = ["_row", "_col"] )
	df.dropna(inplace=True)
	#Drop duplicates	
	df.drop_duplicates(subset=["tStamp", "NEvent"], keep=False, inplace=True, ignore_index=True)
	#Check whether pix argument contains ints. If not, convert to ints
	if not isinstance(pix[0], int):
		pix=[int(pix[0]),int(pix[1])]
	#Remove entries if any pixel other than pix is measured - only one pixel enabled at a time
	df=df[df['Locatn_row']==pix[0]]
	df=df[df['Locatn_col']==pix[1]]
	return df.reset_index(), int(lenIn), int(lenR), int(lenC)
	
	
#visualize array
def arrayVis(arrIn, barTitle:str=None, invert:bool=False):

	#expecting 35x35 array for arrIn
	#if invert=True, pixel r0c0 is NOT in bottom left (like in array). invert=True reconfigures arrIn for proper visualization

	if invert:
		arrIn = np.flip(arrIn,0)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	cax=ax.matshow(arrIn)#,cmap=plt.cm.YlOrRd)
	#redisplay y axis to match proper labeling
	ylabels=[34-2*i for i in range(18)]
	ax.set_xticks([2*i for i in range(18)])
	ax.set_yticks([2*i for i in range(18)])
	ax.set_yticklabels(ylabels)
	ax.tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=True)
	cbar = plt.colorbar(cax)
	if barTitle is not None:
		cbar.set_label(barTitle) 	
	else:
		cbar.set_label('Counts') 	
	plt.tight_layout() #reduce margin space	
	plot=plt.gcf()
	
	return plot
	

