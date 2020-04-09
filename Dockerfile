# Ubuntu Linux as the base image
FROM ubuntu:16.04
# Set UTF-8 encoding
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
# Install packages, you should modify this based on your program
RUN apt-get -y update && \
 apt-get -y upgrade && \
 apt-get -y install python3-pip python3-dev &&\
 pip3 install spacy && \
 python3 -m spacy download en_core_web_lg
RUN wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
# Download standford NLP
RUN unzip stanford-corenlp-full-2018-10-05.zip; \
unzip stanford-ner-2018-10-16.zip; \
mv stanford-corenlp-full-2018-10-05 CoreNLP; \
cd CoreNLP; \
export CLASSPATH=""; for file in `find . -name "*.jar"`; \
do export CLASSPATH="$CLASSPATH:`realpath $file`"; done

# Expose port 9090 for standford corenlp
ENV PORT 9090

EXPOSE 9090
# Add the files into container, under QA folder, modify this based on your need
ADD ask /QA
ADD answer /QA
ADD answer.py /QA

COPY . .
# Change the permissions of programs, you may add other command if needed
CMD ["chmod 777 ask"]
CMD ["chmod 777 answer"]
# Set working dir as /QA
#WORKDIR /QA
#ENTRYPOINT ["/bin/bash", "-c"]
ENTRYPOINT [ "./start.sh" ]