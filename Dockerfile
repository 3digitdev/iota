FROM python:3.6.10

WORKDIR /usr/src/app

# Install prereqs
RUN apt-get update && apt-get install -y \
    git \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    python-dev \
    libatlas-base-dev \
    mpg123

# PyAudio Setup
RUN git clone http://people.csail.mit.edu/hubert/git/pyaudio.git \
    && cd pyaudio \
    && python setup.py install

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY run.sh iota/run.sh
RUN chmod +x iota/run.sh

COPY iota/ iota/iota/

WORKDIR /usr/src/app/iota

CMD [ "./run.sh" ]
