import re

def decrypt_php(text):
    pattern =r'(?!id\b)[a-zA-Z]{2,}|[0-9]+'
    result = re.findall(pattern, text)

    flag=False
    current_key=""
    mapping={}

    for i in result:
        if(i.isnumeric() and not flag):
            continue
        elif(flag and i.isnumeric()):
            if(current_key in mapping):
                mapping[current_key].append(i)
            else:
                mapping[current_key]=[i]
            flag=False
        else:
            current_key=i
            flag=True
    return mapping