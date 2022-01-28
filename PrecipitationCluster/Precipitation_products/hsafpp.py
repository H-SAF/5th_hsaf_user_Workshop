#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 11 16:51:12 2022

@author: Daniele Casella Paolo Sano', ISAC CNR

# version 1.01

# hsafpp contains functions to read and plot H SAF precipitation products

# version 1.01 : bug fixed for h03 and h05 products


Notes for future improvements:
    - extract lat,lon from Netcdf in geostationary grid
    - include different projections for mapping
    - extract data for a given basin with a shapefile
    - plot timeseries
"""

import pygrib
import numpy as np
from sys import argv
from netCDF4 import Dataset    # Note: python is case-sensitive!
from netCDF4 import stringtochar 
import gzip
import glob
import os

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap 
from mpl_toolkits.basemap import Basemap

def define_main_variable(pid,infilename):
    
    if pid=='auto':
        pid=os.path.basename(infilename)[0:3]
        
    xvar={}
    
        
    xvar['pid']=pid
    xvar['value']=0 
    xvar['qind']=0
    xvar['lat']=[] 
    xvar['lon']=[] 
    xvar['time']=0 
    xvar['attributes']={}
    if pid=='h03' or pid=='h03B':       
        xvar['shortname']='rainRate'
        xvar['bias']=3600  #multiplicative bias
        xvar['unit']='mm/h'  # it is in kg/m^2/s in grib files   *3600 becomes  mm/h
        xvar['label']='Instantaneous Precipitation Rate'
        xvar['standard_name']='Instantaneous_rain_rate'
        xvar['gribName']='Instantaneous rain rate'
        xvar['ncName']='rr'
        xvar['stdRange']=[0, 20]
        
    elif pid=='h05' or pid=='h05B' or pid=='h61' or pid=='h90' or pid=='h64':
        xvar['shortname']='rain'
        xvar['bias']=1
        xvar['unit']='mm'
        xvar['label']='Accumulated Precipitation '
        xvar['standard_name']='Accumulated_rain'
        xvar['gribName']='Estimated precipitation'
        xvar['ncName']='acc_rr'     
        xvar['stdRange']=[0, 50]
        
    elif pid=='h60' or pid=='h63' or pid=='h67' or pid=='h68':
        xvar['shortname']='rainRate'
        xvar['bias']=1  #multiplicative bias
        xvar['unit']='mm/h'  
        xvar['label']='Instantaneous Precipitation Rate'
        xvar['standard_name']='Instantaneous_rain_rate'
        xvar['gribName']='Instantaneous rain rate'
        xvar['ncName']='rr'
        xvar['stdRange']=[0, 30]

    elif pid=='h01' or pid=='h02' or pid=='h17' or pid=='h18'or pid=='h20':
        xvar['shortname']='rainRate'
        xvar['bias']=1  #multiplicative bias
        xvar['unit']='mm/h'  
        xvar['label']='Instantaneous Precipitation Rate'
        xvar['standard_name']='Instantaneous_rain_rate'
        xvar['gribName']='Instantaneous rain rate'
        xvar['ncName']='rr'
        xvar['stdRange']=[0, 30]
        
    return xvar
    
def find_lmits(xvar,latmin,latmax,lonmin,lonmax):
    #this functions finds the pixels corresponding to the corners of the selected lat-lon area
    
    lats=xvar['lat']
    lons=xvar['lon']
    x=xvar['values']
    a=np.where(np.logical_and(np.logical_and(lats>latmin,lats<latmax),np.logical_and(lons>lonmin,lons<lonmax)) )
    lims=[min(a[0]),max(a[0]),min(a[1]),max(a[1])]
    lat=lats[lims[0]:lims[1],lims[2]:lims[3]]
    lon=lons[lims[0]:lims[1],lims[2]:lims[3]]
    x1=x[lims[0]:lims[1],lims[2]:lims[3]]
    xvar['lat']=lat
    xvar['lon']=lon
    xvar['values'] =x1
    if len(xvar['qind'])>1:
        xvar['qind']=xvar['qind'][lims[0]:lims[1],lims[2]:lims[3]]
    return xvar



def grib2nc(xvar,infilename,latlim,lonlim,outpt):
    #translate a grib file to netcdf
    if infilename[-3:] == '.gz':
        infilename=gunzip(infilename)
    xvar=read_grib(infilename,xvar)
    xvar=find_lmits(xvar,latlim[0],latlim[1],lonlim[0],lonlim[1])    
    outfilename=outpt+os.path.basename(infilename[0:-4])+'.nc'    
    ncfileWrite(outfilename,xvar)
    return outfilename

def read_grib(infilename,xvar):
    #reads a grib file
    
    grbs = pygrib.open(infilename)  
    # useful for printing grib messages    
    grbs.seek(0)
    # for grb in grbs:
    #     print(grb)
        
    # grbs.seek(0)
    # grb1 = grbs.read(1)[0]
    
    grb1 = grbs.select(name=xvar['gribName'])[0]
    qind = grbs.read(1)[0]
    
    lats, lons = grb1.latlons()
    lats=-lats #this is needed
    xvar['lat']=lats
    xvar['lon']=lons
    xvar['values']=grb1.values
    xvar['qind']=qind.values
    xvar['time']=grb1.analDate.isoformat()
    d1=grb1.keys()
    att={}
    for d in d1:
        if d=='analDate' or  d=='validDate' :
            att[d]=grb1.analDate.isoformat()
        elif d=='codedValues' or d=='values' or d=='numberOfSection' or d=='sectionNumber' or d=='name':
            d=d;
        else:
            att[d]=grb1[d]
    att['parameterUnits']=xvar['unit']
    att['units']=xvar['unit']
    att['unitsECMF']=xvar['unit']
    xvar['attributes']=att
    
    if (xvar['pid']=='h03' or xvar['pid']=='h05') and np.shape(xvar['lat'])==(900,1900):
        ncfile1 = Dataset('h03coord.nc','r')
        lat=ncfile1['lat'][:]
        lon=ncfile1['lon'][:]
        xvar['lat'    ]=lat
        xvar['lon'    ]=lon
    return xvar

def ncfileWrite(outfilename,xvar):
    #writes a Netcdf file
    rr=xvar['values']*xvar['bias']
    
    sz=rr.shape
    ncfile = Dataset(outfilename,mode='w',format='NETCDF4') 
    ncfile.createDimension('x', sz[0])     # latitude axis
    ncfile.createDimension('y', sz[1])    # longitude axis
    ncfile.createDimension('t', len(xvar['time'])) # unlimited axis (can be appended to).
    
    # Define two variables with the same names as dimensions,
    # a conventional way to define "coordinate variables".
    lat = ncfile.createVariable('lat', np.float32, ('x','y'),zlib=True)
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lat[:,:]=xvar['lat']
    lon = ncfile.createVariable('lon', np.float32, ('x','y'),zlib=True)
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    lon[:,:]=xvar['lon']
    time = ncfile.createVariable('time', 'S1', ('t'),zlib=True)
    time.units = 'isoformat'
    time.long_name = 'time'
    time[:]= stringtochar(np.array([xvar['time']], 'S'))
    # Define a 3D variable to hold the data
    rainRate = ncfile.createVariable(xvar['ncName'],np.float32,('x','y')) # note: unlimited dimension is leftmost
    rainRate.units = xvar['unit']
    rainRate.standard_name = xvar['standard_name']
    rainRate[:,:]=rr
    
    qind = ncfile.createVariable('qind',np.float32,('x','y')) # note: unlimited dimension is leftmost
    #qind.units = xvar['unit']
    qind.standard_name = 'pixel quality index'
    qind.range = [0,100]
    qind[:,:]=xvar['qind']
    
    att=xvar['attributes']
    for d in att.keys():
        setattr(ncfile,d,att[d] )
        
    
    ncfile.close();

def ncfileRead(inputfilename,xvar):
    #reads a netcdf file
    if inputfilename[-3:] == '.gz':
        inputfilename=gunzip(inputfilename)
        
    ncfile = Dataset(inputfilename,'r')
    if xvar['pid'][0:3]=='h03' or xvar['pid'][0:3]=='h05' :
        
        latitude=ncfile['lat'][:]
        longitude=ncfile['lon'][:]
        rainRate=ncfile[xvar['ncName']][:]
        time=ncfile['time'][...].tostring().decode()
        
        xvar['lat'    ]=  latitude
        xvar['lon'    ]=  longitude
        xvar['values' ]=  rainRate
        xvar['time'   ]=  time
        
    elif xvar['pid'][0:3]=='h64':
        
        latitude=ncfile['lat'][:]
        longitude=ncfile['lon'][:]
        rainRate=ncfile[xvar['ncName']][:]
        atts=ncfile.__dict__
        time=atts['end_of_accumulation_time']
        lon,lat=np.meshgrid(longitude,latitude)
        xvar['lat'    ]=  np.float32(lat.filled())
        xvar['lon'    ]=  np.float32(lon.filled())
        xvar['values' ]=  np.float32(rainRate.filled())
        
        xvar['time'   ]=  time
        
    elif xvar['pid'][0:3]=='h67':
        
        latitude=ncfile['lat'][:]
        longitude=ncfile['lon'][:]
        rainRate=ncfile[xvar['ncName']][:]
        atts=ncfile.__dict__
        time=atts['end_of_average_time']
        lon,lat=np.meshgrid(longitude,latitude)
        xvar['lat'    ]=  np.float32(lat.filled())
        xvar['lon'    ]=  np.float32(lon.filled())
        xvar['values' ]=  np.float32(rainRate.filled())
        
        xvar['time'   ]=  time        
        
    elif xvar['pid'][0:3]=='h01' or xvar['pid'][0:3]=='h02' or xvar['pid'][0:3]=='h17' or xvar['pid'][0:3]=='h18' or xvar['pid'][0:3]=='h20'  :
        
        lat=ncfile['lat'][:]
        lon=ncfile['lon'][:]
        rainRate=ncfile[xvar['ncName']][:]

        
        xvar['lat'    ]=  np.float32(lat.filled())
        xvar['lon'    ]=  np.float32(lon.filled())
        xvar['values' ]=  np.float32(rainRate.filled())
        
    elif xvar['pid'][0:3]=='h68':
          
          latitude=ncfile['lat'][:]
          longitude=ncfile['lon'][:]
          rainRate=ncfile[xvar['ncName']][:]

          lon,lat=np.meshgrid(longitude,latitude)
          xvar['lat'    ]=  np.float32(lat.filled())
          xvar['lon'    ]=  np.float32(lon.filled())
          xvar['values' ]=  np.float32(rainRate.filled())
        
    else:
        xvar['values' ]=ncfile[xvar['ncName']][:]
        # xvar['lat'    ]=  lat
        # xvar['lon'    ]=  lon
    atts=ncfile.__dict__
    if ('satellite_altitude' in atts.keys() ) and ('satellite_altitude_unit' in atts.keys() ):
        if atts['satellite_altitude_unit' ]=='m':
            xvar['satellite_altitude']=float(atts['satellite_altitude'])
        elif atts['satellite_altitude_unit' ]=='Km':
            xvar['satellite_altitude']=float(atts['satellite_altitude'])*1000
    else:
        xvar['satellite_altitude']=35785831.00
    if ('r_eq' in atts.keys() ) and ('r_eq_unit' in atts.keys() ):
        if atts['r_eq_unit' ]=='m':
            xvar['r_eq']=float(atts['r_eq'])
        elif atts['r_eq_unit' ]=='Km':
            xvar['r_eq']=float(atts['r_eq'])*1000
    else:
        xvar['r_eq']=6378137.00
        
    if ('r_pol' in atts.keys() ) and ('r_pol_unit' in atts.keys() ):
        if atts['r_pol_unit' ]=='m':
            xvar['r_pol']=float(atts['r_pol'])
        elif atts['r_pol_unit' ]=='Km':
            xvar['r_pol']=float(atts['r_pol'])*1000
    else:
        xvar['r_pol']=6356752.3142
    if ('sub-satellite_longitude' in atts.keys() )    :
        xvar['sub-satellite_longitude']=float(atts['sub-satellite_longitude'][0:-2])
    else:
        xvar['sub-satellite_longitude']=0.0
        
    xvar['file']=os.path.basename(inputfilename)
    return xvar



def myCbar():
    from matplotlib import cm
    from matplotlib.colors import ListedColormap, LinearSegmentedColormap
    jet = cm.get_cmap('jet', 256)
    newcolors = jet(np.linspace(0, 1, 256))
    #white = np.array([1, 1, 1, 1])
    #newcolors[:1, :] = white
    newcmp = ListedColormap(newcolors)
    newcmp.set_under(np.array([1, 1, 1, 1]))
    return newcmp

def setParallelsMeridians(latcorners,loncorners,m):
    if len(latcorners)==2:
        if latcorners[1]-latcorners[0]>=40:
            dparal=10
        elif latcorners[1]-latcorners[0]>=0:
            dparal=2
        parallels = np.arange(latcorners[0],latcorners[1],dparal)
    else:
        parallels= np.arange(-90,90,10)
    m.drawparallels(parallels)
    
    if len(loncorners)==2:
        if loncorners[1]-loncorners[0]>=40:
            dmerid=10
        elif loncorners[1]-loncorners[0]>=0:
            dmerid=2
        meridians = np.arange(loncorners[0],loncorners[1],dmerid)
    else:
        meridians= np.arange(-180,180,10)        
    
    
    m.drawmeridians(meridians) 
        


def plotPrecip(xvar,infilename,outpt,imageext,latcorners,loncorners):
    if len(xvar['lat'])==0:
        fig=plotPrecipGEOS(xvar,latcorners,loncorners)
    else :
        fig=plotPrecipLatLon(xvar,latcorners,loncorners)
        
    outfilename=outpt+os.path.basename(infilename)[:-3]+imageext
    fig.savefig(outfilename)
    return outfilename


def plotPrecipGEOS(xvar,latcorners,loncorners):
    
    #plot a single file to a map

    colorAxisMin=xvar['stdRange'][0]
    colorAxisMax=xvar['stdRange'][1]

    # create figure and axes instances
    fig = plt.figure(figsize=(8,8))
    
    m = Basemap(projection='geos',
            rsphere=(xvar['r_eq'],xvar['r_pol']),
            resolution='c',
            area_thresh=10000.,
            lon_0=xvar['sub-satellite_longitude'],
            satellite_height=xvar['satellite_altitude'])
    
    cmap0=myCbar()
    rr=np.fliplr(xvar['values'])
    #rr[rr==0]=np.nan
    im1=m.imshow(rr,cmap=cmap0,vmin=colorAxisMin,vmax=colorAxisMax)
    m.drawcoastlines() 
    # set parallels and meridians
    setParallelsMeridians(latcorners,loncorners,m)
    
    # add colorbar.
    cbar = m.colorbar(location='bottom',pad="5%")
    cbar.set_label(xvar['unit'])
    
    # set limits
    if len(latcorners)==2 and len(loncorners)==2:
        xmin, ymin = m(loncorners[0], latcorners[0])
        xmax, ymax = m(loncorners[1], latcorners[1])
        
        ax = plt.gca()
        
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])

    # add title
    plt.title(xvar['label']+'  '+ xvar['file'])
    
    return fig


def  plotPrecipLatLon(xvar,latcorners,loncorners):
    colorAxisMin=xvar['stdRange'][0]
    colorAxisMax=xvar['stdRange'][1]
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    m = Basemap(projection='geos',
            rsphere=(xvar['r_eq'],xvar['r_pol']),
            resolution='l',
            area_thresh=10000.,
            lon_0=xvar['sub-satellite_longitude'],
            satellite_height=xvar['satellite_altitude'],\
                         llcrnrlat=latcorners[0],urcrnrlat=latcorners[1],\
                         llcrnrlon=loncorners[0],urcrnrlon=loncorners[1])
    cmap0=myCbar()
    im1 = m.pcolor(xvar['lon'],xvar['lat'],xvar['values'],shading='nearest',cmap=cmap0,latlon=True,vmin=colorAxisMin,vmax=colorAxisMax)
    m.drawcoastlines()
    # set parallels and meridians

    setParallelsMeridians(latcorners,loncorners,m)
    # add colorbar.
    cbar = m.colorbar(location='bottom',pad="5%")
    cbar.set_label(xvar['unit'])
    # add title
    plt.title(xvar['label']+'  '+ xvar['file'])
    plt.show()
    return fig
   
   

    # add title
    #plt.title(xvar['label']+'  '+ xvar['time'])
    

def listFiles(input_path='',output_path='',ext2find='.nc' ):
    # lists the input files to be processed with extension defined by ext2find
    # input_path can be a folder or a file, default is local folder
    # output_path can be a folder, default is local folder
    if len(input_path)>1:
        if os.path.isdir(input_path): #if input_path is a folder
            inpt=input_path+os.sep+'*'+ext2find
        elif os.path.isfile(input_path): #if input_path is a single file
            inpt=input_path
    else: #if input_path is not defined
        inpt=os.getcwd()+os.sep+'*'+ext2find #looks for files in the local folder
        outpt=os.getcwd()+os.sep
    if len(output_path)>1:
        outpt=output_path+os.sep
    else:
        outpt=os.getcwd()+os.sep
    
    lst1=glob.glob(inpt)
    if not lst1:
        print('no file found')
    lst1.sort()
    return lst1,outpt
 
def makeGif(lst2,outpt):
    #it creates an animated gif from images listed in lst2
    import imageio as iio
    from pygifsicle import optimize
    outfilegif=outpt+os.path.basename(lst2[0])+os.path.basename(lst2[-1])+'.gif'
    image=[]
    for img in lst2:
        image.append(iio.imread(img))
    iio.mimsave(outfilegif, image, fps=2)
    # with iio.get_writer(outfilegif, mode='I') as writer:
    #     for img in lst2:
    #         writer.append_data(iio.imread(img))
    optimize(outfilegif)
    gif = iio.mimread(outfilegif)
    iio.mimsave(outfilegif, gif, fps=2)    
    iio.show()
    return outfilegif

def gunzip(infilename):
    # this function unzip a .gz file
    input = gzip.GzipFile(infilename, 'rb')
    s = input.read()
    input.close()
    output = open(infilename[0:-3], 'wb')
    output.write(s)
    output.close()
    return infilename[0:-3]