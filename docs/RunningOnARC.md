# Running on ARC
To run your container on ARC, copy the `.sif` file to your desired location on ARC:

```bash
scp infinigen_singularity.sif <uniqname>@greatlakes.arc-ts.umich.edu:/<path>/<to>/<destination>/
```

Next, in the folder where your `.sif` file is located on ARC, add a file to put the slurm commands in. You can name this in a way so that you know what the specific slurm file does. For example, mine is called `generate_apartment.slurm` and these are the contents:
```slurm
#!/bin/bash
#SBATCH --account=bucherb_owned1
#SBATCH --partition=spgpu2
#SBATCH --job-name=generate_apartment_infinigen
#SBATCH --output=output_file.txt
#SBATCH --error=error_file.txt
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH -c 48
#SBATCH --gpus=1
#SBATCH --mem=24G
#SBATCH --gpu_cmode=shared

# Load the singularity module
module load singularity

# Run the container
cd /scratch/bucherb_root/bucherb0/skwirskj/
singularity run --bind /scratch/bucherb_root/bucherb0/skwirskj/infinigen_outputs/:/infinigen/infinigen_outputs/ --nv infinigen_singularity.sif
```

The first path in the `bind` needs to point to a folder that you have already created on ARC, and the second one, `/infinigen/infinigen_outputs/`, needs to remain the same unless you change the [generate_apartments.sh](../generate_apartment.sh) script.

Then, make a directory called `omniverse` inside of your outputs folder.
```bash
cd infinigen_outputs
mkdir omniverse
```

Once this is all setup, submit the slurm job on ARC.
```bash
# submit the job
sbatch generate_apartments.slurm

# Check the status of your job
squeue -u <uniqname>
```

Once the job is finished running, you should see output populated in your designated output folder.