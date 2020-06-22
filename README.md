# aux-accumul repository
Generates forecasted alerts for extreme-precipitation events

## Usage in production mode
### STEP 1 - Clone the repository in your server using git 
    git clone https://github.com/ITHACA-org/aux-accumul.git
or simply download the repository and extract it in your server

### STEP 2 - Customize the procedure
1. copy the sea/land mask file and the rain-threshold files in the [tool_data](./tool_data) folder
1. edit the [config.ini](./config.ini) file with proper values

### STEP 3 - Build the Docker image using the following commands
    cd aux-accumul
    docker build --tag tag_name:version .
You should now have a docker image with that <tag_name>. 

### STEP 4 - Run the image for the first time with the following command
    docker run -it --volume /path/to/host/data/folder:/home/aux-accumul/data/wrf --name container_name tag_name:version
Please substitute the first part of the --volume switch with the destination host folder, like below

### STEP 5 - After the first run you can restart the process as needed, with the command below
    docker start -a container_name

## Development mode
### Requirements are GDAL and Python 3 (minimum tested version is 3.6) with the following packages:
* python-gdal
* numpy
* scipy
* netCDF4
* pysftp
### The main module is __procedure.py__ , run it with the command
    python3 procedure.py
