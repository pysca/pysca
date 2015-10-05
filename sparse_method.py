import pinfwrapper,fullmsa
from multiprocessing import Pool,cpu_count
import numpy as np
import cvxpy as cvx
from scipy import sparse

class entropy():
    def __init__(self, mtx):
        self.mtx = mtx.copy()
        self.mask= self.get_sparse_mask()
        self.M, self.L = mtx.shape
        self.k = mtx.max()+1
        self._nonzero_elems = self.mask.T*self.mask
        self.pool = Pool(cpu_count())

    def get_sparse_mask(self):
        M,L = np.shape(self.mtx)
        k = self.mtx.max()+1
        mask = sparse.lil_matrix((M,L*k))
        for i in range(k):
            mask[:, np.arange(L)*k+i] = np.array(self.mtx==i, dtype=float)
        return sparse.csr_matrix(mask)

    def gradient(self, W, **kw):
        columns = kw.get('columns', np.arange(self.L*self.k))
        M = self.mask.shape[0]
        helper = grad_helper(self.mask, W, columns=columns)
        grad = np.array(self.pool.map(helper, np.arange(M)))
        return grad

    def gradient_descent(self, **kw):
        columns = kw.get('columns', np.arange(self.L*self.k))
        W = kw.get('wo', np.ones(self.M)/float(self.M))
        alpha = kw.get('alpha', 1e-7)
        maxiter = kw.get('maxiter', 100)
        H,T = [],[]
        for i in range(maxiter):
            W = W + alpha*self.gradient(W, columns=columns)
            W = project(W)
            H.append(self(W, columns=columns))
            T.append(W)
        return H,T

    def __call__(self, w, **kw):
        columns = kw.get('columns', np.arange(self.L*self.k))
        W = sparse.csr_matrix(np.diag(w))
        O = self.mask[:,columns].T*W*self.mask
        return np.nansum(O.data*np.log(O.data))

def project(W):
    M = len(W)
    V = cvx.Variable(M)
    p = cvx.Problem(cvx.Minimize(cvx.norm2(V-W)), [cvx.sum_entries(V) == 1., V >=0.])
    try:
        p.solve()
    except:
        p.solve(solver="SCS")

    return np.array(p.variables()[0].value).flatten()

class grad_helper():
    def __init__(self, A, W, **kw):
        self.columns = kw.get('columns', np.arange(A.shape[1]))
        self.A = sparse.csr_matrix(A)
        self.W = sparse.csr_matrix(np.diag(W))
        self.O = self.A[:,self.columns].T*self.W*self.A
        self.O.data = np.log(self.O.data) + 1.
        self.O.data[np.isnan(self.O.data)] = 0.

    def __call__(self, i):
        M = self.A.shape[0]
        w = sparse.csr_matrix((M, M))
        w[i,i] = 1.
        o = self.A[:,self.columns].T*w*self.A
        return -(self.O.multiply(o).sum())
