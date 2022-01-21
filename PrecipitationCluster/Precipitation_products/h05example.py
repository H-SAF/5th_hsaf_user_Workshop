#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 11 18:12:43 2022

@author: Daniele Casella Paolo Sano', ISAC CNR

# version 1.0

# example script to:
    1 translate some H05 file from GRIB to NetCDF
    2 read the created Netcdf files
    3 plot a png image for each file
    4 save all images as a gif animation
"""


# This section should be modified by the user with the preferred settings 

#---------------------------------------------------------------------------------------
# these numbers set the latitude and longitude limits
latlim=[36,47] #degrees north
lonlim=[6,19]  #degrees east


# set the proper product ID (pid)
# pid='h03'
pid='h05'
# pid='h60'
# pid='h61'


#set input path with grib files (it can be a single file)
grib_path='./h05B'
#set output path where you want the netcdf files
nc_path='./h05B'
# set output path where you want the images
png_path='./h05B'

#set the images extention
imageext='.png'
#set to true if you want a gif to be produced
dogif=True

#---------------------------------------------------------------------------------------
# This section should not be modified by the user (unless you know what you are doing)
import hsafpp



lst1,outpt=hsafpp.listFiles(grib_path,nc_path,ext2find='.grb.gz')

for infilename in lst1:
     xvar=hsafpp.define_main_variable(pid,infilename)
     outfilename=hsafpp.grib2nc(xvar,infilename,latlim,lonlim,outpt)
     print(outfilename +'  processed')
    

lst2,outpt=hsafpp.listFiles(nc_path,png_path,ext2find='.nc') 
lst3=[]

for infilename in lst2:
    xvar=hsafpp.ncfileRead(infilename,xvar)
    outfilename=hsafpp.plotPrecip(xvar,infilename,outpt,imageext,latlim,lonlim)   
    lst3.append(outfilename)
    print(outfilename +'  done')

if dogif:
    outfilegif=hsafpp.makeGif(lst3,outpt)
    print()
    print(outfilegif +'  done')