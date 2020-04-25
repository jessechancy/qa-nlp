PP_LIMIT = 3
COMMA_LIMIT = 2

def rank(indexed_questions):
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
        if len(question) < 30 or len(question) > 200:
            fails += 1
        
        if fails == 0:
            rank1.append(question)
        if fails == 1:
            rank2.append(question)
        if fails == 2:
            rank3.append(question)
        
    return rank1

