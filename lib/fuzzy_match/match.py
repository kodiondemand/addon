#!/usr/bin/env python
# encoding: utf-8
import heapq
from . import algorithims



def extract(query, choices, match_type='trigram', score_cutoff=0, limit=5):
    """
    Find the similarity between a query item and a list of choices.
    Returns a tuple of all choices and their associated similarity score.

     Arguments:
        query: The string you are wanting to match.
        choices: An iterable or dictionary-like object containing choices
            to be matched against the query.
        score_cutoff: Optional argument for score threshold. If the best
            match is found, but it is not greater than this number, then
            return None anyway ("not a good enough match").  Defaults to 0.

    """
    try:
        if match_type == 'trigram':
            match_type = algorithims.trigram
        elif match_type == 'levenshtein':
            match_type = algorithims.levenshtein
        elif match_type == 'cosine':
            match_type = algorithims.cosine
        elif match_type == 'jaro_winkler':
            match_type = algorithims.jaro_winkler
        try:
            if choices is None or len(choices) == 0:
                return
        except TypeError:
            pass

        results = []
        
        for i in choices:
            score = (match_type(query, i))
            data = (i, score)
            if score >= score_cutoff:
                results.append(data)


        return heapq.nlargest(limit, results, key=lambda i: i[1]) if limit is not None else \
            sorted(results, key=lambda i: i[1], reverse=True)

        # return results

    except:
        return None


def extractOne(query, choices, match_type='trigram', score_cutoff=0):
    """
    Finds the most similar item to query item from a list of choices.
    Returns tuple of best choice and its associated similarity score.

     Arguments:
        query: The string you are wanting to match.
        choices: An iterable or dictionary-like object containing choices
            to be matched against the query.
        score_cutoff: Optional argument for score threshold. If the best
            match is found, but it is not greater than this number, then
            return None anyway ("not a good enough match"). Defaults to 0.

    """

    try:
        best_list = extract(query, choices, match_type, score_cutoff)

        best = max(best_list, key=lambda i: i[1])

        return best

    except:
        return None