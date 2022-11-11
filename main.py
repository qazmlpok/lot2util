#!/usr/bin/env python
# -*- coding: utf-8 -*-

# E:\qazmlpok\Touhou Project\Labyrinth of Touhou2_PlusDisk\save\save1




from lot2character import Character
from lot2save import Save
from lot2speed import Speed

import os

#Main program. Keep any hacky/reporting stuff in here

print("Enter the full path to the save folder, such that the C01.ngd etc files exist there")
lot2_basepath = input("Enter the save folder to scan: ")


saveobj = Save(lot2_basepath)

#for x in saveobj.order_by_BP().characters:
#    print(x.name,'-', x.BP)
#print ("First:", saveobj.characters[0].name)
#print()

#------

remi = saveobj.get_character('Remilia')
byak = saveobj.get_character('Byakuren')

print(remi.character_sheet())
print(remi.full_name, '-', remi.get_stat('SPD'), 'speed')
print("\n".join(remi.list_spells()))
print("-------------------------")
print(byak.character_sheet())
print(byak.full_name, '-', byak.get_stat('SPD'), 'speed')
print("\n".join(byak.list_spells()))


tiger =  saveobj.get_character('Shou')

tiger.level = 50000
tiger.set_boosts('DEF', 5, 3)
tiger.set_boosts('MND', 5, 3)
tiger.levelstats['DEF'] = tiger.level/2
tiger.levelstats['MND'] = tiger.level/2
tiger.set_library_level('DEF', tiger.level * 1)
tiger.set_library_level('MND', tiger.level * 1)
#print(tiger.get_stat('DEF'))

#print(tiger.character_sheet())

kags =  saveobj.get_character('Kaguya')

kags.level = 900
kags.set_boosts('MAG', 5, 3)
kags.levelstats['MAG'] = kags.level
kags.set_library_level('MAG', kags.level * 1)
print(kags.get_stat('MAG'))

print(kags.character_sheet())

exit()
#------

#------

eirin = saveobj.get_character('Eirin')
patchy = saveobj.get_character('Patchouli')

print(eirin.character_sheet())

print("Eirin total exp:", eirin.get_total_xp())
print("Eirin next exp:", eirin.get_xp_to_next())



print(patchy.character_sheet())

print("Patchouli total MAG money:", patchy.get_total_money('MAG'))
print("Patchouli next MAG money:", patchy.get_money_to_next('MAG'))

print("Patchouli total FIR money:", patchy.get_total_money('FIR'))
print("Patchouli next FIR money:", patchy.get_money_to_next('FIR'))

spd = Speed(from_game_speed=1000)
print(f"1k spd is {spd.GetRealValue()}")



exit()
#------

for x in saveobj.characters:
    x.level = 1
    x.exp = x.get_xp_to_level(10000 + x.id)
result = saveobj.write_characters()
print("\n".join(result))
exit()

print("Highest atk:")
for x in saveobj.order_by_offense(atkfactor=1).characters:
    print(x.name,'-', x.get_stat('ATK'))
print()
#print("Highest mag:")
#for x in saveobj.order_by_offense(magfactor=1).characters:
#    print(x.name,'-', x.get_stat('MAG'))
#print()
#print("Highest combined for dragon breath:")
#for x in saveobj.order_by_offense(magfactor=1, atkfactor=1).characters:
#    print(x.name,'-', x.get_stat('MAG') + x.get_stat('ATK'))

#Find the highest atk if everyone has 1000 library levels in atk
print()
print()
print()
print("Highest combined, with 1000 library levels in atk and mag for dragon breath:")
for x in saveobj \
        .with_mod(lambda c: c.set_library_level('ATK', 1000)) \
        .with_mod(lambda c: c.set_library_level('MAG', 1000)) \
        .with_mod(lambda c: c.set_bonuses_to_offense()) \
        .with_mod(lambda c: c.set_boosts_max(boost_level=2)) \
        .with_mod(lambda c: c.set_gems_max()) \
        .order_by_offense(atkfactor=1, magfactor=1) \
        .characters:
    print(x.name,'-', x.get_stat('MAG') + x.get_stat('ATK'))

#Need to add reset feature...
print()
print()
print("Highest atk:")
for x in saveobj.order_by_offense(atkfactor=1).characters:
    print(x.name,'-', x.get_stat('ATK'))

#print(saveobj.party)
#for c in saveobj.get_characters(saveobj.party).characters:
#    print(c.character_sheet())



def reimu_to_target(target):
    reimu = saveobj.get_character('Reimu')
    needed = reimu.get_xp_to_level(target)
    needed -= reimu.exp
    if (needed <= 0):
        return 0
    #The formula isn't perfectly accurate. Fudge a bit; hopefully will counter the issue.
    needed = int(needed * 1.005)
    return needed
#
def gems_if_below(target):
    for c in saveobj.all_characters:
        for x in lot2util.gem_stats:
            if c.gems[x] < target:
                print("Giving", c.name, target, "gems for",x, ", from", c.gems[x])
                c.gems[x] = target
#
saveobj.reset()


# #this prints
#  gems_if_below(20)
#  
#  saveobj.all() \
#      .with_mod(lambda c: c.set_all_library_level(1500))
#  result = saveobj.write_characters()
#  print("\n".join(result))


#-----------------------

for c in saveobj.get_characters(saveobj.party).characters:
    print()
    print('=' * 79)
    print(c.full_name, '-', c.get_stat('SPD'), 'speed')
    print("\n".join(c.list_spells()))
#

#for c in saveobj.all_characters:
for c in saveobj.characters:
    print(c.character_sheet())
#    input("Press enter to continue (ctrl-c to exit)")
#


# 
# needed_xp = reimu_to_target(1000)
# print(needed_xp, "exp needed for Reimu to be avg 1000")
# 
# for x in saveobj.all_characters:
#     x.exp += needed_xp
# result = saveobj.write_characters()
# print("\n".join(result))

#print()
#print()
#print("Highest DEF:")
#for x in saveobj.all() \
#        .with_mod(lambda c: c.set_library_level('DEF', 1000)) \
#        .with_mod(lambda c: c.set_bonuses_to_stat('DEF')) \
#        .order_by_defense(deffactor=1) \
#        .characters:
#    print(x.name,'-', x.get_stat('DEF'))
#
#saveobj.top(5)
#for c in saveobj.characters:
#    print(c.character_sheet())
#

# #Real: 1530737621       self.exp is 824006
# #Returns: 1529621466
# print("Reimu's total exp is ", saveobj.get_character('Reimu').get_total_xp())
# 
# #Returns: 5394175    Real: 5417227
# print("Reimu's exp to next is ", saveobj.get_character('Reimu').get_xp_to_next())
# 
# print()
# #Returns: 1528892236        #Real: 1523570388
# print("Kogasa's total exp is ", saveobj.get_character('Kogasa').get_total_xp())
# 
# #Returns: 5322020    Real: 5322020
# print("Kogasa's exp to next is ", saveobj.get_character('Kogasa').get_xp_to_next())
# 
#


#for c in saveobj.get_characters(saveobj.party):
    #print(c.character_sheet())


#save

#print("Kogasa to next:", saveobj.get_character('Kogasa').get_xp_to_next())

saveobj.reset()
print("Reimu's level is ", saveobj.get_character('Reimu').level)

#needed_xp = reimu_to_target(1500)
#print(needed_xp, "exp needed for Reimu to be avg 1500")
#
#for x in saveobj.all_characters:
#    x.exp += needed_xp
#result = saveobj.write_characters()
#print("\n".join(result))


#Tested - works as expected.
#saveobj.all().with_mod(lambda c: c.set_free_bonuses_to_most_used())
#
#for c in saveobj.get_characters(saveobj.party).characters:
#    print(c.character_sheet())
#
#result = saveobj.all().write_characters()
#print("\n".join(result))

exit()

id = 1  #Reimu
id = 6  #Youmu (has max number of skills)
id = 4  #Keine
id = 8  #Rumia

lot2_basepath = r'E:\qazmlpok\Touhou Project\Labyrinth of Touhou2_PlusDisk\save\save1'

save_1_path = lot2_basepath

ngdfile = os.path.join(save_1_path, 'C%02d.ngd' % id)

with open(ngdfile, 'rb') as f:
    parsed = Character(id, f)
name = parsed.name

print(name, "is level", parsed.level, "with",  parsed.unused_bonus_points, "unused bonus points. BP is", parsed.BP)
print(name, "is subclass", parsed.subclass, "and has", parsed.unused_skill_points, "unused skill points",)
print(name + "'s magic stat is", parsed.get_stat('MAG'), 'from an adjusted growth of', parsed.get_adjusted_growth('MAG'))        #108 growth, 56172 stat. No items.
print(name + "'s speed stat is", parsed.get_stat('SPD'), 'from an adjusted growth of', parsed.get_adjusted_growth('SPD'))        #108 growth, 56172 stat. No items.
print(name + "'s MP is", parsed.get_stat('MP'))        #108 growth, 56172 stat. No items.

print(parsed.character_sheet())

skill_listing = parsed.list_skills()
print(name + "'s skills are:")
for x in skill_listing:
    print(x)

