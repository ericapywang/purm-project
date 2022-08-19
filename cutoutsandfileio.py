import sys
import getopt

import csv
import os
import glob
import re
import time

import numpy as np
import matplotlib.pyplot as plt
import astropy

from astropy.visualization import astropy_mpl_style
from astropy.wcs import WCS
from astropy.table import Table
from astropy.utils.data import get_pkg_data_filename
from astropy.io import fits
from astropy.visualization import simple_norm

from astrocut import fits_cut
from astropy import units as u
from astropy.coordinates import SkyCoord

# get list of fake supernova
def get_fake_supernova(filename):
    with open(filename, mode='r') as csv_file:
        fake_list = []
        reader = csv.reader(csv_file)
        count = 0
        for row in reader:
            if len(row) > 0 and row[0].startswith('FAKE'):
                string = list(filter(None, row[0].split(' ')))
                fake_list.append((float(string[14]), float(string[15])))
        csv_file.close()
        return(fake_list)

# check if fake supernova is in cutout
def fake_in_cutout(filename, fake_supernova):
    f = get_pkg_data_filename(filename)
    f1 = fits.open(f)
    #print(f)
        
    for s in fake_supernova:
        wcs = WCS(f1[1].header)
        x, y = wcs.world_to_pixel_values(s[0], s[1])
        if ((0 < x < 51) and (0 < y < 51)):
            print(str(x) + ", " + str(y) + ": true")
            return True
        
    return False

def get_last_id(filename):
    try:
        with open(filename, mode='r') as csv_file:
            table = []
            reader = csv.reader(csv_file)
            for row in reader:
                tablerow = []
                for col in range(0,len(row)):
                    tablerow.append(row[col])
                table.append(tablerow)
            if len(table) == 0:
                last_id = 0
            else:
                last_id = table[len(table) - 1][0][-7:] # only get last 7 digits of ID, don't get exposure number
            #print(last_id)
        return int(last_id)
    except:
        return 0

def check_rows(csv_file, ccd_num, directory, imgs, cutouts_folder):
    with open(csv_file) as csv_file:
        reader = csv.reader(csv_file)
        
        exposure_nums = set()

        # get exposure numbers
        for img in imgs:
            exposure_nums.add(img.split('/')[2].split('_')[1])

        for exp_num in exposure_nums:
            csv_file.seek(0)

            # get number of rows with exposure/ccd number
            print(exp_num.rjust(7,'0') + ccd_num)
            rows = [row for row in reader if row[0][0:10] == exp_num.rjust(7,'0') + ccd_num]
            print("# of rows: " + str(len(rows)))

            #print(imgs)

            # get number of cutouts with exposure/ccd number
            cutouts_list = glob.glob(directory + cutouts_folder + '/' + exp_num.rjust(7,'0') + ccd_num + '*_search.fits')
            print("# of cutouts: " + str(len(cutouts_list)))

            print(len(cutouts_list) == len(rows))

            with open('checks.csv', mode='a') as checks_csv:
                writer = csv.writer(checks_csv)
                writer.writerow([directory, exp_num, len(cutouts_list) == len(rows)])
            checks_csv.close()

def main():
    
    argv = sys.argv[1:]
    
    directory = ''
    folder = '' # g_xx, i_xx, r_xx, z_xx
    
    try:
        opts, args = getopt.getopt(argv, 'hd:f:', ['dir=', 'fol='])
    except getopt.GetoptError:
        print('cutoutsandfileio.py --dir <directory> --fol <folder>')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print('cutoutsandfileio.py --dir <directory> --fol <folder>')
            sys.exit()
        elif opt in ('-d', '--dir'):
            directory = arg
        elif opt in ('-f', '--fol'):
            folder = arg

    csv_name = 'test3.csv'
    cutouts_folder = '/testcutouts'
            
    # get list of directory paths based on date and g_xx, i_xx, r_xx, z_xx
    dirs = sorted(glob.glob(directory + '/' + folder))
    #print(dirs)
    count = 0
    
    start = time.time()

    #file i/o, open file
    with open (csv_name, mode = 'a') as csv_file:
        writer = csv.writer(csv_file)
        id_num = get_last_id(csv_name)

        # loop through each individual folder
        for x in dirs:

            # get list of search image files (combined, tile) in directory
            imgs = sorted(glob.glob(x + '/*[+fakeSN][!weight].fits'))

            # get template image
            template = glob.glob(x + '/SNTemplate*[!weight].fits')[0]

            # for each search image file...
            for search in imgs:

                # read in appropriate catalog
                catalog = x.split('/')[0] + '/'+ search.split('/')[2].split('.fits')[0] + '.cat'
                cat_file = get_pkg_data_filename(catalog)
                fits.info(cat_file)
                
                # get list of fake supernova for that catalog
                fake_supernova = get_fake_supernova(x + '/' + catalog.split('/')[1].split('.cat')[0] + '_doFake.out')

                cat_data = fits.getdata(cat_file, ext=2)
                print(len(cat_data))

                size = (51, 51)
                count = 0
                
                # get exposure number to append to id
                exposure_num = search.split('/')[2].split('_')[1]
                print(exposure_num)
                
                # get ccd number to append to id
                if (x.split('/')[1]).split('_')[0] == 'g':
                    ccd_num = '0' + (x.split('/')[1]).split('_')[1]
                elif (x.split('/')[1]).split('_')[0] == 'r':
                    ccd_num = '1' + (x.split('/')[1]).split('_')[1]
                elif (x.split('/')[1]).split('_')[0] == 'i':
                    ccd_num = '2' + (x.split('/')[1]).split('_')[1]
                elif (x.split('/')[1]).split('_')[0] == 'z':
                    ccd_num = '3' + (x.split('/')[1]).split('_')[1]

                for source in cat_data:
                    try:
                        # CUTOUTS
                        id_num += 1
                        count += 1
                        center_coord = SkyCoord(source[6], source[7], unit = 'deg')

                        # generate cutouts
                        template_cutout = fits_cut(template, center_coord, size, single_outfile = False, output_dir = x + cutouts_folder)
                        search_cutout = fits_cut(search, center_coord, size, single_outfile = False, output_dir = x + cutouts_folder)

                        print(str(count) + ": " + str(template_cutout))
                        print(str(count) + ": " + str(search_cutout))

                        # FILE I/O
                        lst = []

                        # COL 1: ID (should be same as file)
                        lst.append(exposure_num.rjust(7,'0') + ccd_num + str(id_num).rjust(6, '0'))

                        # COL 2-11: INFO FROM CATALOG
                        for y in range(1, len(source)):
                            lst.append(source[y])

                        # COL 12: IF CONTAINS FAKE
                        # check if fake supernova is in the cutout
                        if fake_in_cutout(str(search_cutout[0]), fake_supernova):
                            lst.append(1) # 1 if contains fake
                        else:
                            lst.append(0) # 0 if doesn't contain fake

                        # COL 13: FROM COMBINED/TILE
                        # check if cutout came from tile or combined image
                        if 'combined' in str(search_cutout[0]):
                            lst.append(1)
                        elif 'tile' in str(search_cutout[0]):
                            lst.append(0)

                        #lst.append(str(search_cutout[0]))

                        writer.writerow(lst)

                        # change name of file
                        os.rename(str(search_cutout[0]), x + cutouts_folder + '/' + exposure_num.rjust(7,'0') + ccd_num + str(id_num).rjust(6, '0') + '_search.fits')
                        os.rename(str(template_cutout[0]), x + cutouts_folder + '/' + exposure_num.rjust(7,'0') + ccd_num + str(id_num).rjust(6, '0') + '_template.fits')

                    # if an exception is thrown, skip and move to next cutout
                    except Exception as e:
                        print(str(count), e)

                        
    check_rows(csv_name, ccd_num, dirs[0], imgs, cutouts_folder)
    
    end = time.time()
    print('runtime: ' + str(end - start))
                        
if __name__ == '__main__':
    main()
