import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def reduceFile(f, outDir="./csv/"):
	"""Convert input txt file to csv and save to local dir
	Return: path to output csv"""
	
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


def getDF_singlePix(f, pix=[0,0]):
	"""With input csv/dataframe, clean data to retain only "good hits" (matching timestamp and trigger in expected pixel) and standardize notation
			ASSUMES A SINGLE PIXEL IS ENABLED
	Return: Cleaned dataframe"""
	df=pd.read_csv(f)
	print(f)
	print(f'Input DF length: {len(df)}')
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
	"""With input csv/dataframe, clean data to retain only "good hits" (matching timestamp and trigger in expected pixel) and standardize notation
			ASSUMES A SINGLE PIXEL IS ENABLED
	Return: Cleaned dataframe
			Original length of dataframe
			Original number of row hits
			Original number of column hits
			Original number of triggered events"""
	
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
		
	#Raw number of triggers
	lenTrigs = df['NEvent'].iloc[-1]
		
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
	return df.reset_index(), int(lenIn), int(lenR), int(lenC), int(lenTrigs)
	
def getDF_fullArr(f):
	"""With input csv/dataframe, clean data to retain only "good hits" (matching timestamp and trigger) and standardize notation
			allow hit in any pixel
	Return: Cleaned dataframe"""
	df=pd.read_csv(f)
	print(f)
	print(f'Input DF length: {len(df)}')
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
	return df.reset_index()
		

def getRowCol(f):
	"""Identify row and column of active pixel from input file name
	Return: row and pixel value"""

	r,c = -1, -1
	
	parts=f.split('_')
	rStr = [p for p in parts if "row" in p]
	cStr = [p for p in parts if "col" in p]
	r = rStr[0][3:] #eliminate 'row'
	c = cStr[0][3:] #eliminate 'col'
	
	return r,c

