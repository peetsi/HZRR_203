
def g(c):
    print(c)

if __name__ == "__main__":
    st =                     ('set_fast_mode,mod,int',
                            'get_milisec,mod',
                            'cpy_eep2ram,mod',
                            'cpy_ram2eep,mod',
                            'wd_halt_reset,mod',
                            'clr_eep,mod',
                            'check_motor,mod,reg',
                            'calib_valve,modAdr,reg',
                            'motor_off,modAdr,reg',
                            'get_motor_current,mod',
                            'lcd_backlight,mod,int',
                            'get_jumpers,mod',
                            'change_param,str,reg,name,float',
                            'get_param,mod,reg',
                            'send_param,mod,reg')
    a = ""
    b = ""
    c = ""
    for x in st:
        a=    "'"+x.split(",")[0]+"'"             +": self.help.r('"+x+"','"+x.replace('mod',"4",-1).replace('reg',"1",-1).replace('float',"77.0,",-1)+"',\n"
        b=    "'"+x.split(",")[0]+ "MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),"
        c+= a + b
    g(c.replace('\n','%__ENTER__%'))

