# region imported modules
import csv
import numpy as np
import h5py
import gdal
from osgeo import osr
import datetime
import tempfile
import os
import sys
# endregion
from auxilary import progressbar




# region Decoder/Convert Module

class Decoder(object):
    def __init__(self):

        self.version = '0.3'
        self.product = None
        self._product_list = ['H10', 'H12', 'H35', 'H34', 'H13']
        self.last_update = "Log methodology has been removed"
        self.product_transformation_array = {

            "H13": [(-25.12500, 0.25, 0.0, 75.125, 0.0, -0.25), (201, 281), [75.000, -25.000], [25.000, 45.0000]],
            "H12": [(-25.00500, 0.01, 0.0, 75.005, 0.0, -0.01), (5000, 7000), [75.000, -25.000], [25.000, 45.0000]],
            "H35": [(-179.9950, 0.01, 0.0, 89.995, 0.0, -0.01), (8999, 35999), [89.99, -179.99], [0.0000, 179.999]],
            "H10": [(-25.02500, 0.05, 0.0, 75.025, 0.0, -0.05), (1001, 1401), [75.000, -25.000], [25.000, 45.0000]],
            "H34": [(-180.0250, 0.05, 0.0, 90.025, 0.0, -0.05), (3601, 7201), [90.000, -180.000], [-90.000, 180.000]],

        }
        self.root_folder = r"."
        self.input_location = os.path.join(self.root_folder, "input")
        self.output_location = os.path.join(self.root_folder, "output")
        self.starttime = datetime.datetime.now()
        self.endtime = None

    def readproduct(self, product_):
        self.product = ""
        if product_ in self._product_list:
            self.product = product_
            return self
        else:
            msg = "Product is not defined"
            raise Exception(msg)

    def get_available_products(self):
        return self._product_list

    def get_product_extend(self):
        return {'UL': self.product_transformation_array[self.product][2],
                'LR': self.product_transformation_array[self.product][3]}

    def get_resolution(self):
        return self.product_transformation_array[self.product][0][1]

    @staticmethod
    def write_to_ascii(data_, header_, file_):
        with open(file_, mode='w') as data_file:
            ascii_writer = csv.writer(data_file, delimiter=' ')
            ascii_writer.writerow(['ncols', header_[0]])
            ascii_writer.writerow(['nrows', header_[1]])
            ascii_writer.writerow(['xllcorner', header_[2]])
            ascii_writer.writerow(['yllcorner', header_[3]])
            ascii_writer.writerow(['cellsize', header_[4]])
            ascii_writer.writerow(['NODATA_value', header_[5]])
            for data_row in data_:
                ascii_writer.writerow(data_row.tolist())

    def msg_geographic_to_pixel(self, latitude_of_msg, longitude_of_msg):
        # MSG specifations
        sat_height = 42164.0
        r_eq = 6378.169
        r_pol = 6356.5838
        sub_lon = 0.0
        cfac = -781648343.0
        lfac = -781648343.0
        coff = 1856.0
        loff = 1856.0

        if self.product.upper() == 'H10':
            upper_left_row_index = 65
            upper_left_column_index = 1215
        elif self.product.upper() == 'H34':
            upper_left_row_index = 1
            upper_left_column_index = 1
        else:
            raise Exception('Product Type', 'Product Type Mismatch: Avilable Products H10 and H34')

        latitude_of_msg = np.deg2rad(latitude_of_msg)
        longitude_of_msg = np.deg2rad(longitude_of_msg)
        geocent_latitude = np.arctan((0.993243 * (np.sin(latitude_of_msg) / np.cos(latitude_of_msg))))
        re = r_pol / np.sqrt((1 - 0.00675701 * np.cos(geocent_latitude) * np.cos(geocent_latitude)))
        r1 = sat_height - re * np.cos(geocent_latitude) * np.cos(longitude_of_msg - np.deg2rad(sub_lon))
        r2 = - re * np.cos(geocent_latitude) * np.sin(longitude_of_msg - np.deg2rad(sub_lon))
        r3 = re * np.sin(geocent_latitude)
        rn = np.sqrt(r1 * r1 + r2 * r2 + r3 * r3)
        rtt = (r_eq / r_pol) * (r_eq / r_pol)
        dotprod = r1 * (re * np.cos(geocent_latitude) * np.cos(
            longitude_of_msg - np.deg2rad(sub_lon))) - r2 * r2 - r3 * r3 * rtt

        xx = np.arctan((-r2 / r1))
        yy = np.arcsin((-r3 / rn))
        rows = np.round(loff + yy * np.power(2.0, (-16.0)) * lfac).astype('int16')
        columns = np.round(coff + xx * np.power(2.0, (-16.0)) * cfac).astype('int16')
        row_re_arranged = (3712 - rows - upper_left_row_index) * (dotprod > 0).astype('int8')
        columns_re_arranged = (3712 - columns - upper_left_column_index) * (dotprod > 0).astype('int8')

        return [row_re_arranged, columns_re_arranged]

    @staticmethod
    def get_extent(gt, cols, rows):
        """Return list of corner coordinates from a geotransform

            @type gt:   C{tuple/list}
            @param gt: geotransform
            @type cols:   C{int}
            @param cols: number of columns in the dataset
            @type rows:   C{int}
            @param rows: number of rows in the dataset
            @rtype:    C{[float,...,float]}
            @return:   coordinates of each corner
        """
        ext = []
        xarr = [0, cols]
        yarr = [0, rows]

        for px in xarr:
            for py in yarr:
                x = gt[0] + (px * gt[1]) + (py * gt[2])
                y = gt[3] + (px * gt[4]) + (py * gt[5])
                ext.append([x, y])
            yarr.reverse()
        return ext

    def convert_array_to_raster(self, np_array, transform, out_f_name, extension="GTiff", epsg_code=4326, bbox=None):
        try:
            if bbox is not None or extension == 'ascii':
                f_name = tempfile.NamedTemporaryFile('w+b').name

            else:
                f_name = out_f_name
            projection = osr.SpatialReference()
            projection.SetWellKnownGeogCS("EPSG:" + str(epsg_code))
            driver = gdal.GetDriverByName("GTiff")
            export_data = driver.Create(f_name, transform[1][1], transform[1][0], 1, gdal.GDT_Float32)
            # sets the extend
            export_data.SetGeoTransform(transform[0])
            # sets projection
            export_data.SetProjection(projection.ExportToWkt())
            export_data.GetRasterBand(1).WriteArray(np_array)

            # if you want these values transparent
            export_data.GetRasterBand(1).SetNoDataValue(999)
            # Save the data
            export_data.FlushCache()
            if bbox is not None and extension is 'GTiff':
                gdal.Translate(out_f_name, export_data, projWin=bbox)
            elif extension is 'ascii':
                asc_ = tempfile.NamedTemporaryFile('w+b').name
                gdal.Translate(asc_, export_data, projWin=bbox)
                if bbox is not None:
                    ds = gdal.Open(asc_)
                else:
                    ds = gdal.Open(f_name)
                t_array = ds.GetRasterBand(1).ReadAsArray()
                exts = self.get_extent(ds.GetGeoTransform(), t_array.shape[1], t_array.shape[0])
                header_array = [t_array.shape[1],
                                t_array.shape[0],
                                exts[1][0],
                                exts[1][1],
                                ds.GetGeoTransform()[1],
                                9999]
                self.write_to_ascii(t_array, header_array, out_f_name)

#             print("Process has been finished")
            return True
        except Exception as e:
            # self.log_.error("There is a problem with exporting")
            print("There is a problem with exporting")
            print('Error on line {}: {} : {}'.format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e))
            return False

    def get_data(self, file_, input_extension="hdf"):
        ret_data = []
        if self.product in ['H10', 'H34']:
            data_name = 'SC' # H34
        elif self.product in ['H12', 'H35']:
            data_name = 'FSC'
        elif self.product in ['H13']:
            data_name = 'SWE'
        else:
            err_txt = "No data name has been provided"
            # self.log_.error(err_txt)
            print(err_txt)
            raise Exception(err_txt)

        if input_extension == "hdf":
            hf = h5py.File(file_, 'r')
            data = hf[data_name]
            ret_data = np.array(data)
            hf.close()
        elif input_extension == "grib2":
            ds = gdal.Open(file_)
            dd = ds.GetRasterBand(1)
            ret_data = dd.ReadAsArray()

            ret_data = ret_data[0:self.product_transformation_array[self.product][1][0], 0:self.product_transformation_array[self.product][1][1]]
        return ret_data

    def reporoject(self, file_, out_file, input_extension="hdf", extension="GTiff", boundingbox=None):
        hsaf_data = None
        # self.log_.info("START " + self.product + " : Converting")

        file_ = os.path.join(self.input_location, file_)

        ext = self.get_product_extend()
        ul = ext['UL']
        lr = ext['LR']
        resolution = self.get_resolution()
        if self.product in ['H10', 'H34']:
            lat_to_be_projected = np.arange(ul[0], lr[0] - resolution, -resolution)
            lon_to_be_projected = np.arange(ul[1], lr[1] + resolution, resolution)
            whole_lat = np.tile(lat_to_be_projected, (np.shape(lon_to_be_projected)[0], 1))
            whole_lon = np.tile(lon_to_be_projected, (np.shape(lat_to_be_projected)[0], 1))
            csc = self.get_data(file_, input_extension)
            ret = self.msg_geographic_to_pixel(whole_lat, whole_lon.transpose())
            filt = (ret[0] > 0) & (ret[1] > 0) & (ret[0] < csc.shape[0]) & (ret[1] < csc.shape[1])
            ret_0 = ret[0] * filt
            ret_1 = ret[1] * filt
            csc_filtered = csc[ret_0, ret_1]
            csc_filtered_t = csc_filtered.transpose()
            hsaf_data = csc_filtered_t
            del csc_filtered
            del csc_filtered_t
        elif self.product in ['H12', 'H35', 'H13']:
            hsaf_data = self.get_data(file_, input_extension)

        self.convert_array_to_raster(hsaf_data, self.product_transformation_array[self.product],
                                     os.path.join(self.output_location, out_file),
                                     extension=extension, bbox=boundingbox)



# endregion



# region Decoder Examples
if __name__ == '__main__':
    prod = 'h13'
    if prod == 'h10':
        process_path = './h10_data'
    elif prod == 'h13':
        process_path = './h13_data'
    else:
        process_path = './h34_data'
    dc_h10 = Decoder().readproduct(prod.upper())
    dc_h10.input_location = process_path
    dc_h10.output_location = process_path
    fname = 'h13_20191026_day_merged.grib2'
    dc_h10.reporoject(fname, 'h13_20191026_day_merged.tif', input_extension='grib2')
    # converter_object = Decoder().readproduct('H10')

    # fname = 'MountainMask.H5' # H12
    # fname = 'mountainmask_sr.h5' # H10
    # fname = 'h13_mountain_mask.H5'  # H34
    # fname = 'MountainMask_North.H5' # H35
    #
    # fname = 'mountainmask_fd.h5'  # H34
    # converter_object.reporoject(fname, 'H10__08.ascii_ck', extension="ascii", boundingbox=[22, 41, 45, 35])
    # converter_object.reporoject(fname, 'H34_test.mmask.gtiff')
    # fname = 'h12_20141130_day_merged.grib2'
    # converter_h34_obj.reporoject(fname, 'H34__BBOX.ascii', extension="ascii", boundingbox=[22, 41, 45, 35])
    # converter_h13_obj.reporoject(fname, 'H12_re_arranged.tif', input_extension="grib2")

    # dc_h13 = Decoder().readproduct('H13')
    # fname = 'h13_20190201_day_merged.grib2'
    # dc_h13.reporoject(fname, 'H13__1_bbox_________1.tif', input_extension="grib2")

    # dc_h12 = Decoder().readproduct('H12')
    # fname = 'H12_20190119_day_TSMS.h5'
    # dc_h12.reporoject(fname, 'H12__08.tif')

    # dc_h12 = Decoder().readproduct('H12')
    # fname = 'H12_20190119_day_TSMS.h5'
    # # dc_h12.reporoject(fname, 'H12__00013___________bbox.ascii', extension='ascii', boundingbox=[22, 41, 45, 35])
    # dc_h12.reporoject(fname, 'H12__00013___________normal_bbox.tiff', boundingbox=[22, 41, 45, 35])
    # endregion
