import json


######## get_names Function ########
# Parameters:- n/a
# Return type:- names: list
# Purpose: Opens the json database to read the names and returns them
##########################
def get_names():
    names = []
    try:
        r_file = open("scores.json", "r")
    except FileNotFoundError:
        return []
    else:  # runs if try statement catches no exception
        scores = json.load(r_file)
        for score_data in scores:
            names.append(score_data[0])
    r_file.close()
    return names


######## get_scores Function ########
# Parameters:- n/a
# Return type:- score: list
# Purpose: Reads the score database and saves the scores tuples - (name, score) and returns them
##########################
def get_scores():
    try:
        s_file = open("scores.json", "r")  # opens file for reading
    except FileNotFoundError:  # if no file, no scores
        return None
    else:  # if no exception, will run else statement
        scores = json.load(s_file)  # deserialize the opened file
        s_file.close()
        return scores


######## add_score Function ########
# Parameters:- name: string, score: integer
# Return type:- n/a
# Purpose: With a given name and score, will add the record into the database sorted by scores,  ascending.
##########################
def add_score(name, score):  # sorts score into correct position
    try:
        r_file = open("scores.json", "r")  # opens file for reading
    except FileNotFoundError:  # if no actual file there
        w_plus_file = open("scores.json", "w+")  # makes a new file and is for writing
        json.dump([[name, score]], w_plus_file)  # puts the value in to
        w_plus_file.close()
    else:  # if no exception occurs in the try part, continue
        scores = json.load(r_file)  # deserialize the opened file
        pos = 0  # keeps count of what index we need to put the value into

        for score_data in scores:
            if score_data[1] > score:  # if score in list is smaller, use current pos val as the index
                pos += 1  # is will be the index of the next item in the list
            else:
                break  # if score is bigger, will break and so curr pos is set
        scores.insert(pos, (name, score))

        r_file.close()

        with open("scores.json", "w") as w_file:  # opens file for writing
            json.dump(scores, w_file)  # serialise the new list of scores to be dumped
