#!/bin/bash -l

#SBATCH -J JOBNAME
#SBATCH -q shared
#SBATCH -A dessn
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 02:00:00
#SBATCH -L SCRATCH,project
#SBATCH -C haswell

dir=$1
folder=$2

cd ${SLURM_SUBMIT_DIR}

source /global/common/software/dessn/cori_haswell/setup_DiffImg_Haswell.sh

cp /global/cscratch1/sd/eriwang/default.conv ./${dir}
cp /global/cscratch1/sd/eriwang/default.param ./${dir}
cp /global/cscratch1/sd/eriwang/default.sex ./${dir}

cp /global/cscratch1/sd/eriwang/runsextractor.sh .

funpack ${dir}/${folder}/*Template*.fits.fz

./runsextractor.sh ${dir} ${folder}

source /global/common/software/dessn/cori_haswell/setup_python.sh
conda activate astro

cp /global/cscratch1/sd/eriwang/cutoutsandfileio.py .
python cutoutsandfileio.py --dir ${dir} --fol ${folder}
