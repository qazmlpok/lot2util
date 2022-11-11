from lot2helper import *

import os
import copy
import math

def get_equipment_stat(self, stat):
    """Gets the combined bonus (multiplier or flat boost; it depends on the stat)
    of all equipped items.
    Includes the Maintenance bonus."""
    bonus = 0
    for i in self.items:
        i = int(i)
        if i == 0:
            continue
        if i not in item_stats:
            raise Exception("Strange equipped item with id " + i)
        item = item_stats[i]
        bonus += float(item[stat])
     
    #Check maintenance. These all have different ids, and Miko's version has a different name as well.
    #Nitori
    if self.id == 13 and self.skills[20] > 0:
        bonus *= 2
    #Renko
    if self.id == 47 and self.skills[23] > 0:
        bonus *= 2
    #Miko
    if self.id == 52 and self.skills[23] > 0:
        bonus *= 2
    
    return bonus
#
def get_equipment_specials(self):
    """Returns all 'special' attributes of current equipment. This is things like a quartz charm's
    flat damage boost. There's no automatic parsing.
    Filters out empty results. [] means no items equipped with special attributes."""
    results = []
    for i in self.items:
        i = int(i)
        if i == 0:
            continue
        if i not in item_stats:
            raise Exception("Strange equipped item with id " + i)
        item = item_stats[i]
        if 'Special' in item and item['Special'].strip() != '':
            results.append(item['Special'])
    return results
#
def _get_boost(self, stat):
    """Private function to handle the annoying mess that is determining 
    if boost 1/2/3 skills are available, if your character is a guy,
    and therefore how much they boost and given stat"""
    boost_level = 1
    #Everyone has a default boost skill; it doesn't really matter if the skill is unlocked or naturally known
    #Assume there's no trickery where a locked skill has points in it.
    
    #No levels, just the basic boost. Except Rinnosuke, of course
    if stat in ('EVA', 'ACC', 'AFF', 'RES'):
        if stat == 'EVA':
            if (self.id == 3):
                return 20
            else:
                return 6
        else:
            raise Exception("other stats unimplemented.")
    
    #Check if boost2/3 unlocked. boost value of 0 and 1 are the same; boost_level=1
    if (self.boosts[stat] > 1):
        boost_level = self.boosts[stat]
    if (self.id == 3):
        #Rinnosuke.
        #He only has two levels: "High" and "Giga".
        if boost_level == 3: boost_level = 2        #Simplifies the returns.
        if (stat == 'HP'):
            return (0, 12, 16)[boost_level]
        if (stat == 'MP'):
            return (0, 2, 5)[boost_level]
        if (stat == 'TP'):
            return (0, 4, 6)[boost_level]
        elif (stat in ('ATK', 'MAG')):
            return (0, 10, 15)[boost_level]
        elif (stat in ('DEF', 'MND')):
            return (0, 8, 11)[boost_level]
        elif (stat == 'SPD'):
            return (0, 6.0, 9.0)[boost_level]
    else:
        #Three levels: Boost, Boost 2, Mega Boost
        if (stat == 'HP'):
            return 4 * boost_level
        if (stat == 'MP'):
            return 1 * boost_level      #It's just 1/2/3 added (not actually growth)
        if (stat == 'TP'):
            return (0, 2, 4, 4)[boost_level]        #again, flat bonus
        elif (stat in ('ATK', 'MAG')):
            return 2 * boost_level
        elif (stat in ('DEF', 'MND')):
            return 2 * boost_level
        elif (stat == 'SPD'):
            return (0, 1.4, 2.2, 3.0)[boost_level]
    #
    raise Exception("other stats unimplemented.")

#https://en.touhouwiki.net/wiki/Labyrinth_of_Touhou_2/Gameplay#Base_Stats_and_Stat_Formulas
#Growth here is in 10ths internally, wiki uses decimals instead.
#Note - this function returns a float, because some growth modifiers use fractionals,
#even of the already-fractional growths (speed, Rumia's awk skill, maybe others)
def get_adjusted_growth(self, stat):
    """Take the character's standard growth, add in boosts from skills, gems, subclass"""
    index = stat_index[stat]
    growth = self.basestats[stat]

    #Mostly useless, but whatever.
    if (stat == 'MP'):
        return ("1/%d" % (growth['MP growth denominator']), growth['MP growth denominator'])

    #Boost
    boostMult = self._get_boost(stat)
    boostSkill = self.skills[index]
    boostAdd = boostMult * boostSkill
    
    #gems. Each is worth +2. The jewels are only worth +1
    gemcount = self.gems[stat]
    if gemcount <= 10:
        growth += gemcount * 2
    else:
        growth += 20 + (gemcount-10)
    
    #Should be this floor'd here?
    growth += boostAdd
    
    #Skills
        #Which skills even boost stats?
        #Keine's Were-Hakutaku Form  [all]
        #Rumia's Darkness-Lurking Youkai [mag, eva]
        #Cirno's Acrobatic Tomboyish Fairy 	 [spd, eva]
        #Chen's Indiscernible Monster Cat [eva, atk, spd]
        #Aya's Crow Tengu's Watchful Eyes  [eva]
        #Alice's Doll Guard [eva], Additional Doll Guards 
        #Patchy's Asthma Medicine [hp]
        #Eirin's Special Endurance Medicine  [aff, res]     #FIX
        #Iku's Pearl of the 5-Clawed Dragon 
        #Ran's Fried Tofu Power-Up [all]
        #Suwako's Chytridiomycosis Resistance [res, hp]
        #Tenshi's ___ [hp]
        #Yuyuko's Saigyou Ayakashi Seal [hp]
        #Byakuren has some, but for ailments, and they're irksome
    #
    for i in range(20, 30):
        #Skip boost skills and spellcards.
        level = self.skills[i]
        if level == 0:
            #Skip unlearned skills, skip any placeholder skills (which would cause a key error)
            continue
        #Will be 0 for most entries.
        growth += (self.skilldata[i][stat] * level)

        #debug
        #if self.skilldata[i][stat] > 0:
        #    print("Skill %s raises growth by %f" % (self.skilldata[i]['Name'], self.skilldata[i][stat]))
        #
        
    #Items. These list everything in tenths; "Egg" says 0.5, but raises in-game display by 5.
    growth += int(self.get_equipment_stat(stat + ' Base Value') * 10)
        
    #Subclass
    #Mastery skill
    growth += subclass_bonuses[self.subclass_id][stat]

    #Check for other subclass skills:
    #I think just transcendant's skill?
    #WINNER's Auto Roller 
    #Archmage and Swordmaster
    #These might be easier to just hardcode.
    for i in range(1, 20):
        level = self.subskills[i]
        if level == 0:
            continue
        subbonus = hardcoded_subskill_boosts(self.subclass_id, i, stat)
        growth += (subbonus * level)
        #Does this need to be floor'd?
        #if subbonus != 0:
        #    print("Subclass skill %d boosted by %f" % (i, subbonus))
        #
    
    #SubSkills
    
    #int here to floor the value? Or leave that up to the caller?
    return growth
#
def get_MP(self, stat='MP'):
    #Included just to keep the prototypes similar.
    #Only thing missing is skills.
    stat='MP'
    index = stat_index[stat]
    
    basegrowths = self.basestats
    
    value = int(basegrowths[stat])
    
    #MP gain from levels (appears to) cap out at double the character's base stat
    fromlevels = int(self.level / basegrowths['MP growth denominator'])
    if (fromlevels > value):
        fromlevels = value
    value += fromlevels

    #Boost
    boostMult = self._get_boost(stat)
    boostSkill = self.skills[index]
    boostAdd = boostMult * boostSkill

    value += boostAdd
    #Gems
    #I'm pretty sure these are just +1 MP
    value += self.gems['MP']
    
    #skills
    
    #Subclass
    #value += hardcoded_subskill_boosts(self.subclass, (loop over all skills), 'MP')
    
    #Mastery skill
    value += subclass_bonuses[self.subclass_id][stat]
    
    #I think that's it.
    
    return value
#
def get_aux_stat(self, stat):
    basegrowths = self.basestats[stat]
    index = stat_index[stat]
    
    #Boosts (level 1 only - treat as a skill)
    
    #Skills
    
    #TP has gems.
    
    #Subclass. Mastery only I think.
    
    if stat == 'EVA':
        value = int(basegrowths)
        
        #Boost
        boostMult = self._get_boost(stat)
        boostSkill = self.skills[index]
        boostAdd = boostMult * boostSkill

        value += boostAdd
        
        for i in range(20, 30):
            #Skip boost skills and spellcards.
            level = self.skills[i]
            if level == 0:
                #Skip unlearned skills, skip any placeholder skills (which would cause a key error)
                continue
            #Will be 0 for most entries.
            value += (self.skilldata[i][stat] * level)

            #debug
            #if self.skilldata[i][stat] > 0:
            #    print("Skill %s raises EVA by %f" % (self.skilldata[i]['Name'], self.skilldata[i][stat]))
            #
            
        
        #Subclass skills
        subbonus = hardcoded_subskill_boosts(self.subclass_id, i, stat)
        value += (subbonus * level)
        
        #Mastery skill
        value += subclass_bonuses[self.subclass_id][stat]
        
        return value
    
    #ok this should probably just be eva/acc and res/aff should be their own function...
    raise Exception("Not implemented.")
#
def get_stat(self, stat):
    """Get the actual value of a stat. Ignores items"""
    #(It technically shouldn't ignore items due to maintenance, but items are otherwise the same for everyone.)
    #Oh, and the +stat growth main equips. Those would vary based on level. Oh well.
    stat = stat.upper()
    
    #Sufficiently different that they don't belong in here.
    if (stat == 'MP'):
        return self.get_MP()
    if (stat in ('ACC', 'EVA', 'TP') or stat in affinities or stat in resistances):
        return self.get_aux_stat(stat)
        #This should be a different function for res/aff...
        #TP, ACC, and EVA have no growth; they're only based on base stat and skills.
    if (stat in ('RES', 'AFF')):
        raise Exception("Can't get stats for resistances or affinities in general. Use a specific affinity or resistance.")
    
    #Multiplier = 1 + Equipment Bonuses + (Level Up Bonuses * 0.03) + (Stat Level * 0.02)
    multiplier = 100
    
    #Library
    multiplier += self.libstats[stat] * 2
    
    #Level-up bonuses
    multiplier += self.levelstats[stat] * 3
    
    #Equipment is a pain in the ass.
    multiplier += self.get_equipment_stat(stat)
    
    #There shouldn't be any other sources of a multiplier.
    growth = int(self.get_adjusted_growth(stat))
    level = self.level
    
    #If there are slight inaccuracies in the results, re-work this to remove floating point math
    #Although it's perfectly possible the in-game implementation has floating point errors.
    growth = growth / 10.0
    
    #HP = (Level + 6) * Growth Rate + 10
    #ATK/ MAG/ DEF/ MND = (Level + 4) * Growth Rate + 4
    #SPD = (Level + 10) * (Growth Rate / 32)
    
    if (stat == 'HP'):
        value = (level + 6) * growth + 10
    elif stat in ('ATK', 'DEF', 'MAG', 'MND'):
        value = (level + 4) * growth + 4
    elif (stat == 'SPD'):
        value = (level + 10) * (growth / 32.0)
    else:
        raise Exception("Stat not implemented.")
    

    
    #The final values of each stat are calculated as follows:
    #HP/ ATK/ MAG/ DEF/ MND = floor(floor(Base Value) * Multiplier)
    #SPD = floor(floor(Base Value) * Multiplier) + 100

    if stat in ('HP', 'ATK', 'DEF', 'MAG', 'MND'):
        value = int((int(value) * multiplier) / 100.0)
    elif (stat == 'SPD'):
        value = int((int(value) * multiplier) / 100.0) + 100
    
    return value
#
def get_xp_to_next(self, level=None):
    #This xp formula is an appoximation, taken from the jp wiki.
    #It's not perfect but it seems to work well enough.
    #At level 761, Kogasa, in-game required exp is 4188866, this formula returns 4189322  (diff: 456)
    #LvDiff * (0.144ｘ^2 + 0.516ｘ + 0.34)
    #762 to next:   real:4199857   this func: 4200313   (diff:456)
    #My own calculations yield: a = 0.144  b = 0.504  c = 0.36
    if level == None:
        #can't use self.level as a default value (unless python3 changes that)
        level = self.level
    lvsq = level * level
    levelrate = int(self.basestats['Leveling rate'])
    #return int(levelrate * (0.144 * (lvsq) + 0.516 * level + 0.34))
    return int(levelrate * (0.144 * (lvsq) + 0.504 * level + 0.36))
#
def get_xp_to_level(self, target):
    level = self.level
    total = 0
    while (level < target):
        total += self.get_xp_to_next(level)
        level += 1
    return total
#
def get_total_xp(self):
    level = self.level
    total = self.exp
    while (level > 1):
        total += self.get_xp_to_next(level)
        level -= 1
    return total
#
