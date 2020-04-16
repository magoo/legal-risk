import matplotlib.pyplot as plt
from scipy.stats import powerlaw
from numpy import loadtxt


settlements = loadtxt('settlements.dat')


# Disclosure

# Will litigation happen

# (if litigation) How many litigators

# Class action?

# Discovery?

# Settlement

# Trial

# Regulation

# Indemnification


fit = powerlaw.fit(settlements)
incidents = powerlaw(a=fit[0], loc=fit[1], scale=fit[2])


plt.hist(settlements, bins=50)

plt.show()
