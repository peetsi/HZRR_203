



class hz_rr_Terminal_defines:

    def __init__(self):
        self.__first_distance=10
        self.__hfirst_dist=self.__first_distance/2
        self.__line_length=65#int(cg.conf_obj.r('Terminal','line_length',65))
        self.__ln="\n"
        self.__call_mask =  "%__CALLER__%"
        self.__usage_mask = "%__USAGE__%"
        self.__usage_expl = "%__EXPLANATION__%"
        self.__new_line_appender = self._r('-',self.__line_length/3) + "|" + self._r(' ',self.__hfirst_dist)
        self.__usage_buf = ""
        self.__expl_buf = ""
        self.mask = self.__ln + \
                    self._r(' ',self.__hfirst_dist)+ '[CALL - HELP]'+ self.__ln+ \
                    self._r(' ',self.__first_distance) + "+" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r(' ',self.__hfirst_dist) + "[" + self.__call_mask + "]" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r(' ',self.__hfirst_dist) + "[USAGE]" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r('-',self.__line_length) + self.__ln + \
                    self.__usage_mask + \
                    self._r(' ',self.__first_distance)+ "|" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self._r(' ',self.__hfirst_dist) + "[EXPLANATION]" + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self._r('-',self.__line_length) + self.__ln + \
                    self.__usage_expl  + \
                    self._r(' ',self.__first_distance) + "|" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self.__ln + \
                    self._r(' ',self.__first_distance) + "+" + self._r('-',self.__line_length) + self.__ln

    def r(self,caller,usage:str,explanation):
        if usage.find(self.__ln): # multi line usage
            t = usage.split(self.__ln)
            for x in t:
                self.__usage_buf += self.__new_line_appender + x + self.__ln
            usage = self.__usage_buf
        else:
            usage = self.__new_line_appender + usage + self.__ln
        _rbl = 0
        if explanation.find(self.__ln): # multi line usage
            _store=""
            t = explanation.split(self.__ln)
            for x in t:
                _store = self.__expl_buf
                if _rbl < 1:
                    self.__expl_buf += self.__new_line_appender + x + self.__ln
                else:
                    self.__expl_buf += self.__new_line_appender.replace('-',' ') + x + self.__ln
                _rbl += 1
            self.__expl_buf = _store + self.__new_line_appender + x + self.__ln
            explanation = self.__expl_buf
        else:
            explanation = self.__new_line_appender + explanation + self.__ln

        r = self.mask.replace(self.__call_mask, caller).replace(self.__usage_mask,usage).replace(self.__usage_expl,explanation)
        self.__init__()
        return r

    def _r(self, v,r):
        buf= ""
        for i in range(int(r)):
            buf += str(v)
        return buf



if __name__ == "__main__":
    td = hz_rr_Terminal_defines()
    x = td.r('read_stat', 'int,int', 'meh blablabla meh blablabla')
    print(x)
