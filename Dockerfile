#FROM ubuntu:19.04
FROM python:3

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

# Default versions
#ENV INFLUXDB_VERSION=1.7.7
#ENV CHRONOGRAF_VERSION=1.4.4.2
#ENV GRAFANA_VERSION=6.2.5

# Grafana database type
#ENV GF_DATABASE_TYPE=sqlite3

# Fix bad proxy issue
COPY system/99fixbadproxy /etc/apt/apt.conf.d/99fixbadproxy

WORKDIR /root

# Clear previous sources
RUN rm /var/lib/apt/lists/* -vf \
    # Base dependencies
    && apt-get -y update \
    && apt-get -y dist-upgrade \
    && apt-get -y --force-yes install \
        apt-utils \
        ca-certificates \
        curl \
        git \
        htop \
        libfontconfig \
        nano \
        net-tools \
        supervisor \
        wget \
        gnupg \
        python3 \
        python3-pip \
        zip \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install -y nodejs \
    && mkdir -p /var/log/supervisor \
    && rm -rf .profile \
    # Install InfluxDB
#    && wget https://dl.influxdata.com/influxdb/releases/influxdb_${INFLUXDB_VERSION}_amd64.deb \
#    && dpkg -i influxdb_${INFLUXDB_VERSION}_amd64.deb && rm influxdb_${INFLUXDB_VERSION}_amd64.deb \
#    # Install Chronograf
#    && wget https://dl.influxdata.com/chronograf/releases/chronograf_${CHRONOGRAF_VERSION}_amd64.deb \
#    && dpkg -i chronograf_${CHRONOGRAF_VERSION}_amd64.deb && rm chronograf_${CHRONOGRAF_VERSION}_amd64.deb \
#    # Install Grafana
#    && wget https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana_${GRAFANA_VERSION}_amd64.deb \
#    && dpkg -i grafana_${GRAFANA_VERSION}_amd64.deb && rm grafana_${GRAFANA_VERSION}_amd64.deb \
    && wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-02-27.zip
    && unzip stanford-corenlp-full-2018-02-27.zip

    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configure Supervisord and base env
#COPY supervisord/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
#COPY bash/profile .profile
#
## Configure InfluxDB
#COPY influxdb/influxdb.conf /etc/influxdb/influxdb.conf
#COPY influxdb/init.sh /etc/init.d/influxdb
#
## Configure Grafana
##COPY grafana /etc/grafana
#COPY grafana/grafana.ini /etc/grafana/grafana.ini
#COPY grafana/provisioning/datasources/datasource.yaml /etc/grafana/provisioning/datasources/datasource.yaml
#COPY grafana/provisioning/dashboards/local.yml /etc/grafana/provisioning/dashboards/local.yml
#COPY grafana/dashboards/metrics.json /var/lib/grafana/dashboards/metrics.json
#RUN chmod 0755 /etc/init.d/influxdb

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
ARG PYTHONPATH
ENV PYTHONPATH=${PYTHONPATH}:ignite
ENV OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

CMD ["/usr/bin/supervisord"]
