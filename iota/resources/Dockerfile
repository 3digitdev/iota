FROM ubuntu:16.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-utils \
        build-essential \
        apt-utils \
        cmake \
        git \
        wget \
        libatlas-base-dev \
        libboost-all-dev \
        libgflags-dev \
        libgoogle-glog-dev \
        libhdf5-serial-dev \
        libleveldb-dev \
        liblmdb-dev \
        libopencv-dev \
        libprotobuf-dev \
        libsnappy-dev \
        protobuf-compiler \
        python-dev \
        python3-dev \
        python-numpy \
        python-pip \
        python-setuptools \
        python-scipy \
        python-pyaudio \
        python3-pyaudio \
        sox \
        libpcre3 \
        libpcre3-dev

RUN python3 -m pip install pyaudio

RUN rm -rf /var/lib/apt/lists/*

RUN wget http://downloads.sourceforge.net/swig/swig-3.0.10.tar.gz -O swig-3.0.10.tar.gz
RUN tar xvzf swig-3.0.10.tar.gz
RUN cd swig-3.0.10 && ./configure --prefix=/usr --without-clisp --without-maximum-compile-warnings \
       && make && make install \
       && install -v -m755 -d /usr/share/doc/swig-3.0.10 \
       && cp -v -R Doc/* /usr/share/doc/swig-3.0.10

WORKDIR /workspace

RUN git clone https://github.com/Kitt-AI/snowboy.git
WORKDIR /workspace/snowboy/swig/Python/

RUN make

WORKDIR /workspace/snowboy
RUN mkdir model
ADD tools/Iota.pmdl model/Iota.pmdl
RUN python3 setup.py install
