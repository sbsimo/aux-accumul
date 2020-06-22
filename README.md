# aux-accumul repository
Generates forecasted alerts for extreme-precipitation events

## Usage in production mode
### STEP 1 - Clone the repository in your server using git 
    git clone https://github.com/ITHACA-org/aux-accumul.git
or simply download the repository and extract it in your server

### STEP 2 - Build the Docker image using the following commands
    cd aux-accumul
    docker build --tag dati_cima:1.0 .
You should now have a docker image with that tag name. 

### STEP 3 - Run the image for the first time with the following command
    docker run -it --volume /path/to/host/data/folder:/home/aux-accumul/data/wrf --name dati_cima dati_cima:1.0
Please substitute the first part of the --volume switch with the destination host folder, like below

### STEP 4 - After the first run you can restart the process as needed, with the command below
    docker start -a dati_cima

## Development mode
### Requirements are GDAL and Python 3 (minimum tested version is 3.6) with the following packages:
* python-gdal
* numpy
* scipy
* netCDF4
* pysftp
### The main module is __procedure.py__ , run it with the command
    python3 procedure.py
