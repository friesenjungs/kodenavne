import json

jsonWord = 'wordlists\\Word.json'
jsonBankWord = 'wordlists\\BankWord.json'
txtfileEng = 'wordlists\\english.txt'
txtfileGer = 'wordlists\\deutsch.txt'
listEng = []
listGer = []
count = 1
listObjWord = []
listObjBankWord = []

with open(jsonWord) as jw:
    listObjWord = json.load(jw)

with open(jsonBankWord) as jbw:
    listObjBankWord = json.load(jbw)

with open(txtfileEng) as ef:
    listEng = ef.readlines()

with open(txtfileGer) as gf:
    listGer = gf.readlines()

for line in listEng:
    listObjWord.append({
        "word_id": count,
        "word_content": line.rstrip("\n")
    })
    listObjBankWord.append({
        "word_id": count,
        "wordbank_id": 1
    })
    count += 1

for line in listGer:
    listObjWord.append({
        "word_id": count,
        "word_content": line.rstrip("\n")
    })
    listObjBankWord.append({
        "word_id": count,
        "wordbank_id": 2
    })
    count += 1

with open(jsonWord, 'w') as json_file:
    json.dump(listObjWord, json_file, indent=4, separators=(',',': '))

with open(jsonBankWord, 'w') as json_file:
    json.dump(listObjBankWord, json_file, indent=4, separators=(',',': '))
