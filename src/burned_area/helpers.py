import shutil
import gdal
import os

def cog(input_tif):
    
    temp_tif = 'temp.tif'
    
    shutil.move(input_tif, temp_tif)
    
    translate_options = gdal.TranslateOptions(gdal.ParseCommandLine('-co TILED=YES ' \
                                                                    '-co COPY_SRC_OVERVIEWS=YES ' \
                                                                    ' -co COMPRESS=DEFLATE'))

    ds = gdal.Open(temp_tif, gdal.OF_READONLY)

    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
    ds.BuildOverviews('NEAREST', [2,4,8,16,32])
    
    ds = None

    ds = gdal.Open(temp_tif)
    gdal.Translate(input_tif,
                   ds, 
                   options=translate_options)
    ds = None

    os.remove('{}.ovr'.format(temp_tif))
    os.remove(temp_tif)


    
def write_tif(layer, output_name, width, height, input_geotransform, input_georef, to_cog=True):

    driver = gdal.GetDriverByName('GTiff')

    output = driver.Create(output_name, 
                           width, 
                           height, 
                           1, 
                           gdal.GDT_Byte) 
        
    output.SetGeoTransform(input_geotransform)
    output.SetProjection(input_georef)
    output.GetRasterBand(1).WriteArray(layer),

    output.FlushCache()

    if to_cog:
        
        cog(output_name)