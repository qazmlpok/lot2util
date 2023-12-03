import os
import copy
import math
from lot2formation import FakeFormation
from lot2skill import *

#Spell data is taken from the Thurler's spreadsheet; 
#https://docs.google.com/spreadsheets/d/1chsDfMOkUf5G4V2fBiEk3WX06mGA3COM8aRbRheh56M/edit#gid=2064051559

#Youkai Yakuza Kick:
#atk and mult are: 150/170/210/230
#That's no reading, reading, no reading awakened, reading awakened.
#The Count of Monte Cristo and Musketeer d'Artagnan only have no reading/reading: 120/140 * 120/150
#Shield Bash: CDef is 0/10/20/30/40, depending on skill level
#Iron Mountain Charge: TDef is 25/22/19/16/13, depending on skill level

class SpellData():
    """ Data class for an attack.
    An attack has a name (not guaranteed to be unique), a damage formula, one or multiple elements,
    a post-use ATB (i.e. "Delay").
    Other things like MP/Skp cost are not included.
    Special effects are not handled in any way, e.g. ailments.
    To actually get damage numbers, the spell has to be used by a character, and then against an enemy
    The enemy may be None to get theoretical max damage (i.e. def is treated as 0)
    """
    copy_fields = ['Name', 'Target', 'ATK', 'MAG', 'DEF', 'MND', 'T.DEF', 'T.MND', 'Multiplier', 'Accuracy', 'Delay']
    def __init__(self, row):
        """Create a new data object from a spreadsheet row.
        """
        self.element = set(row['Element'].split('-'))
        self.name = row['Name']
        #There's probably a better way to do this, but, eh.
        #I'm doing this replace in case I switch to using setattr instead. I don't know if it matters.
        self.row_data = {n.replace('.', ''): row[n] for n in SpellData.copy_fields}
        #print(self.row_data)

    def GetDamage(self, user, all_skills = None, target = None):
        """ Calculate the damage for the associated spell, as cast by the current user.
        User can theoretically be any character - Satori in particular, but also the generic attack skill.
        Formation data is needed to use skills belonging to anyone other than the user.
        """
        #I really should not use that as the name.
        #Fix by making a subclass as a psuedo-character.
        c = user
        if target is None:
            target = {}
        #This needs to be reproduced somewhere.
        #if formation is None:
        #    formation = FakeFormation(user)
        #position = formation.GetPosition(user)
        #if position is None:
        #    formation = FakeFormation(user)
        #    #Again, user must be in the formation. 
        
        #Make a copy of the spell formula - some skills will change it. Don't edit the original object.
        spell_copy = copy.copy(self.row_data)
        #Replace the string-with-hyphens with an array.
        spell_copy['Element'] = self.element
        #...This can actually be modified. Oh boy.
        #That would need to be a priority, since other skills will take effect. Sigh.

        print(user.name, all_skills)
        c = {
            'Name' : user.name,
            'ATK' : user.get_stat('ATK'),
            'DEF' : user.get_stat('DEF'),
            'MAG' : user.get_stat('MAG'),
            'MND' : user.get_stat('MND'),
            'SPD' : user.get_stat('SPD'),
        }
        
        print('BEFORE', c);
        
        #Apply skills. All skills is filtered to those that are "active", but not all skills will do anything
        #Counter-based skills are _not_ yet filtered.
        for sk in all_skills.skills.values():
            #print(sk)
            if sk.CounterActive() and sk.IsApplicable(spell_copy, target):
                #Any of the user, spell, or target may be modified by this.
                #Typically only just one. I don't think anything would hit two.
                sk.PreApply(spell_copy)
        for sk in all_skills.skills.values():
            #print(sk)
            if sk.CounterActive() and sk.IsApplicable(spell_copy, target):
                #Any of the user, spell, or target may be modified by this.
                #Typically only just one. I don't think anything would hit two.
                sk.Apply(c, spell_copy, target, True)
                print("APPLY:", sk)
        
        #If there are skills that affect target's stats (Alice has one), apply as well. Need a copy of target.
        #Or, rather, need to get the actual values for target.
        
        print('AFTER', c);
        
        #Apply items? Super Drill will do target def *= 0.75.
        #Scouter will, if targetting a weakness, multiply damage by 1.10
        #Quartz Crystal is flat 20%; there's some element boosting items.
        
        (catk, cmag, cdef, cmnd, tdef, tmnd) = (spell_copy['ATK'],spell_copy['MAG'],spell_copy['DEF'],spell_copy['MND'],spell_copy['TDEF'],spell_copy['TMND'])
        mult = spell_copy['Multiplier']
        
        #Using the character data and spell, calculate the base damage
        dmg = (
                  (c['ATK'] * catk / 100) +
                  (c['MAG'] * cmag / 100) +
                  (c['DEF'] * cdef / 100) +
                  (c['MND'] * cmnd / 100)
              )
        
        #Subtract defensive stats, if target has them.
        #Skills may alter defense...
        if hasattr(target, 'get_stat'):
            deffactor = (
                        (target.get_stat('DEF') * tdef / 100) + 
                        (target.get_stat('MND') * tmnd / 100)
                   )
            if deffactor > dmg:
                #I thiiiiink this will reproduce the weirdness of hitting for 1-2 damage instead of 0 on super high def enemies.
                #It should always prevent dmg from going negative (which is the important bit)
                deffactor = int(dmg)
            dmg -= deffactor
        
        dmg = dmg * mult / 100
        
        #Apply affinity.
        dmg = dmg * self._getAffinity(target) / 100
        
        #Idea: Store everything except the final damage number in an object.
        #Just pass in the raw data - character/target stats, affinities/elements, etc
        #Define every skill as a lambda function that will operate on this object,
        #and modify either the raw values (atk + 10% in x situation)
        #or the Multiplier (10% bonus damage for row skills)
        #Or the formula itself (Komachi's stuff)
        #Or the affinity (Sheer Force)
        #Then when all the skills are done, use the updated obj to get the final damage.
        
        return int(dmg)
        
    def _getAffinity(self, target):
        elements = self.element
        if elements is None or len(elements) == 0 or not hasattr(target, 'get_stat'):
            return 100
        #Loop over all elements (always an array). Check target for affinity
            #Just check for missing here - it'll be easier to do lowest as a specific call to Min or something
            #But that'd break if stuff was missing.
        #Return the lowest.
        #I guess this should use get_stat too; enemies will need a dummy version.
        #If any aren't found, return 100.
        
        #Apply skills to the final result: Sheer Force.
        #I don't believe any items can affect affinities.
        
        return 100
#