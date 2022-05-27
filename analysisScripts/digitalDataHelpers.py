import pandas as pd

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
						line="NEvent\t"+line
					csvline=[sub.replace("\t",",") for sub in line]
					csvline=''.join(csvline)
					fileOut.write(csvline)
	return outFileName

#pull dataframe from CSV and read ToT information
def getDF(f):
	df=pd.read_csv(f) 
	#Drop any hit from count 0 - FPGA dump
	df=df[df['NEvent']!=0]
	#put matching row and column info in one line
	df_row = df[df["Row/Col"] == "Row"]
	df_col = df[df["Row/Col"] == "Col"]
	df = df_row.merge( df_col, how="outer", on = ["tStamp","NEvent"], suffixes = ["_row", "_col"] )
	#Drop duplicates
	df.drop_duplicates(subset=["tStamp", "NEvent"], keep=False, inplace=True, ignore_index=True)
	#Remove entries if any pixel other than (0,0) is measured - only (0,0) is enabled
	df=df[df['Locatn_row']==0]
	df=df[df['Locatn_col']==0]
	print(df.describe().T)
	return df.reset_index()