      #err = us.ser_reset_buffer()
      #lg.log_obj.rr_log(monitor_running = 1, call_from_monitor=1)

      # OLD:
      #answer, repeat = us.ser_obj.ping(modAdr)

      # NEW:
      #repeat = 0


        #while (answer == 8): # serial bus is currently blocked. please wait
        #  answer = us.ser_obj.get_jumpers(modAdr)
        #  ti.sleep(0.5) # dont let the script go nuts..
        #  self.dbg.m("waiting for serial bus...")


        #if self.summer == "W":
        #  self.flVal[self.conAbsIdx+0*4].setText("%5.1f"%(self.vlm0) )
        #  self.flVal[self.conAbsIdx+1*4].setText("%5.1f"%(self.rlm0) )
        #  self.flVal[self.conAbsIdx+2*4].setText("%5.1f"%(self.rls0) )
        #  self.flVal[self.conAbsIdx+3*4].setText("%3.0f%%"%(self.ven0) )
        #elif self.summer == "S":
        #  self.flVal[self.conAbsIdx+0*4].setText("%5.1f"%(self.vlm0) )
        #  self.flVal[self.conAbsIdx+1*4].setText("%5.1f"%(self.rlm0) )
        #  self.flVal[self.conAbsIdx+2*4].setText("%5.1f"%(self.rls0) )
        #  self.flVal[self.conAbsIdx+3*4].setText("%3.0f%%"%(self.ven0) )
    #
        #else: #summer 0 or whatver
        #  self.flVal[self.conAbsIdx+0*4].setText("%5.1f"%(self.vlm0) )
        #  self.flVal[self.conAbsIdx+1*4].setText("%5.1f"%(self.rlm0) )
        #  self.flVal[self.conAbsIdx+2*4].setText("%5.1f"%(self.rls0) )
        #  self.flVal[self.conAbsIdx+3*4].setText("%3.0f%%"%(self.ven0) )

        #if((self.err0!=0) or (self.vlm0==0.0) or (self.rlm0==999.9)) :
        # first check if summer or winter
        #c = ('W','S')
        #using_color = [self.color_error for w in c if (vals[0].lower() != 'w' and vals[0].lower() != 's')]
        #print( "using_color_test:",using_color )



          #while repeat < 3 and not ende:

        #temporary: obsolete... information is coming from

        # OLD:
        #answer = us.ser_obj.get_jumpers(modAdr)

        # NEW:
          #  if e > 0 :
          #    repeat += 1
          #  else:
          #    ende = True

            #self.dbg.m ("type()=",str(type(e)),",e=",str(e),cdb=3)
            #if type(e) is tuple: e = e[0]


              # no valid data received - set all grey and blank

              #test remove later - save pi-power


                # winter mode
                #flVal[conAbsIdx+0*4].setText("%5.1f"%(vle0) )
                #flVal[conAbsIdx+1*4].setText("%5.1f"%(rle0) )


                #if((self.err0!=0) or (self.vlm0==0.0) or (self.rlm0==-127.0)) :
                #  self.fill_rects(self.conAbsIdx,0,4,self.color_error)
                #else:
                #  self.fill_rects(self.conAbsIdx,0,4,self.color_winter)


                # summer mode
                #flVal[conAbsIdx+0*4].setText("%5.1f"%(vle0) )
                #flVal[conAbsIdx+1*4].setText("%5.1f"%(0.0) )
                #flVal[conAbsIdx+2*4].setText("%5.1f"%(0.0) )

                #"%5.1f"%(vlm0) )
                #"%5.1f"%(rlm0) )
                #"%5.1f"%(rls0) )
                #"%3.0f%%"%(ven0)
                #set_texts(conAbsIdx,0,4,color_error)
                #if((self.err0!=0) or (self.vlm0==0.0) or (self.rlm0==-127.0)) :
                #  self.fill_rects(self.conAbsIdx,0,4,self.color_error)
                #else:
                #  self.fill_rects(self.conAbsIdx,0,4,self.color_summer)

                #self.fill_rects(self.conAbsIdx,0,4,self.color_error)
