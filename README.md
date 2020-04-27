## Build Info 

NOTE: If simply looking to run the system, follow the steps in bullet 5 under *BUILD STEPS (Detailed)*: *(Run Docker Image (Normal)* .

The question and answer build system is built out of four components : 
The Question generation system, the Answer Generation system, the NLP parsing server and the training datasets. 

### BUILD STEPS OUTLINE
This is the rough outline for the steps used to build the project. 

**Build Python Ask and Answer System**

In order to run the question and answer systems, we need to first install all the modules they depend on via pip. These dependencies are listed elsewhere in the document under “Dependencies for Question Answer System”. 

We expect the source files needed for the question and answer system to be placed in a folder called `sources/question_src` and `sources/answer_src` respectively.


**Download Server**

The ask and answer systems rely on the Standford NLP server to work. It was to be downloaded from http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip


**Download Required Datasets**

The following datasets were downloaded
http://nlp.stanford.edu/data/glove.6B.zip

SPACY en_core_web_lg 
https://spacy.io/models/en

NLTK datasets 
http://www.nltk.org/nltk_data/





Dependencies for Question Answer System

````
    nltk==3.4.5
    numpy==1.17.3
    pycorenlp==0.3.0
    spacy==2.1.0
    neuralcoref==4.0
    pytextrank==2.0.1
````

### BUILD STEPS (Detailed) 

1. Copy sources into QUESTION_SRC
    1. Go to branch “final” 
    2. Copy `./final2/ask.py` into ``sources/question_src`
2. Copy sources into ANSWER_SRC
    1. Go to branch “micheala_dev” 
    2. Copy `./answer.py` into `./sources/answer_src`
3. Build Docker image 
    1. Run `docker build --tag nlp_project . `
4. Run Docker Image (Test)
    1. Run “docker run -it --entrypoint /bin/bash nlp_project”
    2. Run ./start.sh to start server 
    3. Run `tail -f nohup.out` to monitor server output
    4. Once server is listening on port 9000, you may exit tail and run programs 
    5. Examples can be run with `./answer examples/a1.txt examples/q1.txt` and `./ask examples/a1.txt 6`
5. Run Docker Image (Normal)
    1. run `docker run  nlp_project` 
    2. attach to shell sesssion with `docker exec -it <container_ID> /bin/sh -c "[ -e /bin/bash ] && /bin/bash || /bin/sh"`
    3. Check if the server is up by running `netstat -l` and seeing if there is somthing listening on port 9000
    4. Run programs as above
