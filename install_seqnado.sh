#!/bin/bash

if ! command -v mamba &> /dev/null; then
  echo "mamba not found. Installing mambaforge..."
  # Install mambaforge using the official installer
  wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh -O mambaforge.sh
  bash mambaforge.sh -b -p $HOME/mambaforge
  rm mambaforge.sh
  # Add mambaforge to the PATH
  export PATH="$HOME/mambaforge/bin:$PATH"
fi


# Create a new conda environment from the environment file
echo "Creating a new conda environment..."
mamba env create -n seqnado_dev -f environment_minimal.yml

# Activate the conda environment
echo "Activating the conda environment..."
conda activate seqnado_dev

# Install the seqnado package using pip (editable mode for development)
echo "Installing seqnado..."
pip install -e .

# Deactivate the conda environment
echo "Deactivating the conda environment..."
conda activate base

# Set the environment variables for CCB
if [[ $(hostname) =~ "imm-" ]]; then
  echo 'export APPTAINER_BINDPATH="/ceph:/ceph, /project:/project, /databank:/databank"' >> ~/.bashrc
  export APPTAINER_BINDPATH="/ceph:/ceph, /project:/project, /databank:/databank"
fi


echo "Done!"
