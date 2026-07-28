import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

A = np.array([
    [0.33,0.30,0.29,0.25,0.22,0.25],
    [0.30,0.20,0.00,0.38,0.20,0.00],
    [0.13,0.12,0.08,0.26,0.22,0.16],
    [0.27,0.22,0.23,0.34,0.31,0.27],
    [0.39,0.27,0.12,0.50,0.29,0.08],
    [0.38,0.34,0.30,0.31,0.25,0.23]
])

plt.figure(figsize=(6,5))
sns.heatmap(
    A,
    annot=True,
    cmap="YlOrRd",
    vmin=0,
    vmax=0.5,
    square=True,
    linewidths=0.5
)
plt.show()