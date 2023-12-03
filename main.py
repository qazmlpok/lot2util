#!/usr/bin/env python
# -*- coding: utf-8 -*-

# "E:\qazmlpok\Touhou Project\Labyrinth of Touhou2_PlusDisk\save\save1"
# C:\Users\Qaz\AppData\Roaming\CUBETYPE\tohoLaby\save1.dat

from lot2character import Character
from lot2save import Save
from lot2speed import Speed
import lot2data

import os
import sys

import copy

#Helper functions
def reimu_to_target(target):
    reimu = copy.copy(saveobj.get_character('Reimu'))
    old_xp = reimu.get_total_xp()
    reimu.level = target
    reimu.exp = 0
    xp = reimu.get_total_xp()
    return xp - old_xp
#
def gems_if_below(target):
    for c in saveobj.all_characters:
        for x in lot2data.gem_stats:
            if c.gems[x] < target:
                print("Giving", c.name, target, "gems for",x, ", from", c.gems[x])
                c.gems[x] = target
#
def check_stones():
    events = saveobj.events.all_events()
    as_dict = {}
    for e in events:
        event = events[e]
        name = event['Event']
        if name != 'Stone of Awakening':
            continue
        as_dict[event['Floor']] = event
    #There's no other way to sort 11F/10F correctly.
    order = [
        '6F',
        '7F',
        '8F',
        '9F',
        '10F',
        '11F',
        '12F',
        '13F',
        '14F',
        '15F',
        '11F Extra',
        '10F Extra',
    ]
    meanings = {
        0: 'Hidden',
        1: 'Available',
        2: 'Obtained',
    }
    counter = 0
    for o in order:
        event = as_dict[o]
        
        print(f"{event['Floor']}: {meanings[event['value']]}")
        if event['value'] == 2:
            counter += 1
    print(f"Obtained: {counter} / 12 Stones of Awakening")
#
def round_up_ic(saveobj):
    #It's being reported as "40", for "Start on floor: 41"
    #So I guess it needs to "round up" to xx9.
    #I'm not positive ic_avail works correctly. I think I was getting weird data in there once.
    if saveobj.misc_data.ic_avail and saveobj.misc_data.ic_floor > 0:
        return (((saveobj.misc_data.ic_floor+10) // 10)*10) - 1
    else:
        print("IC doesn't appear to be available.")
#Main program. Keep any hacky/reporting stuff in here

if (len(sys.argv) > 1):
    lot2_basepath = sys.argv[1]
else:
    print("Enter the full path to the save folder, such that the C01.ngd etc files exist there")
    lot2_basepath = input("Enter the save folder to scan: ").strip()
saveobj = Save(lot2_basepath)
#check_stones()

flan = saveobj.get_character('Flandre')
yuugi = saveobj.get_character('Yuugi')
kanako = saveobj.get_character('Kanako')

#Get specific characters
character_list = ['Meiling', yuugi, 'Kasen', 'Kanako', 'Reimu']
saveobj.party.SetCharacters(character_list)
for c in character_list:
    chara = saveobj.get_character(c)
    print(chara.name, saveobj.party.GetPosition(chara))
#exit()

for c in saveobj.party.GetCharacterList():
    print(c.name)
    all_skills = saveobj.party.GetCharacterSkills(c)
    print("Skill counters:")
    for x in all_skills.GetCounters():
        print(x)
    all_skills.SetCounter('LastFortress', 11)
    #So I guess I want to set the counters on the SkillCollection?
    #The individual skills would need to query that
    #Or I guess calling it on the coll could forward to every skill
    #That would solve the trr/psn/par issue. Kinda.
    #It would work for "I've inflicted trr, so I don't need to say they have an ailment"
    #The generic ailment skill could just also check trr and everything else.
    for l in c.list_spells():
        print(l)
    for i in c.formatted_spelldata:
        s = c.formatted_spelldata[i]
        print(f"{c.name}, {s.name}, {s.GetDamage(c, all_skills, None)}")
    #print(c.character_sheet())
    print()

#Yuugi, Knockout in Three Steps, 32698710
#Yuugi, Knockout in Three Steps, 42508323   [With Ruinous]
#Yuugi, Knockout in Three Steps, 42508323
#python main.py C:\Users\Qaz\AppData\Roaming\CUBETYPE\tohoLaby\save1.dat

#Kasen {'Name': 'Kasen', 'ATK': 5041096, 'DEF': 561000, 'MAG': 20344, 'MND': 614788, 'SPD': 17747}
#Kasen, Higekiri's Cursed Arm, 13724383
#Adversity should boost damage but not stats; no ailment should boost stats
#With healthy:
#Kasen, Higekiri's Cursed Arm, 15096820

print(yuugi.get_skill_level('Last Fortress'))
print(yuugi.get_skill_level('Physical Counter'))
print(yuugi.get_skill_level('Supernatural Phenomenon'))
print(yuugi.get_skill_level('etc'))
exit()




xp = 10000000
for c in saveobj.characters:
    c.level = 1
    c.exp = xp
    while (c.level_if_able()):
        pass
    #print(c.character_sheet())
for x in saveobj \
        .with_mod(lambda c: c.set_library_money('HP', 100000))\
        .order_by_stat('HP') \
        .characters:
    print(x.name,'-', x.get_stat('HP'), '   - HP:', x.libstats['HP'], 'Level:', x.level)

exit()

oldfloor = saveobj.misc_data.ic_floor
newfloor = round_up_ic(saveobj)
print(f"Floor: {oldfloor} -> {newfloor}")
if oldfloor != newfloor:
    adam = saveobj.items.get('Adamantite')
    ori = saveobj.items.get('Orichalcum')
    if adam['Count'] > ori['Count']:
        print(f"Orichalcum: {ori['Count']} -> {ori['Count']+1}")
        ori['Count'] += 1
    else:
        print(f"Adamantite: {adam['Count']} -> {adam['Count']+1}")
        adam['Count'] += 1
    saveobj.write_items()
    saveobj.misc_data.ic_floor = newfloor
    saveobj.write_misc()
exit()

#

#saveobj.misc_data.step_count = 5000

#flan.exp  = 1000000000
#saveobj.write_characters()

#q = saveobj.items.Query('Reincarnation')
#print(q)
#q.SetCount(90)
#saveobj.write_items()
#saveobj.write_misc()
#exit()

from lot2skill import skill_to_class_name
from lot2character import character_skills, character_spells
for x in character_skills:
    ch = character_skills[x]
    for i in ch:
        skl = ch[i]
        print(skill_to_class_name(skl['Name']))

exit()


#Utsuho, Wriggle : 120 BP.
#Cirno, Nitori, Chen: 200 BP.
#Meiling, Patchouli, Sakuya, Remilia: 300 BP.
#Minoriko, Komachi, Nazrin: 400 BP.



#q = saveobj.items.Query('Tome')
#q = saveobj.items.Query('Tome of Insight')
#q.Add("Veteran's Tome")
#q.Add("Spartan's Tome")
#for x in q.Contents():
#    print(f"{x['Name']}: {x['Count']}")
#q.SetCountIfBelow(56)
#for x in q.Contents():
#    print(f"{x['Name']}: {x['Count']}")

saveobj.items.get('Infinity Gem')['Count'] = 200
saveobj.write_items()
exit()
#gems_if_below(20)
#saveobj.write_characters()


#for c in saveobj.with_mod(lambda c: c.set_library_level('ATK', 1000)) \
#        .with_mod(lambda c: c.set_library_level('MAG', 1000)) \
#        .with_mod(lambda c: c.set_bonuses_to_offense())\
#        .characters:
#    for i in c.formatted_spelldata:
#        s = c.formatted_spelldata[i]
#        print(f"{c.name}, {s.name}, {s.GetDamage(c, None)}")
#

#for c in saveobj.characters:
#    print(c.character_sheet())

#for c in sorted(saveobj.characters, key=lambda x: x.get_total_money(), reverse=True):
#    print(c.name, ' - ', c.get_total_money())
#Check BP for all characters
#for x in saveobj.order_by_BP().characters:
#    print(x.name,'-', x.unused_skill_points)

add_xp = reimu_to_target(2400)
if add_xp > 0:
    for c in saveobj.characters:
        c.exp += add_xp
    saveobj.misc_data.money += int(add_xp // 4)
    print(f"Adding {add_xp} exp and {int(add_xp // 4)} money.")
    #
    result = saveobj.write_characters()
    saveobj.write_misc()
exit()

#for c in saveobj.get_characters(saveobj.party).characters:
#    print(c.character_sheet())

#print(saveobj.items.items)
#saveobj.items.get('Compact Arm')['Count'] = 3
#saveobj.items.get('Shuttle Body')['Count'] = 3

#TODO: Fix.
#saveobj.write_items()

#------
c = saveobj.get_character('Reimu')
print(c.character_sheet())

c.exp += 1
saveobj.misc_data.money += 1
#
result = saveobj.write_characters()
#print(result)
saveobj.write_misc()
#print("Wrote money:", saveobj.misc_data.money)
exit()

#==================================================
saveobj.reset()
exit()
#Some common things:
#Convert speed; to/from in-game display and actual ticks values.
spd = Speed(from_game_speed=1000)
print(f"1k spd is {spd.GetRealValue()}")
spd = Speed(from_real_speed=1000)
print(f"1k real spd is {spd.GetGameValue()}")

#Check BP for all characters
for x in saveobj.order_by_BP().characters:
    print(x.name,'-', x.BP)
    
#Show spellcards - and how much speed is needed to reach the next "speed threshold"
for x in saveobj.characters:
    for l in x.format_skill_list():
        print(l)
        
#Get specific characters
for x in saveobj.get_characters(['Suika', 'Yuugi', 'Kasen']):
    print(x.name)
    for l in x.format_skill_list():
        print(l)
    for i in c.formatted_spelldata:
        s = c.formatted_spelldata[i]
        print(f"{c.name}, {s.name}, {s.GetDamage(c, None)}")

#Get party
#for c in saveobj.get_characters(saveobj.party).characters:
#Get everyone
for c in saveobj.characters:
    print(c.character_sheet())
    skills = c.format_skill_list()
    for x in skills:
        print(x)


#Level everyone up to Reimu at 100.
#Don't do this for actual level ups; it should work, but it's safer to just assign xp.
#reimu = saveobj.get_character('Reimu')
#reimu.level = 100
#reimu.exp = 0
#xp = reimu.get_total_xp()

#for c in characters:
#    ch = saveobj.get_character(c)
#    #ch.level = 1
#    #ch.exp = xp
#    #while (ch.level_if_able()):
#    #    pass
#    print(ch.character_sheet())

#Maximum potential damage
for c in saveobj.characters:
    for i in c.formatted_spelldata:
        s = c.formatted_spelldata[i]
        print(f"{c.name}, {s.name}, {s.GetDamage(c, None)}")

#Highest ATK stat
for x in saveobj.order_by_offense(atkfactor=1).characters:
    print(x.name,'-', x.get_stat('ATK'))
#Highest combined (for dragon breath, or any composite subclass skill)
for x in saveobj.order_by_offense(magfactor=1, atkfactor=1).characters:
    print(x.name,'-', x.get_stat('MAG') + x.get_stat('ATK'))
#Highest combined, with 1k library levels, boost skills maxed out, gems maxed out, and all level up
#bonuses applied to the appropriate off stat.
print("Highest combined, with 1000 library levels in atk and mag:")
for x in saveobj \
        .with_mod(lambda c: c.set_library_level('ATK', 1000)) \
        .with_mod(lambda c: c.set_library_level('MAG', 1000)) \
        .with_mod(lambda c: c.set_bonuses_to_offense()) \
        .with_mod(lambda c: c.set_boosts_max(boost_level=2)) \
        .with_mod(lambda c: c.set_gems_max()) \
        .order_by_offense(atkfactor=1, magfactor=1) \
        .characters:
    print(x.name,'-', x.get_stat('MAG') + x.get_stat('ATK'))
#Undo any changes made to the characters
saveobj.reset()
print("Highest DEF:")
for x in saveobj.all() \
        .with_mod(lambda c: c.set_library_level('DEF', 1000)) \
        .with_mod(lambda c: c.set_bonuses_to_stat('DEF')) \
        .order_by_defense(deffactor=1) \
        .characters:
    print(x.name,'-', x.get_stat('DEF'))
#Check money library levels
patchy = saveobj.get_character('Patchouli')
print("Patchouli total MAG money:", patchy.get_total_money('MAG'))
print("Patchouli next MAG money:", patchy.get_money_to_next('MAG'))

print("Patchouli total FIR money:", patchy.get_total_money('FIR'))
print("Patchouli next FIR money:", patchy.get_money_to_next('FIR'))
