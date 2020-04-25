# Ubuntu Linux as the base image
FROM ubuntu:16.04
# Set UTF-8 encoding
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Fix bad proxy issue
COPY system/99fixbadproxy /etc/apt/apt.conf.d/99fixbadproxy
# Install packages, you should modify this based on your program
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
        zip \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install -y nodejs \
    && mkdir -p /var/log/supervisor \
    && rm -rf .profile

RUN apt-get -y update && \
 apt-get -y upgrade && \
 apt-get -y install python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN pip3 install spacy && \
 python3 -m spacy download en_core_web_lg
RUN apt-get -y install wget
RUN wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
# Download standford NLP
RUN apt-get -y install unzip
RUN unzip stanford-corenlp-full-2018-10-05.zip; \
unzip stanford-ner-2018-10-15.zip; \
mv stanford-corenlp-full-2018-10-05 CoreNLP; \
cd CoreNLP; \
export CLASSPATH=""; for file in `find . -name "*.jar"`; \
do export CLASSPATH="$CLASSPATH:`realpath $file`"; done


# Configure Supervisord and base env
COPY supervisord/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY bash/profile .profile

ENV JAVA_XMX 4g
# Expose port 9000 for standford corenlp
ENV PORT 9000

EXPOSE 9000
# Add the files into container, under QA folder, modify this based on your need
RUN python3 -m spacy download en_core_web_sm

RUN apt-get -y install openjdk-8-jdk
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get -y install python3-tk
COPY . .

# Change the permissions of programs, you may add other command if needed
CMD ["chmod 777 ask"]
CMD ["chmod 777 answer"]
CMD ["chmod 777 start.sh"]
RUN nohup java -mx4g -cp "CoreNLP/*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -preload tokenize,ssplit,pos,lemma,ner,parse,depparse -status_port 9000 -port 9000 -timeout 15000 & exec "$@"
CMD ["/usr/bin/supervisord"]
#ENTRYPOINT ["/bin/bash", "-c"]
ENTRYPOINT [ "./start.sh" ]