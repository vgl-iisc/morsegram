import pyms3d
import itertools
import numpy as np
from collections import defaultdict
from python_algorithms.basic.union_find import UF
import math

msc=pyms3d.mscomplex()
msc_file_name='msc_chan_vese_chamf_distance_pers_2.0'
#msc.load('msc_otsu_Depositional_Steel_Air_downsampled_mean_213_256_251_pers_2.0')
#msc.load('msc_chamfer_dist_pers_2.0')
msc.load(msc_file_name)
msc.collect_geom(dim=3,dir=0)
cps_2sad=msc.cps(2)
dim=[251,256,213]
x_max=dim[0]-1
y_max=dim[1]-1
z_max=dim[2]-1
dual_pts=msc.dual_points()


surv_sads=np.loadtxt('surviving_sads'+msc_file_name)

def get_cube_max_val(dual_pt):
	inc_arr=list(itertools.product([0.5,-0.5],repeat=3))
	max_val=100
	#flag=0
	for inc in inc_arr:
		curr_pt=np.add(dual_pt,inc)
		if(curr_pt[0]<x_max and curr_pt[1]<y_max and curr_pt[2]<z_max):
			#flag=1
			curr_val=msc.vert_func(int(curr_pt[0]),int(curr_pt[1]),int(curr_pt[2]))
			if(curr_val<max_val):
				max_val=curr_val
	#print(flag)
	return(max_val)

def get_des_vol(max_id):
	des_geom=msc.des_geom(max_id)
	count=0
	for cube_id in des_geom:
		if(get_cube_max_val(dual_pts[cube_id])>0):
			count+=1
	return count
	
def dia_from_vol(vol):
	dia=(vol*3.0)/(4.0*math.pi)
	dia=dia**(1/3.0)
	return 2.0*dia

cps_max=msc.cps(3)

#point ids
#C. Number
#Vol
#Assoc Radius

def get_cnum_max(max_id):
	count=0
	for sad_id,k in msc.des(max_id):
		if(sad_id in surv_sads):
			count+=1
	return count

max_data_array=[]
for i in range(len(cps_max)):
	max_id=cps_max[i]
	curr_max_data=[]
	co_ords=[x/2.0 for x in msc.cp_cellid(max_id)]
	vol=get_des_vol(max_id)
	dia=dia_from_vol(vol)
	c_num=get_cnum_max(max_id)
	curr_max_data.extend(co_ords)
	curr_max_data.append(vol)
	curr_max_data.append(dia)
	curr_max_data.append(c_num)
	curr_max_data.append(max_id)	
	max_data_array.append(curr_max_data)

np.savetxt('max_data_array_'+msc_file_name,max_data_array)

