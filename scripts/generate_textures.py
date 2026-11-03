from PIL import Image, ImageDraw
from pathlib import Path
import random, base64, zlib

random.seed(76)
blob = zlib.decompress(base64.b85decode('c-mc7Yj7LY6}EP@k}ONwmsYFyN~`BeTCLu1OR{CjFIl$Y_!YlM9LG*<f)f%u4}u8}CJ$a2k~Aei0x5JT(-sCwA<WPzp-fwtb~^2^PW!jh{$x7vyT@{qGQD#~vwQV@=brnWbI)Ffqcyl4<2Z-M?T$qviD)DRCWSLnI2Q>=1z%K>qM{fU1Su2(q|@Q#oxH6zf`LFJ9L~n$lG84j*$8LN`Q62!uNd?WB&BLJl=iw@2EBtO!#*$I?KV5dap1?t*=-c*VHq1m0CJ(f>-hN4>Dkfa6GL;=;^9UWW+uwnIB$<QtP!`<<#Jgp7OTY?@cGQR)@L#l0^Z?VVy03!Iy!K6ZtwQ;%!Q@tBg3^9j~}{wVg1J!PxmLngGs3*`nz&jQ)}=}r(iYrM1qIvJy(wIzj12ijja=Ro<0G@>+6S~S)O@w>%?2z8<$q*W-9r)N`AIdm>Q@W46MOmU>Ig!U**V1?_6)`k%6x9?%Z^5>HVwcZ*Q)>d*$rwn`<{uuPhDM)F@)sX^h&AsKa`oUSnBSuV-kQKDcLaZER4BVVF!Nm&p_;GT&Q-b>DjC<lU_kXXp0@t;V(oLxrMwze^HBG(}Ss)#&Pk*LFE7Yil#IMx|1TwzUlxlGjfzUteFIt94?sHu!6GbyX&lf&ZY{Ff&*a1A^UdpQ-o8U7P}up)y&qScFKv`|g{;Sm>Qgr$2e+($%#C1+zhmB1)O;+i$-K6WZ~lczkTIn$MUmmW`RwgT>TLL`aZ2QjX#XV#DN5&W(P0>(Z}ozwp!Np18a`Jt_%N16{TljucZHQ^RA$bUGqxwD{u4!1`q4#8742>zvNTB$~W<Xx~pRpMG=e@fVLRoL`(eHc@|NV|k&Jnn_FB2ga>>N+*|_%@(yr$8#L5=`a%7<x=|D#i@{5)f9c>#Z-p^+guns*ysT%UO2We5D`}TIujlTygE!qf}%Tg1f^&EP9C=7HZkXy_RUtZ-J*AMX&Usob>Zae&z=E!w;o$C>8Wd{jtEX0jUwStnD_W6XCCPtXoP%%O{q}G+U7?3hbo1Di~Hqk&jYts%r<J}hY7m1ecER=^?U3Vh7mkI1CE<;oN8B1rNc=*p;2IfK@jBb)e8y?+ogaLSu0I(QQ-B&N+qK}5SrF=MkAqA5*VgJk>QBH=C%7c%l{}XLu9gD)2iEZoGItBt1!&UvIbm>D;1Pd(IH0@oOv!8y197_V6C-e4_Ro-E<L_faoJ2NrM6vVqDY-mVbFBgX;R;z1}70KduFoEn~l++4}Cy^LZ!4CJ%NMUve%(RQKCa_Byqq4(Q7fn5!TA(u-}r|&>a&mpFIXF3~8B6R`1F$PK-2zo}AOtj$uHw=_wmc1?-lv(<WF=5CDjvk)w0@#O*6jj`nvCl=HwH?dxvV%GWklGBn|$35`l=XK0s+^_W=;fm=x&xDnp&HW?_5dL|xta<;iJ-hg71BeM5yUM@<3wR(3@PXf_I5l)t|(v-`{*a#h|P(birGwZjS?0PC?Hx2XFg-U*NajMywym@xjfywhGy`92Y0=F@=8pGOA)Pn0moF(ewj5@6XMO%AB;2~=^toIi;$NRVEnkR<3b1ZGtKm$PJD1xD=R;A*=1Bxac=KUE7`V2$j-_Pd5)PP+(w>B*KIkgJXp_Zf2Ko-ks8;PG>n%hmp?k}jCk%F9=y>Vu>H{gOWtQ3Jmks(NsBK)}aj~~CI?NDbTq1`M1<=mqO5ACgIac#*BWg{0IRu`*>^QBf`{T}Y^?Ng$M|Mk1C0WvKGH<srg-#_ux>>d%<?i5BxyPYE9Zby)_SZT6P;OFB(KdHNS`z13?Rx`0@9$QFSjSW8^GBKp40~8}vDi95n*R`u)iL{kHkPL0jj=Z!ob7g7ja5XP#)PjLhK-s8NI(56>VzM)oiNv9p33a;`D%oZ%dbn<ZFZrC1ARDfgKajLtfkD9lrpIRb;KsA3m**2=;LG>kfbB#4y@m8dy_yn*-~Rm0a!-y_w?icJa46OfpE)?$sFwe9?_CSafRZb-V=tULo(y>3zp=egh(nsl4)tszbhIb8Hr8LsCcgUMM?R+=e6H=EynX3hn73WuI6NNm_$)>i*NsK|Qvr7d*W~@~k8WL&ygWp8aCG3>6G!z3;+3OKzY_`!6mv6VH*all=6&(dt4}<7;n3vf{=Ju1=bkz+=Eme13Xho>*d63WC6`MkW+^KjtLCmO@4I&Fz|Hlg=T~M=?&%FG;e0V1sY7=@94HtZ8Hv!X_jj(A5-0mRPt{9n)!afxnh?EctFGXj!uB;gok8wUtEN)oh~yhjhQ^X&L-N;r&Z5JD!bbr?B;F388c7`lfXa~FvTSuK*~1<pM^Uv(xmyMnnuJ6^%)o6S|2uYy8M1(&46Y4wR`6+|2@FBOcEArj!$S+UgM_oW%j!@nv??Wh^>)GEhbd6GTA@(N<thcHhF+)H*;fmRU^{Mi7j4xBh7oFYyFvkNfj2S`Cj+Nd{{P4w^;AmeMHW3-;O&37|9PWc-}%Z?G)d8AFaPpW=f1vwAMQhXy`I)HJwfl@Z0f6zesT5UMb^OT4QxFj#Tokc_SWw|{IJ>FV=$Wc<dYJvtqR_c@7}rp*=M}RHxv&`I&I10oawKA^7dQLz5IhN-ku=wo{+C33I|6=?)>o8E~hQ6C;OtIqUcX~U5lg5iql>&G6Sh-IUGp)Tv@?Wwi<^sv4M2781iTQ?v&5fWid7jsouC$2>Jj3lZ~*@%%{4-ft=teg#2m08*We|`6Mg^Go2xS!oxq(*9DiQvMA(%;^AX%=WMM6n6enix}5<6k9(Z^DxKgN@M(uVKoNi$D`j_BVIj;i5sOLUIRNa27h>qB-6A?{!?|Q%G6Gk=pq@^8oPy2V$R>KifdH-*C<219>Ooivu1|fn+Q0wx&yD%nD9?ega3A~p(|dpW;`4eU7Pgug)_7>~&_BNZ>h<&IYEr;Q5ghOS>tFu-yH{^bcXy5#Gkk}7^ZeG|zx-mY(zPd(n5`Cr4E>vXpZ@IXiy4X-NyVlson4~v$=y4X<wAncHDcmaS8k+`dU|!a771p|#%4M`S<X%OboM4AgXw6>!~$!qm;rIhQlODbWbNi=CO%Qhjuz5AF|nSB^+*8_VWOOCq~q0?Sc!x{=Vm?$PKMI4u1K&a8tRsU1Ig%QcYZjVEQJNYR3gE?gfs$)i;DSxw<x&573kI*7CLR_jNnN-?e%ONX6mVEMo)p%5fj@N7YEa^dL|yxX?PPW8V!|z2Z%74WN5h@gEns=iIm^npNQmb7MN+-&S+OEj9Sfq0K$kg6#'))
pieces = {}
offset = 0
for name, size in [('face',(20,23)),('jaw',(16,7)),('torso',(14,14)),('armleft',(6,20)),('armright',(6,20))]:
    n = size[0]*size[1]*3
    pieces[name] = Image.frombytes('RGB',size,blob[offset:offset+n])
    offset += n

out = Path('src/main/resources/assets/voidmaw/textures')
(out/'entity').mkdir(parents=True, exist_ok=True)
(out/'item').mkdir(parents=True, exist_ok=True)
tex=Image.new('RGBA',(256,128),(49,35,35,255))
d=ImageDraw.Draw(tex)
for y in range(128):
    for x in range(256):
        v=random.randrange(-17,17)
        r=max(10,min(240,91+v))
        g=max(8,min(240,67+int(v*.85)))
        b=max(8,min(240,68+int(v*.8)))
        tex.putpixel((x,y),(r,g,b,255))
tex.paste(pieces['face'],(12,12))
back=Image.new('RGB',(20,23),(60,44,44))
bd=ImageDraw.Draw(back)
for yy in range(23):
    for xx in range(20):
        rv=random.randint(-10,12)
        basecol=(57 if yy<5 else 92,43 if yy<5 else 70,42 if yy<5 else 69)
        bd.point((xx,yy),fill=tuple(max(0,c+rv) for c in basecol))
tex.paste(back,(44,12))
for x0 in (0,32):
    for y in range(12,35):
        for x in range(x0,x0+12):
            v=random.randrange(-12,12)
            raw=(67,45,49) if y<16 else (110,81,80)
            tex.putpixel((x,y),(*[max(0,min(255,c+v)) for c in raw],255))
tex.paste(pieces['jaw'],(75,5))
tex.paste(pieces['torso'],(128,8))
tex.paste(pieces['armleft'],(7,51))
tex.paste(pieces['armright'],(42,51))
for ox in (74,102):
    for y in range(50,62):
        for x in range(ox,ox+6):
            v=random.randint(-10,10)
            tex.putpixel((x,y),(51+v,41+v,42+v,255))
d.rectangle((184,0,220,24),fill=(225,216,197,255))
for i in range(150):
    x=random.randint(184,220)
    y=random.randint(0,24)
    d.point((x,y),fill=random.choice([(205,195,176,255),(237,226,209,255),(183,166,152,255)]))
d.rectangle((19,20,19,20),fill=(246,246,241,255))
d.rectangle((27,20,27,20),fill=(245,245,241,255))
tex.save(out/'entity/void_maw.png')

egg=Image.new('RGBA',(32,32),(0,0,0,0))
e=ImageDraw.Draw(egg)
widths={2:3,3:5,4:7,5:8,6:9,7:10,8:11,9:11,10:12,11:12,12:12,13:12,14:12,15:12,16:12,17:12,18:12,19:11,20:11,21:11,22:10,23:9,24:8,25:7,26:6,27:5,28:3}
for yy,w in widths.items():
    for xx in range(16-w,17+w):
        if xx<0 or xx>=32:
            continue
        shade=10 if xx>21 else 0
        c=(96-shade,70-shade,72-shade,255)
        if yy<8:
            c=(64,47,48,255)
        egg.putpixel((xx,yy),c)
for rec,color in [((7,11,13,16),(10,8,12,255)),((19,11,25,16),(10,8,12,255)),((8,18,24,26),(15,9,11,255)),((9,17,23,18),(96,29,28,255))]:
    e.rectangle(rec,fill=color)
e.rectangle((10,13,10,13),fill=(255,250,234,255))
e.rectangle((22,13,22,13),fill=(255,250,234,255))
for x in (9,12,15,19,23):
    e.rectangle((x,18,x+1,20+(x%2)),fill=(230,222,198,255))
for x in (11,15,20):
    e.rectangle((x,24,x+1,26),fill=(227,218,191,255))
e.line((9,6,8,10),fill=(163,128,128,255),width=2)
egg.save(out/'item/void_maw_spawn_egg.png')
print('Generated monster and egg textures')
