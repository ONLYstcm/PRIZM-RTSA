import numpy
import os

class scio:
    def __init__(self,fname,arr=None,status='w',compress=None,diff=False):
        if not(compress is None):
            if len(compress)==0:
                compress=None
        self.fid=open(fname,status)
        self.fname=fname
        self.diff=diff
        self.last=None
        self.compress=compress
        self.closed=False

        if arr is None:
            self.dtype=None
            self.shape=None
            self.initialized=False
        else:
            self.dtype=arr.dtype
            self.shape=arr.shape
            self.initialized=True
            self.write_header(arr)
            self.append(arr)

    def __del__(self):
        if self.closed==False:
            print('closing scio file ', self.fname)
            self.fid.flush()        
            self.fid.close()
            self.closed=True
            if not(self.compress is None):
                to_exec=self.compress + ' ' + self.fname
                os.system(to_exec)


    def close(self):
        self.__del__()
    def write_header(self,arr):
        sz=arr.shape
        myvec=numpy.zeros(len(sz)+2,dtype='int32')
        myvec[0]=len(sz)
        if self.diff:
            myvec[0]=-1*myvec[0]
        for i in range(len(sz)):
            myvec[i+1]=sz[i]
        myvec[-1]=dtype2int(arr)
        myvec.tofile(self.fid)

        
    def append(self,arr):
        if self.initialized==False:
            self.dtype=arr.dtype
            self.shape=arr.shape
            self.write_header(arr)
            self.initialized=True

        if (arr.shape==self.shape):
            pass
        else:
            print("shape mismatch in scio.append")       
        if (arr.dtype==self.dtype):
            if (self.diff):
                if self.last is None:
                    arr_use=arr
                else:
                    arr_use=arr-self.last
                self.last=arr.copy()
            else:
                arr_use=arr
            arr_use.tofile(self.fid)
            self.fid.flush()
        else:
            print('dtype mismatch in scio.append on file ', self.fname)
            

def read(fname):
    f=open(fname)
    ndim=numpy.fromfile(f,'int32',1)
    if (ndim<0):
        diff=True
        ndim=-1*ndim
    else:
        diff=False
        
    sz=numpy.fromfile(f,'int32', int(ndim))
    mytype=numpy.fromfile(f,'int32',1)
    vec=numpy.fromfile(f,dtype=int2dtype(mytype))
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
    
def dtype2int(dtype_str):
    
    if (type(dtype_str)!=numpy.dtype):
        dtype_str=dtype_str.dtype

    aa=numpy.zeros(1,dtype='float64')
    if (dtype_str==aa.dtype):
        return 8

    aa=numpy.zeros(1,dtype='float32')
    if (dtype_str==aa.dtype):
        return 4
    

    aa=numpy.zeros(1,dtype='int32')
    if (dtype_str==aa.dtype):
        return -4
    
    aa=numpy.zeros(1,dtype='int64')
    if (dtype_str==aa.dtype):
        return -8

    aa=numpy.zeros(1,dtype='uint32')
    if (dtype_str==aa.dtype):
        return -104

    aa=numpy.zeros(1,dtype='uint64')
    if (dtype_str==aa.dtype):
        return -108
    
    print('unknown dtype')
    return 0

