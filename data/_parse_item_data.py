#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import csv

#Open _itemdata_json.txt and read in all of the data
#Then parse it to figure out what stats each item boosts
#Then write it to a csv. A csv is easier to filter, and everything else is a csv.
#itemdata_jp might be easier to parse, maybe?

number_regex = re.compile(r'^[+-]([\d.]+)(%)?')

def id_to_type(id):
    id = int(id)
    if id <= 60:
        #Main equipment: 1-60
        return 'main'
    if id >= 201 and id <= 440:
        return 'sub'
    #materials; these don't have stat boosts.
    if id >= 501 and id <= 600:
        return 'material'
    #Key items; also no stat boosts.
    #It'd be worth making a list of notable key items, e.g. the gems, tomes, etc
    if id >= 801 and id <= 980:
        return 'key'
    return 'unknown'

def load_item_data(fname):
    with open(fname, 'r') as f:
        data = f.read()
        itemdata = json.loads(data)
        #Fix the mangling of one item. Only do it if using english data (i.e. check name)
        powerdragon = itemdata["425"]
        if powerdragon['Name'] == "Power Dragon Scalemail":
            powerdragon['Desc3'] = '---'
            powerdragon['Desc4'] = 'HP/ATK/MND +330% DEF +660% FIR/CLD/WND/NTR +100 MYS/SPI/DRK/PHY +40'
        elif powerdragon['Name'] != u'パワードラゴンスケイルメイル':
            raise Exception("Unknown name for what should be Power Dragon Scalemail")
        
        #Quick pre-processing.
        for id in itemdata:
            item = itemdata[id]
            item['ID'] = id
            item['Type'] = id_to_type(id)
    return itemdata

#Data
stats = [
    'HP',
    'HP Recovery Rate',     #also HP Rec. Rate
    'MP',       #Frequently [Maximum ]MP
    'MP Recovery Rate',     #also MP Rec. Rate
    'TP',       #Frequently [Maximum ]TP
    'ATK',
    'DEF',
    'MAG',
    'MND',
    'SPD',
    'EVA',
    'ACC',
]
#Double check.
all_stats = [
    'HP',
    'ATK',
    'DEF',
    'MAG',
    'MND',
    'SPD',
]
affinities = [
    'FIR',
    'CLD',
    'WND',
    'NTR',
    'MYS',
    'SPI',
    'DRK',
    'PHY',
]
#(and void, but you can't raise that.)
resistances = [
    'PSN',
    'PAR',
    'HVY',
    'SHK',
    'TRR',
    'SIL',
    'DTH',
    'DBF',
]

mapping = {
    'All Ailments' : resistances,
    'All Resistances' : resistances,
    'All Resist' : resistances,
    'All Affinities' : affinities,
    'All stats' : all_stats,
    'Maximum MP' : 'MP',
    'Maximum TP' : 'TP',
    'HP Rec. Rate' : 'HP Recovery Rate',
    'HP Recovery' : 'HP Recovery Rate',
    'MP Rec. Rate' : 'MP Recovery Rate',
    'MP Recovery' : 'MP Recovery Rate',
}

for x in (affinities+resistances+stats):
    mapping[x] = x
#
all_base_values = []
for x in all_stats:
    base = x + ' Base Value'
    mapping[base] = base
    all_base_values.append(base)
mapping['All Stats Base Values'] = all_base_values  #Egg
mapping['All Base Values'] = all_base_values  #Tokugawa Statue (I changed it to match Egg)
#

#Probably not the best way to handle it...
for x in affinities:
    mapping[x + ' Damage dealt'] = 'Special'

#Get the keys. Sort by length (desc). Match "HP Recovery Rate" in favor of just "HP"
map_keys = list(mapping.keys())
map_keys = sorted(map_keys, key=lambda x: len(x), reverse=True )

itemdata = load_item_data('_itemdata_json.txt')

def parse_item_string(inp):
    special = []
    orig_inp = inp
    inp = inp.strip()
    ret = {}
    
    #Special case: Give up if it says "Adds x effect to all attacks"
    #if inp.find('effect to all attacks') != -1:
    #    return {'Special' : inp}
    #if inp == 'Reduces damage taken by 8% of max HP, occasionally negates damage':
    #    return {'Special' : inp}
    #if inp == 'Recovers 4% HP when attacking an enemy':
    #    return {'Special' : inp}
    #if inp == 'Occasionally prevents MP consumption':
    #    return {'Special' : inp}
    
    while inp != '':
        #If there are no numbers left, dump everything into special. 
        m = re.search(r'[0-9]', inp)
        if m is None:
            special.append(inp)
            break
        found_stats = []
        match = find_first_match(inp)
        if match is not None:
            #Oops this might need to be case insensitive. Maybe the source data happens to be consistent...
            stat = mapping[match]
            found_stats.append(stat)
            
            #Remove the match
            inp = inp[len(match):].strip()
            while inp[0] == '/':
                inp = inp[1:]
                #Next token should also be a perfect match.
                nextmatch = find_first_match(inp)
                if nextmatch is None:
                    raise Exception("Error parsing / in " + orig_inp + " - got to: " + inp)
                stat = mapping[nextmatch]
                found_stats.append(stat)
                inp = inp[len(nextmatch):].strip()
            
            #Next should be the value. This should start with a +, then digits, then maybe end in a %
            if inp[0] != '+' and inp[0] != '-':
                raise Exception("Error parsing " + orig_inp + " - expected a + at: " + inp)
            word, inp = (inp+' ').split(' ', 1)
            m = number_regex.match(word)
            if m:
                number = float(m.group(1))
                perc = m.group(2)
                
                if word[0] == '-':
                    number *= -1
                
                if (found_stats[0] == all_stats or found_stats[0] in all_stats) and perc is None:
                    print("Stats doesn't have a % when one was expected: ", found_stats, word)
                elif (found_stats[0] != all_stats and found_stats[0] not in all_stats) and perc is not None:
                    print("Stats has a % when one was not expected: ", found_stats, word)
                
                for s in found_stats:
                    if s == 'Special':
                        special.append(match)
                        special.append(word)
                    elif type(s) == str:
                        ret[s] = number
                    else:
                        #Compound. Iterate over everything and add all of those.
                        for x in s:
                            ret[x] = number
            else:
                raise Exception("Regex failed on word " + word + "  from " + orig_inp)
            
        else:
            #Grab the whole word
            extra, inp = (inp+' ').split(' ', 1)
            special.append(extra)
        inp = inp.strip()
    ret['Special'] = " ".join(special)
    
    return ret
        
def find_first_match(inp):
    #Loop over map_keys and find the first match. Return None if no match.
    #Case insensitive.
    #This has to be a list, not a dict, because the order matters. A longer match must be presented if available
    #This is specifically for "HP Recovery Rate" versus "HP"
    
    #Return value is the matched key; this is needed to know how many characters to skip ahead.
    inp = inp.upper()
    for k in map_keys:
        #ku = k.upper()
        m = re.search(r'^' + k + r'\b', inp, re.IGNORECASE)
        #if (inp).startswith(ku):
        if m:
            return k
    return None


for id in itemdata:
    item = itemdata[id]
    if (item['Type'] != 'main' and item['Type'] != 'sub'):
        continue 
    
    itemtext = item['Desc4']
    result = parse_item_string(itemtext)
    
    for x in (stats+all_base_values+affinities+resistances):
        #item[x] = ''
        item[x] = 0
    
    for x in result:
        item[x] = result[x]
    #item['Stats'] = result     #It's easier to read like this.
    #print(item)
    #print()
    
    #Plan: Check the start of the string for a match in map_keys. Favor start; there may be multiple matches
    #If there is no match, skip to next space.
    #If there is a match, consume it. Then consume next "word", which _should_ be +x or +x%
    #If there is a match, check for a / and split on that; everything should be an exact key match
    #If no match is found, add it to a "special" key. This will be stuff like "Occasionally deals double damage"
    #   or "Damage dealt +20% Damage taken -20%"
#

item_cols = [
    'ID',
    'Name',
    'Type',
] + stats+all_base_values+affinities+resistances + [
    'Special',
    'Desc1',
    'Desc2',
    'Desc3',
    'Desc4',
]
with open('_item_data.csv', 'w', encoding='utf-8', newline='') as f:
    f.write('\ufeff')       #force BOM
    writer = csv.DictWriter(f, fieldnames = item_cols, extrasaction='ignore')
    writer.writeheader()
    #I feel like this is already sorted. But it shouldn't be guaranteed.
    ids = itemdata.keys()
    for id in sorted(ids, key=lambda x: int(x)):
        item = itemdata[id]
        if (item['Type'] != 'main' and item['Type'] != 'sub'):
            continue
        writer.writerow(item)
#


    

#test = parse_item_string(itemdata["427"]['Desc4'])
#print(test)
#print(itemdata["427"]['Desc4'])
#
#print()
#
#test = parse_item_string(itemdata["414"]['Desc4'])
#print(test)
#print(itemdata["414"]['Desc4'])
#
#print()
#
#test = parse_item_string(itemdata["411"]['Desc4'])
#print(test)
#print(itemdata["411"]['Desc4'])
#
#print()
#
#test = parse_item_string(itemdata["426"]['Desc4'])
#print(test)
#print(itemdata["426"]['Desc4'])
#
#print()
#
#test = parse_item_string(itemdata["319"]['Desc4'])
#print(test)
#print(itemdata["319"]['Desc4'])

#print()
#
#test = parse_item_string(itemdata["302"]['Desc4'])
#print(test)
#print(itemdata["302"]['Desc4'])

#print(affinities+resistances+stats+all_base_values)

