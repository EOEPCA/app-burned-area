import os
import sys 
from pystac import Catalog, Collection, Item, MediaType, Asset, CatalogType
import gdal
import numpy as np
import datetime
from .helpers import *
import logging
import click
import shutil

gdal.UseExceptions()

logging.basicConfig(stream=sys.stderr, 
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

workflow = dict([('id', 'burned-area'),
                ('label', 'Sentinel-2 burned area'),
                ('doc', 'Sentinel-2 burned area with NDVI/NDWI threshold')])


ndvi_threshold = dict([('id', 'ndvi_threshold'),
                       ('value', '0.19'),
                       ('label', 'NDVI difference threshold'),
                       ('doc', 'NDVI difference threshold'),
                       ('type', 'string')])

ndwi_threshold = dict([('id', 'ndwi_threshold'),
                       ('value', '0.18'),
                       ('label', 'NDWI difference threshold'),
                       ('doc', 'NDWI difference threshold'),
                       ('type', 'string')])

pre_event = dict([('id', 'pre_event'),
                  ('label', 'Sentinel-2 Level-2A pre-event'),
                  ('doc', 'Sentinel-2 Level-2A pre-event acquisition'),
                  ('value', '/workspace/data/'), 
                  ('type', 'Directory'),
                  ('stac:collection', 'pre-event'),
                  ('stac:href', 'catalog.json')])

post_event = dict([('id', 'post_event'),
                  ('label', 'Sentinel-2 Level-2A post-event'),
                  ('doc', 'Sentinel-2 Level-2A post-event acquisition'),
                  ('value', '/workspace/data/'), 
                  ('type', 'Directory'),
                  ('stac:collection', 'post-event'),
                  ('stac:href', 'catalog.json')])


@click.command()
@click.option('--pre_event', 'e_pre_event' , help=pre_event['doc'])
@click.option('--post_event', 'e_post_event' , help=post_event['doc'])
@click.option('--ndvi_threshold', 'e_ndvi_threshold', default=0.19, help=ndvi_threshold['doc'])
@click.option('--ndwi_threshold', 'e_ndwi_threshold', default=0.18, help=ndwi_threshold['doc'])
def entry(e_pre_event, e_post_event, e_ndvi_threshold, e_ndwi_threshold):
    
    ndvi_threshold['value'] = e_ndvi_threshold
    ndwi_threshold['value'] = e_ndwi_threshold
    pre_event['value'] = e_pre_event  
    post_event['value'] = e_post_event
    
    main(ndvi_threshold, ndwi_threshold, pre_event, post_event)

def main(ndvi_threshold, ndwi_threshold, pre_event, post_event):

    os.environ['PREFIX']='/opt/anaconda/envs/env_burned_area'
    
    os.environ['PROJ_LIB'] = os.path.join(os.environ['PREFIX'], 'share/proj')
    os.environ['GDAL_DATA'] = os.path.join(os.environ['PREFIX'], 'share/gdal')
    
    logging.info(os.path.join(pre_event['value'], 'catalog.json'))
    logging.info(os.path.join(post_event['value'], 'catalog.json'))

    pre_s2 = os.path.join(pre_event['value'], 'catalog.json')
    post_s2 = os.path.join(post_event['value'], 'catalog.json')
    
    s2_items = dict()

    s2_items['pre-event'] =  get_item(pre_s2)
    s2_items['post-event'] = get_item(post_s2)
    
    for key, s2_item in s2_items.items():
        
        logging.info('Stacking bands for input {}'.format(key))
        vrt_bands = []

        for band in ['B04', 'B08', 'B11', 'SCL']:

            vrt_bands.append(s2_item.assets[band].get_absolute_href())

        vrt = '{}.vrt'.format(key)
        tif = '{}.tif'.format(key)

        logging.info('Build vrt for {}'.format(key))

        ds = gdal.BuildVRT(vrt,
                           vrt_bands,
                           srcNodata=0,
                           xRes=10, 
                           yRes=10,
                           separate=True)
        ds.FlushCache()


        logging.info('Translate {}'.format(key))

        gdal.Translate(tif,
                       vrt,
                       outputType=gdal.GDT_UInt16)

        os.remove(vrt)
    
    
    ds = gdal.Open('pre-event.tif')

    pre_b04 = ds.GetRasterBand(1).ReadAsArray()
    pre_b08 = ds.GetRasterBand(2).ReadAsArray()
    pre_b11 = ds.GetRasterBand(3).ReadAsArray()
    pre_scl = ds.GetRasterBand(4).ReadAsArray()

    ds = None

    os.remove('pre-event.tif')

    ds = gdal.Open('post-event.tif')

    post_b04 = ds.GetRasterBand(1).ReadAsArray()
    post_b08 = ds.GetRasterBand(2).ReadAsArray()
    post_b11 = ds.GetRasterBand(3).ReadAsArray()
    post_scl = ds.GetRasterBand(4).ReadAsArray()

    width = ds.RasterXSize
    height = ds.RasterYSize

    input_geotransform = ds.GetGeoTransform()
    input_georef = ds.GetProjectionRef()

    ds = None

    os.remove('post-event.tif')

    gain = 10000

    pre_ndwi2 = (pre_b08 / gain - pre_b11 / gain) / (pre_b08 / gain  + pre_b11 / gain)
    post_ndwi2 = (post_b08 / gain - post_b11 / gain) / (post_b08 / gain + post_b11 / gain)

    pre_b11 = None
    post_b11 = None

    pre_ndvi = (pre_b08 / gain - pre_b04 / gain) / (pre_b08 / gain  + pre_b04 / gain)
    post_ndvi = (post_b08 / gain - post_b04 / gain) / (post_b08 / gain + post_b04 / gain)

    pre_b04 = None
    post_b04 = None

    pre_b08 = None
    post_b08 = None

    conditions = (((post_ndwi2 - pre_ndwi2) > float(ndwi_threshold['value'])) & ((post_ndvi - pre_ndvi) > float(ndvi_threshold['value'])) & (pre_scl == 4) | (post_scl == 4))  

    burned = np.zeros((height, width), dtype=np.uint8) 

    burned[conditions] = 1

    pre_ndwi2 = None
    post_ndwi2 = None

    pre_ndvi = None
    post_ndvi = None
    
    burned[np.where((pre_scl == 0) | (post_scl == 0) | (pre_scl == 1) | (post_scl == 1) | (pre_scl == 5) | (post_scl == 5) | (pre_scl == 6) | (post_scl == 6) | (pre_scl == 7) | (post_scl == 7) | (pre_scl == 8) | (post_scl == 8) | (pre_scl == 9) | (post_scl == 9))] = 2 


    logging.info('Write output product')

    output_name = 'S2_BURNED_AREA_{}'.format('_'.join([s2_item.datetime.strftime("%Y%m%d")for key, s2_item in s2_items.items()])) 

    write_tif(burned, '{}.tif'.format(output_name),
              width,
              height,
              input_geotransform,
              input_georef)

    
    logging.info('Output catalog')

    catalog = Catalog(id='catalog', description='Results')

    catalog.clear_items()
    catalog.clear_children()

    result_titles = dict()

    result_titles[output_name] = {'title': 'Burned area analysis from Sentinel-2',
                                  'media_type': MediaType.COG}



    items = []

    for key, value in result_titles.items():

        result_item = Item(id=key,
                           geometry=s2_items['pre-event'].geometry,
                           bbox=s2_items['pre-event'].bbox,
                           datetime=s2_items['pre-event'].datetime,
                           properties={})

        result_item.add_asset(key='data',
                              asset=Asset(href='./{}.tif'.format(key), 
                              media_type=value['media_type'], 
                              title=value['title']))

        items.append(result_item)

    #collection.add_items(items)

    catalog.add_items(items)

    catalog.describe()

    catalog.normalize_and_save(root_href='./',
                               catalog_type=CatalogType.SELF_CONTAINED)

    
    shutil.move('{}.tif'.format(output_name), 
            os.path.join('./',
                         output_name,
                         '{}.tif'.format(output_name)))
    
    
if __name__ == '__main__':
    entry()

            

    




