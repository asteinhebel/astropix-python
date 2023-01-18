import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
	
def arrayStats(data):	
	"""Calculate statistics of input array
	Return: list of [0, array mean, array variance] - mimics structure of returned Gaussian fit parameters"""

	mean=np.mean(data)
	var=np.var(data)
	
	return[0, mean, var]
	
def Gauss(x, A, mu, sigma):
	"""Gaussian function used for fitting, defining free parameters"""
	return A*np.exp(-(x-mu)**2/(2.0*sigma**2))
    
def fitGauss(data,nmbBins=50, range_in=None, alpha_in=1.0, normalizeHist=False, returnHist=False, returnR2=False):
	"""Fit input dataset to a Gaussian function
	Return: covariance fit matrix (and histogram, if indicated)"""
	
	#Massage inputs
	if range_in is None:
		try:
			range_in=[data.min(), data.max()] #default range
		except ValueError: #cannot find min/max, maybe data array is empty
			range_in=[0.,1.]
	if not np.isfinite(range_in[1]-range_in[0]): #if full array of NaNs or same values
		range_in=[0.,1.]
	
	fig = plt.figure()
	ax = fig.add_subplot(111)
	hist=ax.hist(data, nmbBins, range=range_in, alpha=alpha_in, density=normalizeHist)
	ydata=hist[0]
	binCenters=hist[1]+((hist[1][1]-hist[1][0])/2)
	binCenters=binCenters[:-1]
	muGuess = binCenters[np.argmax(ydata)]
	p0=[ydata.max(),muGuess,muGuess/2] #amp, mu, sig
	try:
		popt, pcov = curve_fit(Gauss, xdata=binCenters, ydata=ydata, p0=p0, absolute_sigma=True)
	except RuntimeError: #fit does not converge
		popt = arrayStats(data)
		
	#Calculate R^2
	r2=calcR2(ydata, Gauss(binCenters,*popt))
	
	if returnHist and returnR2:
		return popt,hist,r2
	elif returnHist and not returnR2:
		return popt,hist
	elif returnR2 and not returnHist:
		plt.close()
		return popt,r2
	else:
		plt.close() #close figure
		#return fit parameters
		return popt
	
		
def calcR2(y, y_fit):
	"""Calculate R^2 value to quantify goodness of fit
	Return: r2"""
	
	# residual sum of squares
	ss_res = np.sum((y - y_fit) ** 2)

	# total sum of squares
	ss_tot = np.sum((y - np.mean(y)) ** 2)

	# r-squared
	r2 = 1 - (ss_res / ss_tot)
	
	return r2
	
	
def calcCorrCoeff(x,y):
	"""Calculate Pearson correlation coefficient r value to quantify whether arrays x and y are correlated
	Return: r, error"""
	
	#returns full correlation matrix
	r = np.corrcoef(x,y)
	
	#error - https://psyarxiv.com/uts98/	
	#use off-diagonal element as r
	err = (1 - (r[0,1]**2)) / np.sqrt(x.size-3)
	
	return r[0,1], err
