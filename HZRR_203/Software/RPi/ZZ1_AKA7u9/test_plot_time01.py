#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
plot - test
pl, Nov.2020
"""
import matplotlib.pylab as plt 

print("\n\nplot-test wich changed x-ticks")
print(50*"-")

#fig,ax = plt.subplots()

x = [i for i in range(26)]
y = [ i for i in range(len(x))]
plt.plot(x,y)

locs,labels = plt.xticks()
print("locs=",locs,"; labels=",labels)
ttics = [tt%24 for tt in locs]
print(ttics)
sttics=[str(x)for x in ttics]


plt.xticks(locs,sttics,rotation=0)
plt.show()
