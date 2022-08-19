#!/bin/bash

dir=$1
folder=$2

cd ${dir}

for file in ${folder}/*{tile,combined}*_${folder}*+fakeSN.fits.fz
    do
	prefix=`echo ${file} | cut -d"/" -f2 | cut -d"." -f1`
#	echo ${prefix}
        funpack ${folder}/${prefix}.fits.fz
	funpack ${folder}/${prefix}.weight.fits.fz
    done

for file in ${folder}/*{tile,combined}*_${folder}*+fakeSN.fits
    do
    prefix=`echo ${file} | cut -d"/" -f2 | cut -d"." -f1`
	sex ${file} -WEIGHT_IMAGE ${folder}/${prefix}.weight.fits -CATALOG_NAME ${prefix}.cat -c default.sex
    done

cd ..
