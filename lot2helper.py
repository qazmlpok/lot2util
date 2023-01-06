# -*- coding: utf-8 -*-

import csv
import re
import math
import copy
import os
from lot2data import *
from lot2speed import Speed

#Miscellaneous functions and other crap.
#There's a bunch of "read-csv" functions that could probably be genericized.

LITTLE_ENDIAN = 'little'
BIG_ENDIAN = 'big'

#for Steam files
xorkey = b''
for i in range(0, 256):
    xorkey += i.to_bytes(1, 'little')
    #The decryption key is just 00..FF
assert len(xorkey) == 256
assert xorkey[0] == 0

def converttoint(bytes, size=4, endian=BIG_ENDIAN):
    result = 0
    for i in range(size):
        temp = bytes[i]
        if endian == LITTLE_ENDIAN :
            result |= (temp << (8*i))
        elif endian == BIG_ENDIAN :
            result = (result << 8) | temp
        else:
            raise Exception('converttoint: Unknown endian specification')

    return result

def convertfromint(value, size=4, endian=BIG_ENDIAN):
    #This was a helper method back from python 2 but 3 seems to have better handling.
    return value.to_bytes(size, endian)
    #result = ""
    #for i in range(size):
    #    if endian == LITTLE_ENDIAN :
    #        #result |= (temp << (8*i))
    #        temp = (value >> (8*i)) & 0x00FF
    #    elif endian == BIG_ENDIAN :
    #        #result = (result << 8) | temp
    #        temp = (value >> (8*(size-i-1))) & 0x00FF
    #    else:
    #        raise Exception('convertfromint: Unknown endian specification')
    #    result += chr(temp)
    #return result

def readbytes(infile, bytecount):
    position = infile.tell()
    bytes = infile.read(bytecount)
    if len(bytes) < bytecount:
        raise Exception("Couldn't read file. Starting position " + str(position))

    return converttoint(bytes, bytecount)
#
def writebytes(outfile, value, bytecount):
    position = outfile.tell()
    bytes = convertfromint(value, bytecount)
    written = outfile.write(bytes)
    if written < bytecount:
        raise Exception("Couldn't write to file. Starting position " + str(position))

    return

def loadSubclassBonuses():
    """Load a CSV file named subclass_bonuses.csv in the same directory."""
    filename = 'subclass_bonuses.csv'
    csvdata = {}
    with open(os.path.join('data', filename), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            #Headers: Name	ID	HP	MP	TP	ATK	DEF	MAG	MND	SPD	EVA	AFF	RES
            #Ignore name, that's just for viewing.
            for stat in boost_stats:
                #This if is the easiest way to get eva bonuses but skip acc
                if stat in row:
                    row[stat] = int(row[stat])
            del row['(Comment)']
            csvdata[int(row['ID'])] = row
    return csvdata
    

def loadCharacterBasestats():
    """Load a CSV file named LoT2_stat_growths.csv in the data directory.
    Loads basic data (base stats, growths, level/library cost)"""
    filename = 'LoT2_stat_growths.csv'
    csvdata = {}
    with open(os.path.join('data', filename), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            #Headers: ID 	Names	HP	ATK	MAG	DEF	MND	SPD	MP	MP growth	TP	EVA	HP regen	MP regen	Leveling rate	Library
            #Need to parse MP growth, since it's listed as a fraction.
            #Ignore name, that's just for viewing.
            for stat in stats:
                #Stats are listed as decimals here; I keep things consistent with in-game display. Multiply by 10.
                row[stat] = int(float(row[stat]) * 10)
            #mp growth is listed as a fraction.
            mpg = row['MP growth']
            m = re.match(r'^\s*1/(\d+)\s*$', mpg)
            if m:
                denom = int(m.group(1))
                row['MP growth'] = 1.0 / float(denom)
                row['MP growth denominator'] = denom
            else:
                raise Exception("Unexpected value in MP Growth cell: " + mpg)
            csvdata[int(row['ID'])] = row
    return csvdata

def loadCharacterSkills():
    """Load a CSV file named _character_skills.csv in the same directory."""
    #(Reminder, this file has unicode data, due to fancy word quotes and team (9) )
    #Need to group this file to {character}->[]
    filename = '_character_skills.csv'
    csvdata = {}
    with open(os.path.join('data', filename), 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            #Headers: Character	CharID	Name	ID	awakening	Cost	Max Lvl	Description	[All the stats]
            for stat in boost_stats:
                row[stat] = float(row[stat])
            row['Max Lvl'] = int(row['Max Lvl'])
            
            char_id = int(row['CharID'])
            row['CharID'] = char_id
            row['awakening'] = (row['awakening'] == 'True')
            id = int(row['ID'])
            row['ID'] = char_id

            if char_id not in csvdata:
                csvdata[char_id] = {}
            csvdata[char_id][id] = row
    return csvdata
    
def loadCharacterSpells():
    """Load a CSV file named _character_spells.csv in the data directory."""
    #Need to group this file to {character}->[]
    filename = '_character_spells.csv'
    csvdata = {}
    #sig since this has a bom
    with open(os.path.join('data', filename), 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            #Headers: Character	CharID	Name	ID	awakening	MP	Cost	Max Lvl	Target	Element	Damage Formula	ATK	MAG	DEF	MND	T.DEF	T.MND	Multiplier	Accuracy	Delay	Special	Notes
            char_id = int(row['CharID'])
            row['CharID'] = char_id
            row['awakening'] = (row['awakening'] == 'True')
            id = int(row['ID'])
            row['ATK'] = int(row['ATK'])
            row['MAG'] = int(row['MAG'])
            row['DEF'] = int(row['DEF'])
            row['MND'] = int(row['MND'])
            row['T.DEF'] = int(row['T.DEF'])
            row['T.MND'] = int(row['T.MND'])
            row['Multiplier'] = int(row['Multiplier'])
            row['ID'] = id

            if char_id not in csvdata:
                csvdata[char_id] = {}
            csvdata[char_id][id] = row
    return csvdata
#
def loadCharacterTitles():
    """Load a CSV file named titles.csv in the data directory."""
    filename = 'titles.csv'
    csvdata = {}
    with open(os.path.join('data', filename), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['ID'] = int(row['ID'])
            csvdata[row['ID']] = row
    return csvdata
#
#(Just main/sub equip, for stats. It's filtered)
def loadItemData():
    """Load a CSV file named titles.csv in the data directory."""
    filename = '_item_data.csv'
    csvdata = {}
    #sig since this has a bom
    with open(os.path.join('data', filename), 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['ID'] = int(row['ID'])
            csvdata[row['ID']] = row
    return csvdata
#

#This should be replaced with a spreadsheet but I can't be bothered to make one.
def hardcoded_subskill_boosts(id, skill, stat):
    if id == 113:       #Transcendent
        #HP, Attack, Defense, Magic, Mind and Speed base values are increased by (SLv).
        if skill == 1 and stat in ('HP', 'ATK', 'DEF', 'MAG', 'MND', 'SPD'):
            return 1
    #
    elif id == 122:     #WINNER
        #Increases all base stats by (SLv * 1.2).
        #(Is this "all stats"?)
        if skill == 1 and stat in ('HP', 'ATK', 'DEF', 'MAG', 'MND', 'SPD'):
            return 1.2
        #Increases all elemental affinities by (SLv * 4).
        if skill == 2 and stat == 'AFF':        #or is_affinity
            return 4
        #Increases all status resistances by (SLv * 2). 
        if skill == 3 and stat == 'RES':        #or is_resistance
            return 2
    #
    elif id == 114:     #Swordmaster
        #Increase Base ATK by 6, decrease MaxMP by 3 and Base HP by 6. 
        if skill == 1:
            if stat == 'ATK':
                return 6
            elif stat == 'MP':
                return -3
            elif stat == 'HP':
                return -6
            return 0
    #
    elif id == 115:     #Archmage
        #Increase Base MAG by 6, decrease MaxMP by 3 and Base HP by 6. 
        if skill == 1:
            if stat == 'MAG':
                return 6
            elif stat == 'MP':
                return -3
            elif stat == 'HP':
                return -6
            return 0
    #
    return 0

#Fake spells, used for calculating the speed chart. Only includes the used stats.
def fake_spell(name, id, delay, formula=''):
    return {'Name' : name, 'ID' : id, 'Delay' : delay, 'Damage Formula': formula}
attack_spell = fake_spell('Attack', -1, 7000, '100% ATK - 50% T.DEF')
magic_attack_spell = fake_spell('Attack', -1, 7000, '100% MAG - 50% T.MND')
formation_spell = fake_spell('Form Change', -2, 7500)
concentrate_spell = fake_spell('Concentrate', -3, 5000)
battle_start_spell = fake_spell('50%', -8, 5000)
empty_gauge_spell = fake_spell('0%', -9, 0)     #Levaetein did this in 1, but does anything do it in 2?



def get_spell_timing(delay, speed):
    """Get data on a spell's speed. Due to how the speed system works, only specific breakpoints
    will actually result in more actions. This is especially pronounced in the postgame.
    Returns the number of ticks a spell's delay actually represents,
    the minimum speed to maintain that speed,
    and the speed needed to actually reduce the tick count.
    """

    #"get_adjusted_delay" is actually post-use...
    delay = 10000 - delay
    
    speedobj = Speed(from_game_speed=speed)
    #real_speed = game_to_db(speed)
    
    #I was hoping to avoid this crap. Maybe I should add a Delay class too? That seems excessive.
    #ticks = math.ceil(delay / real_speed)
    ticks = delay / speedobj
    min = int(math.floor(delay / ticks))
    minspeed = Speed(from_real_speed=min)
    
    #Ordered list; [0] is "1 fewer tick", [1] is "2 fewer ticks", etc. Stops at ticks==1, or after 4 reductions
    next = []
    #Can't ever go faster than 1 tick.
    if (ticks > 1):
        tempspeed = copy.copy(speedobj)
        #Modify speed and figure out the next speed "breakpoints"
        for i in range(4):
            nextticks = delay / tempspeed

            if (nextticks == 1):
                break
            nextspd = int(math.ceil(delay / (nextticks-1)))
            tempspeed.SetValue(from_real_speed=nextspd)
            next.append({'Ticks' : nextticks-1, 'Speed' : tempspeed.GetGameValue()})
        #
    
    return {
        'Ticks' : ticks,
        'Min' : minspeed.GetGameValue(),
        'Next' : next,
    }

def format_spell_oneline(name, delay, formula, speed):
    """Helper function for turning a spell into a delay. Will also work for basic attack, starting at 50%, etc."""
    delaystr = str(delay).ljust(5)
    
    #"get_adjusted_delay" is actually post-use...
    data = get_spell_timing(delay, speed)
    #no spells have 0 delay. Being switched in can be 0 delay, but there's no need to account for that.
    
    ticks = data['Ticks']
    min = data['Min']
    
    ticksstr = str(ticks).ljust(3)
    minstr = str(min).ljust(6)
    
    prevstr = ('(-' + str(speed - min) + ')').ljust(9)
    
    #Longest spell is 31 characters: Jealousy of the Kind and Lovely
    spellname = name.ljust(31)
    
    if (ticks == 1):
        nextformat = 'Next:  MAX'
    else:
        entry = data['Next'][0]
        spd = entry['Speed']
        maxstr = str(spd).ljust(7)
        #nextticks = entry['Ticks']
        nextstr = ('(+' + str(spd - speed) + ')').ljust(9)
        
        nextformat = f"Next: {maxstr} {nextstr}"
    #
    
    s =  f"{spellname} - {delaystr} | Ticks: {ticksstr}    Min speed: {minstr} {prevstr} - {nextformat}"
    return s
#

def format_spell(name, delay, formula, speed):
    """Helper function for turning a spell into a delay. Will also work for basic attack, starting at 50%, etc."""
    delaystr = str(delay).ljust(5)
    
    data = get_spell_timing(delay, speed)
    ticks = data['Ticks']
    min = data['Min']

    prevstr = ('(-' + str(speed - min) + ')').ljust(9)
    nextformat = ''
    
    ticksstr = str(ticks).ljust(3)
    minstr = str(min).ljust(6)
    
    #Longest spell is 31 characters: Jealousy of the Kind and Lovely
    spellname = name.ljust(31)
    
    if (ticks == 1):
        nextformat = 'Next:  MAX'
    else:
        for i in range(len(data['Next'])):
            entry = data['Next'][i]
            spd = entry['Speed']
            nextticks = entry['Ticks']
            
            lead = f"{nextticks}"
            if i == 0:
                lead = 'Next'
            
            maxstr = str(spd).ljust(7)
            nextstr = ('(+' + str(spd - speed) + ')').ljust(9)
            nextformat += f"{lead}: {maxstr} {nextstr} "
    #
    
    lineone = f"{spellname} - {delaystr} | Ticks: {ticksstr} - Min speed: {minstr} {prevstr} | {formula}"
    linetwo = f"    {nextformat}"

    #s =  f"{spellname} - {delaystr} | Ticks: {ticksstr}    Min speed: {minstr} {prevstr} - Next: {maxstr} {nextstr}"
    return lineone + "\n" + linetwo + "\n"# + str(data)
#
