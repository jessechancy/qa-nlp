import os,re
terminators = ['.', '!', '?',"..."]
for filename in os.listdir('.'):
    if filename.endswith(".txt"):
        prefix = filename.split(".")[0]
        with open(filename,"r") as f:
            data = f.read()
            newFile = open(prefix+"sentence"+".txt","w+")
            regexPattern = '|'.join(map(re.escape, terminators))
            sentenceLst = re.split(regexPattern,data)
            for sentence in sentenceLst:
                newFile.write(sentence+"\n")
            newFile.close()
