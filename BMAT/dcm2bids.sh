#!/bin/bash

#SBATCH --job-name=dcm2bids
#SBATCH --output=/storage/research/ions/cemo-pm/shared/BMAT/dcm2bids.log
#SBATCH --error=/storage/research/ions/cemo-pm/shared/BMAT/dcm2bids.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=8192
#SBATCH --time=00:00:45

# prepare environment
module purge 
module load dcm2niix Python/3.10
source /storage/research/ions/cemo-pm/shared/BMAT/.venv/bmat-dcm2bids/bin/activate

python3 /storage/research/ions/cemo-pm/shared/BMAT/dcm2bids_job.py /storage/research/ions/cemo-pm/shared/test/bids_test 001 01 /storage/research/ions/cemo-pm/shared/test/VANDEN-BULCKE-COLIN.zip -z -seq /storage/research/ions/cemo-pm/shared/BMAT/sequences.csv -iso

    
