'''
hr2_net_subs
'''

def get_modules():
    antwort = hkr_cfg.get_heizkreis_config(0,1)
    return( antwort[1] )

def all_mod_regs(mods,regs):
    ''' return list with all modules (m,0) or all regs (m,1)..(m,3)
        from regs input list e.g. [0,1,2,3] '''
    # regs = [0,1,2,3] or part of it
    lAll=[]
    for mod in mods:
        for r in regs:
            lAll.append( (mod,r) )
    print(lAll)
    return lAll



