# qa-nlp

qa-nlp utilizes natural language processing techniques to generate questions and answers from text. 

The primary purpose of the project is for learning nlp techniques such as Named Entity Recognition, Coreference Resolution, Part Of Speech, etc.

## Usage

Start the CoreNLPServer by going to the stanford-corenlp-full-XXXX-XX-XX directory and type the following command
```bash
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
-preload tokenize,ssplit,pos,lemma,ner,parse,depparse \
-status_port 9000 -port 9000 -timeout 15000 & 
```

ask.py generates a file with a list of questions from a text file
```bash
python3 src/ask.py --input ../development_data/text.txt --output ../generated_data/questions.txt
```
