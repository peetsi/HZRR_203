






import inspect
import time

class Test:

    def __init__(self):
        self.__make_deep()
        pass

    def pr( self, inp:tuple ):
        m = inp
        if not type(m) == type((tuple())): m = (m,)
        clv = inspect.currentframe().f_back.f_locals.items()
        if len(m) == 1: return print("{ '%s' : '%s' }"%(str(clv),str(m)))
        _ef = [x for x in m if not [(x in m), print('x in m:',x in m,"x:",x,"m:",m)]]
        m = m[0] if (_ef == list()) else _ef
        #print("m:",m)
        #print("_ef:",_ef)
        _cc = [x for x in clv if not x == 'self']
        _str = 'dict("{"'+ str(_cc) +''":"''+ str(m) +'"}")'
        #print("_str:",_str)
        #print("clv:m ->(",clv, ":", m, ')')
        #_l = ([x for x, v in clv if v is m])
        #_fn= _l
        #_fo=_fn
        _r = "{"
        for _w in clv:
            _r += f' "{_w[0]}":"{_w[1]}", '
            print("_w:",_w)
        _r = _r[:-2] + "}"
        #_r = dict(_r)
        #print("_r:",_r)
        #_r = dir(_r)
        #print(_r)
        return print(_r)

    def __unpack(self,*args):
        if len(args) < 2: return args[0]
        return [x for x in args]

    def __has_attr_and_callable(self, o, do:str):
        if (self.__has_attr(o,do) and self.__is_callable(o,do)): return True
        return False

    def __has_attr(self, o, do:str):
        return (hasattr(o, do))

    def __is_callable(self, o, do:str):
        return (callable(getattr(o, do)))

    def __nest_classes(self,c):
        _unpack_test = self.__unpack(c)
        self.pr(_unpack_test)
        if not type(c) == type((tuple())): c = (c,'')
        _mcmd   =   c[0]
        _type   =   type("class", (), {})
        __self  =   'self'
        _deeper =   __self
        _ldeeper=   _deeper

        if (len(c) == 1):     #   single add
            _deeper = 'self.'+c[0]
            try:
                _e = f"setattr({__self}, '{_mcmd}', '{_type}')"
                print("debug _e:",_e)
                exec(_e)
                print("__nest_classes success:",_e)
                print("self.__has_attr:",self.__has_attr(self))
                return 0
            except Exception as e:
                print("__nest_classes error:",e)
                print("__nest_classes input:",str(c))
                return 1

        else:               #   multi add
            for w in c:
                _w          =   '.' + w
                _ldeeper    =   _deeper
                _deeper    +=   _w
                _obj        =   __self if (_deeper == __self+_w) else _ldeeper
                try:
                    _e      =   f"setattr({_obj}, '{w}', '{_type}')"
                    print("debug _e:",_e)
                    exec(_e)
                    print("__nest_classes success:",_e)
                    print("self.__has_attr:",self.__has_attr(_obj,w))
                    return 0
                except Exception as e:
                    print("__nest_classes error:",e)
                    print("__nest_classes input:",str(c))
                    return 2

    def __make_deep(self):

        single_nest ="single_nest"
        self.__nest_classes(single_nest)
        print(dir(self))

        _nest_by = ('system','value','nest','deeper','and','set''val')
        self.__nest_classes(_nest_by)
        print('multi nest:',dir(self))

        setattr(self,'object',"1111111111111")

        _ty = type("Test", (), {} )
        setattr(self, 'second', _ty)
        setattr(self.second, 'third', _ty)
        _p   = getattr(self,'second')
        _p2  = self.second.third
        self.pr((_p,_p2))
        #exit(0)
        return
        setattr(self, 'third.fourth.firth', _ty)
        #setattr(self.third.fourth.firth, 'fifth_val', 0)
        _p = getattr(self,'')
        self.pr(_p)
        #setattr(cls, 'Inner', inner1)


        _se= 'self'
        _c = "setattr( "
        _t = ('first','second','third')
        _i = "."
        for w in _t:
            _i += w+"."
            #_s = _se + _i + _c
            _s = _c  + _se + _i[:-1] + ', "' + w + '", '+ _ty +' )'
            exec(_s)

        getattr(self,'object')
        getattr(self,'object')

        self.object.__setattr__('n',"1111111111111")
        self.__setattr__('object',"1111111111111")

    def ga(self,n):
        try:
            return self.__getattribute__('object')
        except:
            print("error getattr:",n)
t = Test()

x = dir(t)

print(x)

y = t.ga('object')


if __name__ == "__main__":
    pass


    #x = 10
    #mi = 2
    #ma = 8
    #print( "x > mi < ma:", [x > mi < ma] )
    #if (x >mi < ma):
    #    print("true")
    #else:
    #    print("false")