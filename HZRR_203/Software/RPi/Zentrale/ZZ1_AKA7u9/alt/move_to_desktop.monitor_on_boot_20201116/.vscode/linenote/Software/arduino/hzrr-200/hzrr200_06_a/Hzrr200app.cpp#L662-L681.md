  
  
  
      // ************** set commands **************************
      // command include parameters to set; starting from 0x20 
      case INT_ACTION_SET_VLFTEMP_FROM_CENTRAL :  // set Vorlauf temperature from Zentrale 0x20
        cp = strtok( s0, " " );
        cp = strtok( NULL, " " );
        f = strtod( cp, &cp0 );
        if( cp0 == s0 ) err0 = 1;
        else           err0 = 0;
        if( err0 > 0 ) {
          stat.tvzOk = 0;
          strcpy( s1, "NAK" );
        }
        else {
          stat.tvz = f;
          stat.tvzOk = par[v].tvzTValid;
          strcpy( s1, "ACK" );
        }
      break;
  
  
  
  
  st.motUsV = 0.0;
  st.motImA = 0.0;
  st.motIMin= 0.0;
  st.motIMax= 0.0;
  st.rTemp  = 20.0;
  st.rMode  = 0;
  for(i=0;i<3;i++){
    st.reg[i].motStart = 0xFF;
    st.reg[i].motDir   = 0;
    st.reg[i].motLimit = 0;
    st.reg[i].dtOpen   = 0;
    st.reg[i].dtClose  = 0;
    st.reg[i].tMotDur  = 0;
    st.reg[i].vorlaufTemp = 0.0;
    st.reg[i].ruecklaufTemp = 0.0;
    st.reg[i].zimmerTemp = 0.0;
    st.reg[i].errReg = 0;
