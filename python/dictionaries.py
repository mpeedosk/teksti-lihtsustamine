# Tagastame sagedusloendi
def get_freq_dict(location):
    freq_word = {}
    with open(location, "r", encoding="UTF-8") as file:
        for line in file:
            parts = line.split(" ")
            word = parts[0].strip()
            count = int(parts[1])
            freq_word[word] = count
    return freq_word


# Tagastame võõrsõnade loendi
def get_foreign_dict(location):
    foreign_words = {}
    with open(location, "r", encoding="UTF-8") as file:
        for line in file:
            parts = line.strip().split(" ")
            if len(parts) > 1:
                foreign_words[parts[0]] = parts[1]
            else:
                foreign_words[parts[0]] = None
    return foreign_words


# Tagastame põhisõnavara loendi
def get_basic_list(location):
    basic_words = []
    with open(location, "r", encoding="UTF-8") as file:
        for line in file:
            basic_words.append(line.strip())
    return basic_words
