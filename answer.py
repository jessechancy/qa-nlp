#!/usr/bin/env python3
import os
import sys
import nltk
from nltk.parse import CoreNLPParser
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download("punkt")
nltk.download("stopwords")
# nltk.download("all")

def cosine_sim(t1_set, t2_set):

    combined_set = t1_set.union(t2_set)

    v1 = []
    v2 = []

    #Create vectors based on unique word occurrences
    for word in combined_set:
        if word in t1_set:
            v1.append(1) # create a vector
        else:
            v1.append(0)

        if word in t2_set:
            v2.append(1)
        else:
            v2.append(0)

    matches = 0
    #Cosine Formula
    for i in range(len(combined_set)):
            matches += v1[i] * v2[i]
    cosine = matches / float((sum(v1)*sum(v2))**0.5)
    #print("similarity: ", cosine)
    return cosine

#Input: File object to article
#Output: List of sentences from article
def preprocess(article_file):
    sentences = []
    text = article_file.read()
    paragraphs = text.split("\n")
    for entry in paragraphs:
        split_entries = entry.split(".")
        for se in split_entries:
            if len(se) > 0: #Get rid of empty lines
                sentences.append(se)

    return sentences

#Input: Question, Sentences from queried article
#Output: Answer
def answer(q, sentences):
    qt = word_tokenize(q)

    #Things to remove
    wh = {"Where", "What", "Who", "How", "Why", "When"}
    func = {"a", "an", "the"}
    stops = stopwords.words('english')

    total = wh.union(func).union(stops)

    #TODO: Experiment with what to include as a "function word" for elimination purposes
    #https://www.thoughtco.com/function-word-grammar-1690876

    #Remove words from question
    q_set = {word for word in qt if not word in total}
    results = dict()

    #Remove words from the sentences as well
    for s in sentences:

        st = word_tokenize(s)
        s_set = {word for word in st if not word in stops}

        #Perform cosine similarity and store results in dictionary for each sentence
        k = cosine_sim(q_set, s_set)
        results[k] = s #NOTE: Collisions will just result in later sentences being preferred

    #The sentence with the highest similarity is used as answer
    keys = sorted(results.keys(), reverse=True)

    #print(keys)
    #print(keys[0])

    answer = results[keys[0]] + "."

    '''
    print()
    print("Question: ", q)
    print("Answer: ", answer)
    print()
    '''

    '''
    print("All recorded sentences")
    for k in keys:
        print(results[k])
        print()
    '''

    print(answer)

def main():

    # Lexical Parser
    #parser = CoreNLPParser(url='http://localhost:9000')
    #s = 'What is the color of a swallow, a robin, and a cardinal?'
    #NOTE: 1) Make sentence lowercase
    #Removed for now to create dry run test
    '''
    s = s.lower()
    parsed_list = list(parser.parse(s.split()))
    print(parsed_list)

    for item in parsed_list:
        print(item)
        print(item == "(ROOT")
    '''

    #Check for inputs and assign paths to open files
    print(len(sys.argv))
    '''
    if len(sys.argv) != 3:
        print("ERROR: More arguments required - current number: " + str(len(sys.argv) - 1))
        exit
    '''

    article_path = sys.argv[1]
    questions_path = sys.argv[2]

    artF = open(article_path, "r",encoding='utf8')
    quesF = open(questions_path, "r",encoding='utf8')

    #Temporary filler answering method

    #Preprocess document for querying
    sentences = preprocess(artF)

    #Answer each question in text file
    text = quesF.read()
    questions = text.split("\n")
    for q in questions:
        answer(q, sentences)

    #Close files before ending
    artF.close()
    quesF.close()

# Main function
if __name__ == "__main__":
    main()