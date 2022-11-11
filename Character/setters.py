from lot2helper import *

import os
import copy
import math


###setters
@mods
def set_library_level(self, stat, value):
    """Changes the library bonus level for a stat to the given value."""
    #print('Called for', self.name,'with value', value)
    #TODO: Make a copy.
    if stat not in self.libstats:
        raise Exception("Unknown stat - " + stat)
    self.libstats[stat] = value
#
@mods
def set_all_library_level(self, value):
    """Changes the library bonus level for all stats to the given value."""
    for x in stats:
        self.set_library_level(x, value)
#
@mods
def set_bonuses_to_stat(self, stat):
    """Redistribute all level up bonuses to a single stat"""
    totalbonuses = self.unused_bonus_points
    self.unused_bonus_points = 0
    for x in self.levelstats:
        totalbonuses += self.levelstats[x]
        self.levelstats[x] = 0
    self.levelstats[stat] = totalbonuses
#
@mods
def set_bonuses_to_offense(self):
    """Redistribute all level up bonuses to either Mag or Atk, depending on the user's adjusted growth."""
    maggrowth = self.get_adjusted_growth('MAG')
    atkgrowth = self.get_adjusted_growth('ATK')
    if (maggrowth > atkgrowth):
        return self.set_bonuses_to_stat('MAG')
    else:
        return self.set_bonuses_to_stat('ATK')
#
#Gems
@mods
def set_gems(self, stat, value):
    """Change the character's gems for the given stat to the given value"""
    if stat not in gem_stats:
        raise Exception("Cannot assign gems for " + stat)
    if (value < 0 or value > 20):
        raise Exception("Number of gems must be between 0 and 20")
    self.gems[stat] = value
#
@mods
def set_gems_max(self):
    """Change the character's gems to 20 for every stat"""
    for x in gem_stats:
        self.set_gems(x, 20)
#
@mods
def set_gems_min(self):
    """Change the character's gems to 0 for every stat"""
    for x in gem_stats:
        self.set_gems(x, 0)
#
#Boost skills
#(There's no way I'm allowing setting other skills)
@mods
def set_boosts(self, stat, value, boost_level=1):
    """Change the character's boost type and skill level for the given stat to the given value"""
    if stat not in boost_stats:
        raise Exception("Cannot assign boost level for " + stat)
    if boost_level > 1 and stat not in boost_2_stats:
        #(EVA/ACC/AFF/RES)
        raise Exception("Stat " + stat + " only has 1 level of boost.")
    if (value < 0 or value > 5):
        raise Exception("Boost skill level must be between 0 and 5")
    if (boost_level < 1 or boost_level > 3):
        raise Exception("Boost level must be between 1 and 3 (2 and 3 are the same for Rinnosuke)")
    
    index = stat_index[stat]
    self.skills[index] = value
    
    if (self.id == 3 and boost_level == 2):
        #This code treats 2 and 3 as the same, but the save file uses 3.
        boost_level = 3
    
    if stat in boost_2_stats:
        #Now set boost level
        self.boosts[stat] = boost_level
    #
#
@mods
def set_boosts_max(self, boost_level=3):
    """Change the character's boost to max for every stat"""
    for x in gem_stats:
        self.set_boosts(x, 5, boost_level)
#
@mods
def set_boosts_min(self):
    """Change the character's boost to min for every stat"""
    for x in gem_stats:
        self.set_boosts(x, 0)
#
@mods
def clear_equipment(self):
    """Change the character's boost to min for every stat"""
    #This should also increment the total available for this item by 1 (since it's removed),
    #but I don't have that parsed.
    for x in range(4):
        self.items[x] = 0
#
@mods
def set_subclass(self, newclass):
    """Change the character's subclass. Also learn all subclass skills, since some modify stats"""
    #TODO: Really need to make a spreadsheet of subclass skills...
#