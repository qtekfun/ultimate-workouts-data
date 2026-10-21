import sys, itertools, traceback
sys.path.insert(0,'.')
from tools_imggen import patterns as PT, figure as F
from tools_imggen.patterns import patterns_a as A
EQ=["none","barbell","dumbbell","kettlebell","cable","machine","band","bar","bench","incline_bench","decline_bench","swiss_ball","mat","sz_bar","box"]
VAR=[[],["incline"],["decline"],["seated"],["standing"],["lying"],["single_arm"],["alternating"],["narrow"],["wide"],["reverse"],["front"],["overhead"],["bodyweight"]]
bad=0
for p in A.PATTERNS:
    for eq in EQ:
        for v in VAR:
            try:
                sp=PT.build_spec(p,eq,v,"quads")
                miss=0
                for ps in sp["poses"]:
                    miss=max(miss,ps.get("_miss",0))
                if sp["poses"][0].get("_front"): 
                    pass
                else:
                    for t in (0.0,0.5,1.0):
                        ps=F.pose_at(sp["poses"],t*(len(sp["poses"])-1))
                        miss=max(miss,ps.get("_miss",0))
                if (hash((p,eq,tuple(v)))%7)==0:
                    F.animate_spec(sp, steps=1, size=96)
                if miss>1.5: print("MISS",p,eq,v,round(miss,1)); bad+=1
            except Exception as e:
                print("ERR",p,eq,v,repr(e)); bad+=1
print("done",bad)
