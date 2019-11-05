import numpy
import os

def scioRead(path):
	f = open(path)
	ndim = numpy.fromfile(f, 'int32', 1)
	x = int(ndim)
	if (x<0):
		diff=True
		x=-1*x
	else:
		diff=False

	sz = numpy.fromfile(f, 'int32', x)
	mytype=numpy.fromfile(f,'int32',1)
	vec = numpy.fromfile(f, dtype=int2dtype(mytype))
	nmat=vec.size/numpy.product(sz)
	new_sz=numpy.zeros(sz.size+1,dtype='int32')
	new_sz[0]=nmat
	new_sz[1:]=sz


	mat=numpy.reshape(vec,new_sz)
	if diff:
		mat=numpy.cumsum(mat,0)

	return mat

def int2dtype(myint):
    if (myint==8):
        return 'float64'
    if (myint==4):
        return 'float32'
    if (myint==-4):
        return 'int32'
    if (myint==-8):
        return 'int64'
    if (myint==-104):
        return 'uint32'
    if (myint==-108):
        return 'uint64'

#x = scioRead('D:/pol0.scio')

#print(type(x))
#print(len(x))