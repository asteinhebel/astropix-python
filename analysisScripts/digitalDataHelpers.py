import pandas as pd

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
	#Drop any hit from count 0 - FPGA dump
	try:
		df=df[df['NEvent']!=0]
	except KeyError: #more modern files change the variable names, no FPGA dump
		df.rename(columns={"readout": "NEvent", "timestamp": "tStamp","location": "Locatn","tot_us": "ToT(us)", "isCol":"Row/Col", "hittime":"RealTime"},inplace=True)	
		#convert boolean column to Row/Col structure
		df['Row/Col'] = df['Row/Col'].replace({True: 'Col', False: 'Row'})
	#put matching row and column info in one line
	df_row = df[df["Row/Col"] == "Row"]
	df_col = df[df["Row/Col"] == "Col"]	
	df = df_row.merge( df_col, how="outer", on = ["tStamp","NEvent"], suffixes = ["_row", "_col"] )
	#Drop duplicates	
	df.drop_duplicates(subset=["tStamp", "NEvent"], keep=False, inplace=True, ignore_index=True)
	#Remove entries if any pixel other than pix is measured - only one pixel enabled at a time
	df=df[df['Locatn_row']==pix[0]]
	df=df[df['Locatn_col']==pix[1]]
	#print(df.describe().T)
	return df.reset_index()