// SIRGAS 2000 / UTM 23S <-> WGS84 (GRS80), fórmulas de Snyder
const UTM=(()=>{const a=6378137,f=1/298.257222101,k0=0.9996,e2=f*(2-f),ep2=e2/(1-e2),L0=-45*Math.PI/180,FE=500000,FN=10000000;
function inv(E,N){const x=E-FE,y=N-FN,M=y/k0,mu=M/(a*(1-e2/4-3*e2*e2/64-5*e2**3/256)),e1=(1-Math.sqrt(1-e2))/(1+Math.sqrt(1-e2));
const p1=mu+(3*e1/2-27*e1**3/32)*Math.sin(2*mu)+(21*e1*e1/16-55*e1**4/32)*Math.sin(4*mu)+(151*e1**3/96)*Math.sin(6*mu)+(1097*e1**4/512)*Math.sin(8*mu);
const s=Math.sin(p1),c=Math.cos(p1),t=Math.tan(p1),C1=ep2*c*c,T1=t*t,N1=a/Math.sqrt(1-e2*s*s),R1=a*(1-e2)/Math.pow(1-e2*s*s,1.5),D=x/(N1*k0);
const lat=p1-(N1*t/R1)*(D*D/2-(5+3*T1+10*C1-4*C1*C1-9*ep2)*D**4/24+(61+90*T1+298*C1+45*T1*T1-252*ep2-3*C1*C1)*D**6/720);
const lon=L0+(D-(1+2*T1+C1)*D**3/6+(5-2*C1+28*T1-3*C1*C1+8*ep2+24*T1*T1)*D**5/120)/c;return [lat*180/Math.PI,lon*180/Math.PI]}
function fwd(lat,lon){const p=lat*Math.PI/180,l=lon*Math.PI/180,s=Math.sin(p),c=Math.cos(p),t=Math.tan(p),N1=a/Math.sqrt(1-e2*s*s),T=t*t,C=ep2*c*c,A=c*(l-L0);
const M=a*((1-e2/4-3*e2*e2/64-5*e2**3/256)*p-(3*e2/8+3*e2*e2/32+45*e2**3/1024)*Math.sin(2*p)+(15*e2*e2/256+45*e2**3/1024)*Math.sin(4*p)-(35*e2**3/3072)*Math.sin(6*p));
const E=FE+k0*N1*(A+(1-T+C)*A**3/6+(5-18*T+T*T+72*C-58*ep2)*A**5/120);
const Nn=FN+k0*(M+N1*t*(A*A/2+(5-T+9*C+4*C*C)*A**4/24+(61-58*T+T*T+600*C-330*ep2)*A**6/720));return [E,Nn]}
return {inv,fwd}})();
if(typeof module!=='undefined')module.exports=UTM;
