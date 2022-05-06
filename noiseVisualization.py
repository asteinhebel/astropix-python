import glob,os
import numpy as np
import matplotlib.pyplot as plt


def getRowCounts(f):

	fileIn = open(f,'r')
	lines = fileIn.readlines()
	#line[0] = header -> remove
	del lines[0]
	#columns separated by tabs
	#Column ~ Row ~ Counts ~ Timestamp
	countVals=[]
	for line in lines:
		countVals.append(float(line.split('\t')[2]))
	
	return countVals

def saveFromInput(saveFile): 
	plot=plt.gcf() #get current figure - saves fig in case savePlt==True
	plt.show() #creates new figure for display
	inp= 'a'
	while inp!='y' and inp!='n':
		print("Save plot? y/n")
		inp = input()
	savePlt=True if inp=='y' else False
	if savePlt: #save plt stored with plt.gcf()
		print(f"Saving {saveFile}")
		plot.savefig(saveFile)

if __name__ == "__main__":

	dataDir="output_bench/"
	saveto="noiseMap_bench.pdf"
	
	
	rows=[]
	cols=[]
	counts=[]
	
	os.chdir(dataDir)	
	for f in glob.glob("*.txt"): #get all txt files in datadir
		colVal=float(f.split('_')[1][-1])
		countVals=getRowCounts(f)
		rowVals=[i+1 for i in range(-1,34)]
		colVals=np.repeat(colVal,35) #array of same length as rowVals but all with the column number
		rows.append(rowVals)
		cols.append(colVals.tolist())
		counts.append(countVals)
		
	#flatten arrays
	rows=sum(rows,[])
	cols=sum(cols,[])
	counts=sum(counts,[])
	
	#pixel array = 35x35 pixels
	pl=plt.scatter(cols, rows, c=counts,s=100, cmap='Reds', marker="s")
	cbar = plt.colorbar(pl)
	plt.xlabel("Column")
	plt.ylabel("Row")
	cbar.set_label('Counts (of 1000)') 
	plt.tight_layout() #reduce margin space	
	#plt.show()
	
	saveFromInput(saveto)
	
	fullArray=35*6
	noisy=0
	for c in counts:
		if c>300:
			noisy+=1
	print(f"Saturated pixels (count==1000): {counts.count(1000)/fullArray*100:.3f}% ({counts.count(1000)} pixels)")
	print(f"Noisy pixels (count>300): {noisy/fullArray*100:.3f}% ({noisy} pixels)")