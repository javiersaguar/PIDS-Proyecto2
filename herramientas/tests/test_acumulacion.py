"""La acumulación debe ponderar colas y ejecutar una sola actualización por grupo."""
import math
from herramientas.entrenamiento import entrenar_epoca


class Imagen:
    def __init__(self,valor):self.valor=valor
    def to(self,device):return self


class Perdida:
    def __init__(self,value,grad,opt):self.value=value;self.grad=grad;self.opt=opt
    def __radd__(self,other):assert other==0;return self
    def __mul__(self,value):return Perdida(self.value*value,self.grad*value,self.opt)
    def backward(self):self.opt.grad+=self.grad
    def item(self):return self.value


class Optimizador:
    def __init__(self):self.theta=1.;self.grad=0.;self.steps=0;self.param_groups=[]
    def zero_grad(self):self.grad=0.
    def step(self):self.theta-=.01*self.grad;self.steps+=1


class Modelo:
    def __init__(self,opt):self.opt=opt
    def train(self):return self
    def __call__(self,images,targets):
        ds=[self.opt.theta-im.valor for im in images]
        return {'loss':Perdida(sum(d*d for d in ds)/len(ds),2*sum(ds)/len(ds),self.opt)}


def correr(grupos,acumulacion):
    opt=Optimizador()
    loader=[([Imagen(x) for x in xs],[{} for _ in xs]) for xs in grupos]
    loss=entrenar_epoca(Modelo(opt),loader,'cpu',opt,lambda t,d:t,lambda *a,**k:None,acumulacion)
    return opt,loss


def test_mismo_lote_efectivo_y_cola_sin_dividir_de_mas():
    a,_=correr([list(range(8)),[8]],1)
    b,loss=correr([list(range(4)),list(range(4,8)),[8]],2)
    assert a.steps==b.steps==2 and len(loss)==3
    assert math.isclose(a.theta,b.theta,abs_tol=1e-12)


def test_microbatches_de_distinta_longitud_ponderados_por_imagen():
    a,_=correr([[1,2,3,8,9]],1)
    b,_=correr([[1,2,3],[8,9]],2)
    assert a.steps==b.steps==1
    assert math.isclose(a.theta,b.theta,abs_tol=1e-12)
