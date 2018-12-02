__all__ = ["search"]

import re


def cmpAllLetters(haystack, needle, threshold=1.0):
    """All (or threshold percent) needle letters are in the haystack and in almost (index-+1) correct order"""

    occurence = 0
    for i in range(len(needle)):
        char = needle[i]
        foundindex = haystack.find(char, i - 2 if i > 1 else 0, i + 2)
        if foundindex != -1:
            occurence += 1

    if occurence / len(needle) >= threshold:
        return True

    return False


def cmpAllLettersCaseInsesitive(haystack, needle, threshold=1.0):
    """Case insesitive. All (or threshold percent) needle letters are in the haystack and in almost (index-+1) correct order"""

    needle = needle.lower()
    haystack = haystack.lower()

    occurence = 0
    for i in range(len(needle)):
        char = needle[i]
        foundindex = haystack.find(char, i - 2 if i > 1 else 0, i + 2)
        if foundindex != -1:
            occurence += 1

    if occurence / len(needle) >= threshold:
        return True

    return False


def cmpAllLettersCaseInsesitiveList(haystack, needles, threshold=1.0):
    """Case insesitive. neddles is list of strings. All (or threshold percent) needle letters are in the haystack and in almost (index-+1) correct order"""

    needles = [x.lower() for x in needles if x]
    haystack = re.sub(r"\W+", "", haystack).lower()

    occurence = 0
    for needle in needles:
        c_occurence = 0
        needle_i = 0

        lastMatchIndex = 0
        matches = 0
        nomatches = 0
        i = 0
        while i < len(haystack):
            if haystack[i] in needle[needle_i -
                                     1 if needle_i > 0 else 0: needle_i + 2]:
                matches += 1
                needle_i += 1
                lastMatchIndex = i
            else:
                nomatches += 1
                needle_i += 1

            if matches / len(needle) >= threshold:
                break

            if nomatches == 3:
                needle_i = 1
                c_occurence = 0
                matches = 0
                nomatches = 0
                i = haystack.find(needle[0], lastMatchIndex + 1)
                lastMatchIndex = i
                if i == -1:
                    break

            i += 1

        occurence += matches

    if occurence / sum([len(needle) for needle in needles]) >= threshold:
        return True

    return False


def searchFct(textdata, query, cmp, *args, **kwargs):
    results = []
    for line in textdata:
        if cmp(line, query, *args, **kwargs):
            results.append(line)

    return results


def search(shortnamesId2Fullname, query):

    query = re.sub(r"\W+", " ", query).lower()  # Remove any non ascii
    queries = query.split(" ")

    return searchFct(
        shortnamesId2Fullname,
        queries,
        cmpAllLettersCaseInsesitiveList,
        threshold=0.8)


if __name__ == "__main__":
    from shortnames import shortnamesId2Fullname

    """shortnamesId2Fullname = {
        281: 'Heidelberg, Triplex-Mensa am Uniplatz',
        282: 'Heidelberg, zeughaus-Mensa im Marstall',
        283: 'Mannheim, Mensaria Metropol',
        284: 'Mannheim, Cafeteria KUBUS',
    }"""

    tests = ["Heidleberg Mnesa", "manhem mensu", "mensa südstadt"]
    for test in tests:
        ret = search(shortnamesId2Fullname.values(), test)
        print("Query:  %s" % test)
        print("Result: %s" % ret)
        print(" ")
