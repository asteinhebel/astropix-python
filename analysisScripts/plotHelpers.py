import matplotlib.pyplot as plt
import numpy as np


def arrayVis(arrIn, barRange=None, barTitle:str=None, invert:bool=False):
	"""Visualize array by plotting 35x35 matrix and filling each pixel with its value designated by input array
	Return: subplot of figure (for subsequent plotting)"""
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
	if barRange is not None:
		cax.set_clim(vmin=barRange[0], vmax=barRange[1])
	if barTitle is not None:
		cbar.set_label(barTitle) 	
	else:
		cbar.set_label('Counts') 	
	plt.tight_layout() #reduce margin space	
	
	return cax
	
	
