FROM osgeo/gdal:ubuntu-small-3.0.4

RUN apt update
RUN apt install -y python3-pip

RUN pip3 install scipy
RUN pip3 install netCDF4
RUN pip3 install pysftp

RUN pip3 install numpy --upgrade

COPY . /home/aux-accumul
VOLUME /home/aux-accumul/data/wrf
WORKDIR /home/aux-accumul

CMD python3 procedure.py

