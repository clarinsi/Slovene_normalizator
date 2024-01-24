#standardize quotation marks

def standardize_quotes(sent):
    types_of_quotes=["»", "«", "“", "‘‘", "‘", "„", "``", "`", "''", "”", "’’", "’"]
    for q in types_of_quotes:
        sent=sent.replace(q, '"')
    return sent
