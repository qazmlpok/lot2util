import copy
import re
from lot2helper import *
#This is generic enough that it would probably work fine for lot1. Or 3.
#-All except for character_lookup, from lot2helper. Oh well.

class CharacterList:
    def __init__(self, characters):
        #Master copy - original, without any modifications to content, or filtering/sorting.
        self.original_characters = copy.deepcopy(characters)
        #Full copy - contents can be modified, but the list itself should always be all characters.
        self.all_characters = copy.copy(characters)
        #Modifiable collection. Can be filtered.
        self.characters = characters
    def reset(self):
        """Undoes all changes. Reverts back to the original data read in from the save files"""
        self.all_characters = copy.deepcopy(self.original_characters)
        self.characters = self.all_characters
    #
    def get_character(self, name):
        id = 0
        m = re.match(r'\d+', str(name))
        if m:
            id = int(name)
        else:
            name = name.capitalize()
            
            #Nicknames...
            if name == 'Rin' or name == 'Orin' or name == 'Orinrin':
                id = 23
            elif name == 'Okuu':
                id = 24
            else:
                if name in character_lookup:
                    id = character_lookup[name]
                else:
                #This should then scan character full_name for a match, but I haven't grabbed that yet...
                    pass
        #
        if id == 0:
            #raise Exception("Couldn't match " + str(name) + " to a character's name.")
            return None
        return self.all_characters[id-1]
    #
    def get_characters(self, names):
        #This should be *args
        self.characters = [self.get_character(name) for name in names if self.get_character(name) is not None]
        return self
    #
    #Filtering
    def all(self):
        for c in self.all_characters:
            if c not in self.characters:
                self.characters.append(c)
        return self
    #
    def top(self, number):
        self.characters = self.characters[0:number]
        return self
    #
    #Sorting
    #TODO: Change the order functions to work in-place.
    #Then add a top(x) / bottom(x) function.
    def order_by_BP(self):
        """Returns a list of all characters sorted by BP"""
        #Mostly just a test to make sure sorting works.
        self.characters.sort(key=lambda c: c.BP, reverse=True)
        return self
    #
    def order_by_offense(self, atkfactor=0, magfactor=0):
        #I thought Holy Blessing's subskills were composite too. Oops.
        #If it isn't composite there's little point, since it's just ordering by stat directly.
        #--and every subclass composite spell has equal weight, so there's doubly no point in this.
        #Dragon God's Sigh: 156.25%(ATK+MAG)
        #Ame-no-Murakumo Slash: 241% ATK
        #Start of Heavenly Demise: 353% MAG
        if atkfactor == 0 and magfactor == 0:
            raise Exception("Atk and Mag factors cannot both be 0.")
        func = lambda c: c.get_stat('ATK') * atkfactor + c.get_stat('MAG') * magfactor
        self.characters.sort(key=func, reverse=True)
        return self
    #
    def order_by_defense(self, deffactor=0, mndfactor=0):
        if deffactor == 0 and mndfactor == 0:
            raise Exception("Def and Mnd factors cannot both be 0.")
        func = lambda c: c.get_stat('DEF') * deffactor + c.get_stat('MND') * mndfactor
        self.characters.sort(key=func, reverse=True)
        return self
    #
    def order_by_stat(self, stat):
        func = lambda c: c.get_stat(stat) 
        self.characters.sort(key=func, reverse=True)
        return self
    #
    ###
    def with_mod(self, func):
        #Calls the provided function on all characters.
        #Should be a lambda
        for x in self.all_characters:
            func(x)
        
        return self
    #

#This is based on PPC01.ngd. It's just 12 bytes saying what each party slot is:
# 9ABC   (Backrow)
# 5678   (Backrow)
# 1234   (Frontline)
# L  R

class Formation:
    #To iterate over the formation data in order.
    order = list(range(8, 12)) + list(range(4, 8)) + list(range(0, 4))
    def __init__(self, ids, character_list):
        #I don't think I need to save the full list.
        self.characters = [character_list.get_character(x) for x in ids]
        self.allow_duplicates = False
    def GetCharacterList(self):
        """ Returns the current characters. Effectively `self.characters`,
        except it trims out None
        """
        s = set(self.characters)
        s.remove(None)
        #or list s, but does it really matter?
        return s
    def GetPosition(self, c):
        """ Determines where character c is within the current formation
        Returns None if the character isn't in the current formation
        If you have duplicates, returns the first position.
        """
        for index in range(12):
            i = Formation.order[index]
            if self.characters[i] == c:
                return index
        return None
#
