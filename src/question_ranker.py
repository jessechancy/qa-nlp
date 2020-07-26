

PP_LIMIT = 2
COMMA_LIMIT = 2

def contains(question, phrase_list):
    for phrase in phrase_list:
        if phrase.text in question:
            return True
    return False

def rank(indexed_questions, rank_phrases):
    rank1 = [] #satisfies all constraints
    rank2 = [] #fails one constraint
    rank3 = [] #fails two constraints
    for (question, i, pp_count) in indexed_questions:
        fails = 0
        comma_count = question.count(",")
        if pp_count > PP_LIMIT:
            fails += 1
        if comma_count > COMMA_LIMIT:
            fails += 1
        if len(question) < 30 or len(question) > 150:
            fails += 1
        
        if fails == 0 and pp_count < PP_LIMIT and comma_count < COMMA_LIMIT:
            rank1.append(question)
        elif fails == 0 and (pp_count == PP_LIMIT or comma_count == COMMA_LIMIT):
            rank2.append(question)
        if fails > 0:
            rank3.append(question)
    finalrank = dict()
    for question in rank1:
        flag = False
        for p in rank_phrases:
            if contains(question, p.chunks):
                finalrank[question] = p.rank
                break
    finalrank2 = dict()
    for question in rank2:
        flag = False
        for p in rank_phrases:
            if contains(question, p.chunks):
                finalrank2[question] = p.rank
                break
    sort1 = sorted(finalrank, key=lambda key: -finalrank[key])
    sort2 = sorted(finalrank2, key=lambda key: -finalrank2[key])
    return sort1 + sort2 + rank3

