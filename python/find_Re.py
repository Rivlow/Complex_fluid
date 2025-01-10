import numpy as np

nu = 1e-5
D = 6.4*1e-3
v = 2.375*1e-2

Re_init = (v*D/nu)

print(Re_init)

Re_lists = np.array([36, 45, 60, 65, 70, 80, 100])
new_v = v*(Re_lists/36)
print(new_v)

