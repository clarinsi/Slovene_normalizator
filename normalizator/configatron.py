#CONFIGATRON
#if set, override set, ignore incl, excl
def extended_bool(inp):
    if isinstance(inp, bool): return True
    if isinstance(inp, str) and inp.lower() in ["true", "false"]: return True
    
def boolify(inp):
    if isinstance(inp, bool): return inp
    if isinstance(inp, str):
        if inp.lower() in ["true"]: return True
        if inp.lower() in ["false"]: return False


def configatron(base_config, custom_config):
    config=base_config.copy()
    for key in custom_config:
        if key=="num":
            if isinstance(custom_config[key], dict) and isinstance(config[key], dict):
                if "normalize" in custom_config["num"] and boolify(custom_config["num"]["normalize"])!=boolify(config["num"]["normalize"]):
                    #če je drugač, zamenjaj
                    config["num"]["normalize"]=custom_config["num"]["normalize"]
                if boolify(config["num"]["normalize"]):
                    if "subtypes" in custom_config["num"]:
                        for k in custom_config["num"]["subtypes"]:
                            if k in config["num"]["subtypes"]:
                                for underkey in custom_config["num"]["subtypes"][k]:
                                    if underkey in config["num"]["subtypes"][k]:
                                        config["num"]["subtypes"][k][underkey]=custom_config["num"]["subtypes"][k][underkey]
                                    else:
                                        raise ValueError("Wrong key in config, check again.")
                            else:
                                raise ValueError("Wrong key in config, check again.")
        elif key in config:
            if isinstance(custom_config[key], dict) and isinstance(config[key], dict):
                minidict=custom_config[key]
                for minikey in minidict:
                    if minidict[minikey] and minikey in config[key]:
                        config[key][minikey]=minidict[minikey]
                    elif minikey=="include" and minidict[minikey]:
                        #TODO: če bo set LEVEL UP, spremeni še to DONE
                        config[key]["set"]={**config[key]["set"], **custom_config[key]["include"]}
                    elif minikey=="exclude" and minidict[minikey]:
                        [config[key]["set"].pop(x) for x in custom_config[key]["exclude"] if x in config[key]["set"]]
            elif extended_bool(custom_config[key]) and extended_bool(config[key]):
                config[key]=custom_config[key]
            else:
                raise ValueError("Wrong key in config, check again.")
            
        else:
            print(key.upper() +" is not in config. Did you mean something else?")
    return config
