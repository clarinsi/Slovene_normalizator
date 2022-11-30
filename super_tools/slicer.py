def slicer(listsent, i, context=3, ctype="all", include_self=False):
    if ctype == "all":
        if len(listsent) < (context * 2):
            if include_self:
                return listsent[:i] + listsent[i:]
            else:
                return listsent[:i] + listsent[i + 1:]
        else:
            if i < context:
                if include_self:
                    return listsent[:i] + listsent[i:i + context + 1]
                else:
                    return listsent[:i] + listsent[i + 1:i + context + 1]
            elif i > (len(listsent) - context):
                if include_self:
                    return listsent[i - context:i] + listsent[i:]
                else:
                    return listsent[i - context:i] + listsent[i + 1:]
            else:
                if include_self:
                    return listsent[i - context:i] + listsent[i:i + context + 1]
                else:
                    return listsent[i - context:i] + listsent[i + 1:i + context + 1]
    elif ctype == "R":
        if len(listsent) < (context * 2):
            if include_self:
                return listsent[i:]
            else:
                return listsent[i + 1:]
        else:
            if i < context:
                if include_self:
                    return listsent[i:i + context + 1]
                else:
                    return listsent[i + 1:i + context + 1]
            elif i > (len(listsent) - context):
                if include_self:
                    return listsent[i:]
                else:
                    return listsent[i + 1:]
            else:
                if include_self:
                    return listsent[i:i + context + 1]
                else:
                    return listsent[i + 1:i + context + 1]
    elif ctype == "L":
        if len(listsent) < (context * 2):
            if include_self:
                return listsent[:i + 1]
            else:
                return listsent[:i]
        else:
            if i < context:
                if include_self:
                    return listsent[:i + 1]
                else:
                    return listsent[:i]
            elif i > (len(listsent) - context):
                if include_self:
                    return listsent[i - context:i + 1]
                else:
                    return listsent[i - context:i]
            else:
                if include_self:
                    return listsent[i - context:i + 1]
                else:
                    return listsent[i - context:i]
