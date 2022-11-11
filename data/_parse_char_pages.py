#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Parse the HTML of the wiki character pages to get skill information.

import re
import os

from lot2helper import *

#import HTMLParser
from bs4 import BeautifulSoup, Comment, NavigableString

#Except not always. Yay for consistency.
#times_10_stats = [
#    'HP',
#    'ATK',
#    'DEF',
#    'MAG',
#    'MND',
#    'SPD',
#]

stat_mapping = {
    'HP' : 'HP',
    'ATTACK' : 'ATK',
    'DEFENSE' : 'DEF',
    'MAGIC' : 'MAG',
    'MIND' : 'MND',
    'SPEED' : 'SPD',
    'EVADE' : 'EVA',
    'EVASION' : 'EVA',
    'AFFINITY' : 'AFF',
    'AFFINITIES' : 'AFF',
    'ACCURACY' : 'ACC',
    'RESISTANCE' : 'RES',
    'RESISTANCES' : 'RES',
}

#Remove extra spaces, remove tabs, remove newlines. Web browsers typically do this.
def normalize(inp):
    inp = str(inp)  #Just in case.
    inp = inp.strip()
    inp = re.sub(r'[ \s\n\r]+', ' ', inp)
    
    return inp

#For more genericness, could add headers as a parameter.
def _tbody_to_dict(body, headerrow=1):
    """Helper method to convert a table to a dictionary. Uses the first (or second) row as headers, everything below as value.
    Returns an array of dictionaries"""
    ret = []
    
    trs = body.find_all('tr', recursive=False)
    if (len(trs) == 0):
        return ret
    #Skip the first tr, it's the header text
    #Second tr is the header
    
    #for x in trs: print(x)
    
    headers = [normalize(x.get_text()) for x in trs[headerrow].find_all(['th','td'])]

    for i in range(headerrow+1, len(trs)):
        tr = trs[i]
        #data = [normalize(x.get_text()) for x in tr.find_all(['th','td'])]
        data = [normalize("|".join(x.stripped_strings)) for x in tr.find_all(['th','td'])]
        asdict = {headers[j]:data[j] for j in range(len(data))}
        
        ret.append(asdict)
    return ret

def parse_skill_tbody(body, headerrow=1, character=None):
    """Returns a list of skills from a <tbody> node. Should work on both basic and awaken skills."""
    skills = _tbody_to_dict(body, headerrow)
    
    #Do post-processing;
    #Add an entry for every stat, then try to parse the description to get proper values.
    
    #This is too complicated. Switch to multiple groups.
    #statregex = re.compile(r"Increases? the user's(?: base)? ([A-Za-z]+) by \(SLv ?\*? ?([\d.]*)\),?\s*(?: and(?: the user's)? ([A-Za-z]+) by \(SLv ?\*? ?([\d.]*)\))?", re.IGNORECASE)
    statregex = re.compile(r"([A-Za-z]+)\s*(?:(?:is|are) increase(?:s|d)?)?\s*by \(SLv ?\*? ?([\d.]*)\)", re.IGNORECASE)
    
    #Most: Increase the user's Evade by (SLv * 6), Attack by (SLv * 1) and Speed by (SLv * 1).
    #Iku:  The user's base MAG is increased by (SLv * 8).
    #Byak: The user's elemental affinities are increased by (SLv * 6).
    
    for skill in skills:
        skill['Max Lvl'] = int(skill['Max Lvl'])
        skill['Cost'] = int(skill['Cost'])
        for x in boost_stats:
            skill[x] = 0
            
        #Remove |
        #skill['Name'] = skill['Name'].replace('|', ' ') #I think this got renamed?
        if '|' in skill['Name']:
            skill['Name'] = skill['Name'].split('|')[1].strip('()')
        skill['Description'] = skill['Description'].replace('|', ' ')
        

        #Try to match the regex. The descriptions aren't fully standardized, but might be close enough.
        #print(skill['Description'])
        
        #I switched to findall instead of search, so this isn't really needed as a separate function anymore.
        def handle_regex_results(stat, value):
            #Do the thing with the output of statregex
            stat = stat.upper()
            if stat in stat_mapping:
                #Magic -> MAG, etc
                stat = stat_mapping[stat]
                
            if value == '':
                value = 1
            
            value = float(value)
            
            #ok, this is really annoying. MOST skills use the in-game stat numbers, e.g. "The user's base MAG is increased by (SLv * 8).". But a small number don't! "Increase the user's Evade by (SLv * 8) and Magic by (SLv * 1.2). "
            #so just assume that if the final value would be over 20, it's already in-game.
            #if stat in times_10_stats and value < 2.0:
            #    value = value*10
            #assert float(value) == float(int(value))        #No decimals should have survived.
            
            return (stat, value)
        #
        
        if re.search(r'\b(when|while|if)\b', skill['Description'], re.IGNORECASE):
            pass
            #Filter out conditional stat bonuses (kinship, etc)
        elif skill['Description'] == "Increase all of user's base stats by (SLv * 1).":
            #Keine special case. Not MP, TP, EVA, and probably not acc.
            for x in stats:
                skill[x] = 1
        elif skill['Description'] == "Increase the user's all base stats by (SLv * 2).":
            #Ran special case. Not explicitly checked but probably same as Keine's
            #(This is awkwardly worded; probably a copy/paste issue. It might get fixed at some point.)
            for x in stats:
                skill[x] = 2
        else:
            res = re.findall(statregex, skill['Description'])
            for tup in res:
                stat, value = handle_regex_results(tup[0], tup[1])
                
                #Ensure it's a valid stat
                if stat in stat_index:
                    skill[stat] = value
                else:
                    #print("Probably false positive in stat-skill match: " + stat + ", from: " + skill['Description'])
                    pass
        #

    for x in skills:
        x['awakening'] = False
    return skills
    

#
def parse_spell_tbody(body, headerrow=1, character=None):
    """Returns a list of spells from a <tbody> node. Should work on both basic and awaken spells."""
    spells = _tbody_to_dict(body, headerrow)
    
    target_map = {
        'Enemy (One)' : 'Enemy',
        'Enemy (Row)' : 'Row',
        'Enemy (All)' : 'Enemies',
        'Ally (One)'  : 'Ally',
        'Ally (All)'  : 'Allies',
        'Allies (All)'  : 'Allies',
        'Enemy and Allies (All)' : 'All',
        'Self'        : 'Self',
    }
    
    #Do post-processing; convert "target" into a single word (a bit easier to parse after the fact)
    for spell in spells:
        #Cleanup: <br /> was replaced with | (kinda) during _tbody_to_dict.
        #Undo this for some.
        #For others, use the | to find plus-disk corrections.
        
        spell['Special'] = spell['Special'].replace('|', ' ')
        spell['Notes'] = spell['Notes'].replace('|', ' ')
        spell['Target'] = spell['Target'].replace('|', ' ')
        spell['Name'] = spell['Name'].replace('|', ' ')
    
        #Fix plus-disk MP corrections...  `5(6)`
        if '|' in spell['MP']:
            spell['MP'] = spell['MP'].split('|')[1].strip('()')
        spell['MP'] = int(spell['MP'])
        
        if '|' in spell['Damage Formula']:
            #Yukari has different formula for Yakumo+
            #Take the first one.
            if spell['Name'] == 'Shikigami "Ran Yakumo +"':
                #With chen / Ran; three versions. Grab the first.
                spell['Damage Formula'] = spell['Damage Formula'].split('|')[0]
            elif spell['Name'] == 'Overflowing Unnatural Power':
                #This is self damage.
                spell['Damage Formula'] = ''
            elif spell['Name'] in ('Youkai Yakuza Kick', 'The Count of Monte Cristo',"Musketeer d'Artagnan","Non-Neumann Systems"):
                #These are split into Reading/Non-Reading. Grab non.
                spell['Damage Formula'] = spell['Damage Formula'].split('|')[0]
            else:
                #These are plus-disk changes.
                spell['Damage Formula'] = spell['Damage Formula'].split('|')[1].strip('()')
        #

        
        #A handful of Element changes; same deal
        if '|' in spell['Element']:
            spell['Element'] = spell['Element'].split('|')[1].strip('()')
        #Kokoro has a dual element skill as well.
        
        #Delay. Also strip the %
        if '|' in spell['Delay']:
            if spell['Name'] in ('The Count of Monte Cristo',"Musketeer d'Artagnan","Non-Neumann Systems"):
                #These are split into Reading/Non-Reading. Grab non.
                spell['Delay'] = spell['Delay'].split('|')[0]
            else:
                #These are plus-disk changes.
                spell['Delay'] = spell['Delay'].split('|')[1].strip('()')
        #
        
        if spell['Delay'] == 'X%':
            #Just leave it as this. (Yukari Yakumo's spiriting away)
            spell['Delay'] = 0
        elif '%' in spell['Delay']:
            delay = spell['Delay'].replace('%', '')
            spell['Delay'] = int(float(delay) * 100)
            #Actually this is post-use gauge but whatever.
        else:
            raise Exception("No % in delay? " + spell['Delay'])
        
        spell['Target'] = target_map[spell['Target']]
        if 'Cost' not in spell:
            spell['Cost'] = 5
            #I thiiink all default spells cost 5. 
        else:
            spell['Cost'] = int(spell['Cost'])
            
        print(spell['Notes'])
    
    for x in spells:
        x['awakening'] = False
    return spells
#

def parse_awakening_tbody(body, character=None):
    #Awakenings are two tables combined in one. How annoying.
    #Gotta do the buckets again. For reuse of the other functions, make two dummy tbodies to hold the data.

    spell_bucket = soup.new_tag('tbody')
    skill_bucket = soup.new_tag('tbody')
    bucket = None

    ret = []
    
    trs = body.find_all('tr', recursive=False)
    
    for i in range(len(trs)):
        tr = trs[i]
        #Can't use .children or .contents due to whitespace. bleh
        children = tr.find_all(['td', 'th'])
        
        if (len(children) == 1):
            #This is a header row; there's a single td or th containing text
            
            text = normalize(children[0].get_text())
            #print(text)
            if (text == 'Spells'):
                bucket = spell_bucket
            elif (text == 'Skills'):
                bucket = skill_bucket
            elif (text == 'Comments'):
                break
            else:
                #Probably "Awakened Skills"
                pass
            continue
        
        bucket.append(tr)

    spells = parse_spell_tbody(spell_bucket, 0, character=character)
    skills = parse_skill_tbody(skill_bucket, 0, character=character)
    
    for x in spells:
        x['awakening'] = True
    for x in skills:
        x['awakening'] = True

    return (spells, skills)
#
def get_character_id(name):
    #kinda hackish, but it should work.
    #For the given name, check all of the entries in the characters list for a partial match.
    #The names I dumped in there are short, and I'd rather use those 99% of the time so I don't want to expand it to full names.
    for id in character_ids:
        testname = character_ids[id]
        if re.search(r'\b' + testname + r'\b', name):
            return id
        #Try the other way (not likely, but...)
        if re.search(r'\b' + name + r'\b', testname):
            return id
    raise Exception("Couldn't get id for " + name)
#


sourcedir = 'html'
#sourcefile = 'Characters_2.html'        #TODO: Loop.

character_data = []
for i in range(1, 8):
    sourcefile = ('Characters_%d.html' % i)
    fullpath = os.path.join(sourcedir, sourcefile)
    with open(fullpath, 'r', encoding='utf-8') as f:
        html = f.read()
        soup = BeautifulSoup(html, 'html5lib')
        
        #the HTML isn't heirarchical, and there's no meaningful IDs.
        #It should be possible to split this into sections by headers;
        
        #<h2><span class="mw-headline" id="Reimu_Hakurei"></span></h2>
        #(There's more to it but it's too long)
        #There's also just a <h2>contents</h2>. bleh
        #and a Navigation Menu... just test for the span
        
        headers = soup.find_all('h2')
        filtered = {}
        first = None
        for i in range(len(headers)):
            h = headers[i]
            if h.span is None:
                continue
            #Use the last span if there are multiples. Eiki's name screws things up. 
            #character = h.span.a.get_text()
            spans = h.find_all('span', recursive=False)
            character = spans[-2].a.get_text()
            #print (character)
            #filtered.append(h)
            filtered[h] = character
            if first == None:
                first = h
        #
        #print (filtered[0].parent)
        #All have the same parent (makes sense), and I believe this covers the entire contents of the page.
        buckets = {}
        target = None
        for i in range(len(first.parent.contents)):
            elem = first.parent.contents[i]
            
            if type(elem) == 'Comment':
                #print("Skip comment")
                continue
            if (isinstance(elem, NavigableString) and re.match(r'^[\s\n\r]+$', str(elem))):
                #print("Skip whitespace")
                continue
            
            if elem.name == 'h2':
                if elem in filtered:
                    target = filtered[elem]
                    buckets[target] = []
                else:
                    target = None
                continue
            #
            #This turned out to be a single <div> and a <table>, and only the table is needed. So just keep the table (tbody, actually).
            #(The div contains the picture, if I wanted to scrape those or something. But it's already in the dxa archive...)
            if target:
                if elem.name == 'table':
                    buckets[target] = elem.tbody
        #
        
        #Turns out there's only two elements: a div (which has the picture) and a table (literally everything else)
        #Then the table has a bunch of sub tables and shit.
        
        i = 0
        #for x in buckets['Rinnosuke Morichika'].find_all('tr', recursive=False):    #Reimu Hakurei
        #    #These are all tbody; only child is <tr> (and whitespace, which we want to skip...)
        #    #[0] Character title
        #    #[1] "Base Stats"
        #    #[2] Headers for the following 3 tables: Battle Stats, Status Resistances, Elemental Affinities
        #    #[3] Those 3 tables.
        #    #[4] Table containing Spell Cards (the text "Spell Cards" is in the first row of that table)
        #    #[5] Table containing Skills (the text "Skills" is in the first row of that table)
        #    #[6] Blank   --Not always present. Great.
        #    #[7] Text: Character Overview and Comments
        #    #[8] Two tables. The first is the "overview and comments". The second is Awakened Skills. Only need the second.
        #    #   This table will be different if the character has spells or not. Pretty sure everyone has skills. (Rinnosuke has both, Reimu has only skills)
        #    
        #    #print (x)
        #    #print("\n\t", i, "\n")
        #    #i += 1
        #    pass
        #
        for character in buckets:
            elem = buckets[character]
            title = elem.tr.i.get_text()
            print(character,'-',title)
            print()
            
            char_id = get_character_id(character)
            
            spells_str = elem.find(string=re.compile("^\s*Spell Cards\s*$"))
            spells = spells_str.find_parent('tbody')
            spells = parse_spell_tbody(spells, character=character)
            
            skills_str = elem.find(string=re.compile("^\s*Skills\s*$"))
            skills = skills_str.find_parent('tbody')
            skills = parse_skill_tbody(skills, character=character)

            awakening_str = elem.find(string=re.compile("^\s*Awakened Skills\s*$"))
            awakening = awakening_str.find_parent('tbody')
            (a_spells, a_skills) = parse_awakening_tbody(awakening, character=character)
            
            #print(a_skills)
            #print()
            #print(a_spells)

            if len(a_skills) > 0:
                skills.extend(a_skills)
            if len(a_spells) > 0:
                spells.extend(a_spells)
                

            
            #Assign skill IDs.   (these notes are 1-indexed; subtract 1)
            #Rules:
            #1-12: Boost skills, in order (need stat lookup)
            #19, 20: Motivated Heart and Hands-on Experience, which everyone has
            #21-30: skills
            #31-40: spells
            #No separation between awakening and not, other than awakening always appearing after non-awakening.
            id = 20
            for skill in skills:
                if skill['Name'].endswith('Boost'):
                    stat = skill['Name'].split(' ')[0]      #MP Boost or MP High Boost; just take the first word
                    stat = stat.upper()
                    #Then do a Magic -> MAG lookup.
                    if stat in stat_mapping:
                        stat = stat_mapping[stat.upper()]
                    skill['ID'] = stat_index[stat]
                elif skill['Name'] == 'Motivated Heart':
                    skill['ID'] = 18
                elif skill['Name'] == 'Hands-on Experience':
                    skill['ID'] = 19
                else:
                    skill['ID'] = id
                    id += 1
                skill['Character'] = character
                skill['CharID'] = char_id
            assert id <= 30
            id = 30
            for spell in spells:
                spell['ID'] = id
                spell['Character'] = character
                spell['CharID'] = char_id
                id += 1
            assert id <= 40
            
            #It should be possible to use the same function for spellcards and then for awaken spell cards.
            #Ditto skills.
            
            #print(spells)

            #print(skills)
            #print(awakening)
            
            entry = {
                'Name': character,
                'Spells': spells,
                'Skills' : skills,
            }
            character_data.append(entry)
    #(with open)

#Don't create files
#exit()


spell_cols = ['Character', 'CharID', 'Name', 'ID', 'awakening', 'MP', 'Cost', 'Target', 'Element', 'Damage Formula', 'Delay', 'Special', 'Notes']
skill_cols = ['Character', 'CharID', 'Name', 'ID', 'awakening', 'Cost', 'Max Lvl', 'Description']    
skill_cols.extend(boost_stats)


with open('_character_spells.csv', 'w', encoding='utf-8', newline='') as f:
    f.write('\ufeff')       #force BOM
    writer = csv.DictWriter(f, fieldnames = spell_cols, extrasaction='ignore')
    writer.writeheader()
    for c in character_data:
        spells = c['Spells']
        for s in spells:
            writer.writerow(s)
#
with open('_character_skills.csv', 'w', encoding='utf-8', newline='') as f:
    f.write('\ufeff')       #force BOM
    writer = csv.DictWriter(f, fieldnames = skill_cols, extrasaction='ignore')
    writer.writeheader()
    for c in character_data:
        skills = c['Skills']
        for s in skills:
            writer.writerow(s)
#


