# -*- coding: utf-8 -*-
from ..solver import BC_PR, Solver
from ...tensor_wrapper import Vector, Matrix

class SolverFS_NH_1d(Solver):
    '''
    1D Finite Sum (FS) solver for numerical homogenization
    of multiscale elliptic PDEs of the form 
    -div(k grad u) = f. See parent class Solver for more details.
    '''
    
    def _gen_coefficients(self, PDE, GRD, d, n, h, dim, mode, tau, verb):
        self.iKx0 = Vector.func([GRD.xc], PDE.k0_func, None, 
                                verb, 'iKx0', inv=True).diag()
        self.Kx1  = Vector.func([GRD.xc], PDE.k1_func, None, 
                                verb, 'iKx1').diag()
        self.iKx1 = Vector.func([GRD.xc], PDE.k1_func, None, 
                                verb, 'iKx1', inv=True).diag()
        self.f1   = Vector.func([GRD.xr], PDE.k1_der_func, None,
                                verb, 'f1')
        self.f    = Vector.func([GRD.xr], PDE.f_func, None,
                                verb, 'f')

    def _gen_matrices(self, d, n, h, dim, mode, tau, verb):
        B = Matrix.volterra(d, mode, tau, h)
        self.iBx = Matrix.findif(d, mode, tau, h)
        if self.PDE.bc == BC_PR:      
            E = Matrix.ones(d, mode, tau)
            B = B - h*(E.dot(B) + B.dot(E)) + h*(h+1)/2 * E
            #from ...tensor_wrapper.matrix import toeplitz
            #c = 1.5 + 0.5*h - h*np.arange(n+1, 2*n+1, 1.)
            #r = 0.5 + 0.5*h - h*np.arange(n+1, 1, -1.)
            #B = Matrix(h*toeplitz(c=c, r=r), d, mode, tau)
        self.Bx = B
        
    def _gen_system(self, d, n, h, dim, mode, tau, verb):
        pass
    
    def _gen_solution(self, PDE, LSS, d, n, h, dim, mode, eps, tau, verb):
        f1, f, Bx = self.f1, self.f, self.Bx
        
        ikx0, kx1, ikx1 = self.iKx0.diag(), self.Kx1.diag(), self.iKx1.diag()
        
        #f1 = self.iBx.dot(kx1)
        g = Bx.T.dot(f1) * ikx1
        s = g.sum()/ikx1.sum()
        ux_cell = g - s*ikx1
               
        e = Vector.ones(PDE.d, PDE.mode, PDE.tau)
        Kx_hom = (kx1*(e + ux_cell)).sum()*h**dim
        ikx = 1./Kx_hom * ikx0

        g = Bx.T.dot(f) * ikx
        s = g.sum()/ikx.sum()
        self.ux = g - s*ikx
        self.u  = Bx.dot(self.ux)
        self.ux*= e + ux_cell