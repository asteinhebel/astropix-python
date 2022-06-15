import numpy as np
import time

import hitplotter 

nPix = 40
p = hitplotter.HitPlotter(nPix)
    
for i in range(30):

    numX = 1+np.random.poisson(.2)
    numY = 1+np.random.poisson(.2)
 
    if i == 17:
        X = range(30)
    else:
        X = np.random.randint(0,nPix, numX)

    Y = np.random.randint(0,nPix, numY)

    start = time.perf_counter()

    p.plot_event(Y, X, i)

    stop = time.perf_counter()
    
    print('Dead time: ', (stop - start), "s")

    rest = np.random.normal(1, 0.2)
    time.sleep(rest)
