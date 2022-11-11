from lot2helper import *
from lot2character import Character

import os
import copy
import math

class Save:
    """Represents a save folder in <lot2_root>/Save."""
    #Data from the wiki:
    #C*.ngd: character files (see characters lookup dictionary)
    #D*.txt: Dungeon exploration
    #       See data\ for the actual dungeon data. 
    #EEF01 Contains the flags for found items. 
    #EEN01 has the amount of items in the inventory 
    #       Training manuals are at 0x650    This is two bytes, but there seems to be a max and anything over that is treated as 0. 99, maybe?
    #       Infinity gems at 0x06BC
    #EVF01 has event flags (?)
    #FOE01 has FOE respawn timers.
    #PAC01 contains the flags for achievements that you have obtained but not checked yet.
    #PAM01 has achievement flags.
    #PCF01 has character recruitment flags
    #PPC01 has the current party.
    #PKO01 has the entries for Keine's school?
    #PEX01 has miscellaneous game data. 
    #SHD01 has save game data (changing most of these only affects the value shown in the save, the actual values remain unchanged). 
    
    #The only things of interest are the character data, items, and misc (PEX01 - includes money, IC floor)
    #PPC01 might be useful, but not editable.
    
    def __init__(self, basepath):
        """Creates the Save wrapped object. The path needs to be one of the SaveX folders, i.e. all the *.ngd files must exist here"""
        self._folder = basepath
        self.all_characters = [None] * (len(character_ids))
        for i in character_ids:
            ngdfile = os.path.join(self._folder, 'C%02d.ngd' % i)

            with open(ngdfile, 'rb') as f:
                self.all_characters[i-1] = Character(i, f)
            
            #Add to dict
            #self.characters[self.all_characters[i-1].name] = self.all_characters[i-1]
            #TODO: Extend this to support short name and full name.
            #Actually, and a function so I can use case-insensitive.\
        #
        self.original_characters = copy.deepcopy(self.all_characters)
        self.characters = copy.copy(self.all_characters)
        
        partyfile = os.path.join(self._folder, 'PPC01.ngd')
        with open(partyfile, 'rb') as f:
            self.party = self.load_current_party(f)
        #Should also do items, money.
        
        
        
        #Note on characters
        #There are three lists: original_characters, all_characters, characters
        #original_characters should never be modified and is a deep copy. It allows resetting without re-reading the files.
        #all_characters is every character. The contents can be modified but the list itself shouldn't.
        #characters is initially a copy of all_characters, but is intended to be modified. The sort functions will change the order and filtering can be done.
        
    #
    def write_characters(self):
        #TODO: Add an optional parameter for a filter (using get_characters semantics)
        #Largely unnecessary since it uses characters, but it'd still be nice.
        
        ret = []
        for c in self.characters:
            ngdfile = os.path.join(self._folder, 'C%02d.ngd' % c.id)
            #Make sure it already exists
            if (not os.path.exists(ngdfile)):
                raise Exception("Path doesn't already exist: " + ngdfile)
            with open(ngdfile, 'r+b') as fh:
                c.save_to_file(fh)
            ret.append("Wrote save data for " + c.name + " to path: " + ngdfile)
        return ret
    #
    def reset(self):
        """Undoes all changes. Reverts back to the original data read in from the save files"""
        self.all_characters = copy.deepcopy(self.original_characters)
        self.characters = self.all_characters
    #
    #(This doesn't need its own class)
    def load_current_party(self, filedata):
        """Gets the current party, from PPC01.ngd. Returns a list of ids.
        This is just 12 bytes, one for each character, laid out:
        9ABC
        5678
        1234"""
        
        data = filedata.read(12)
        return list(data)
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
    
    ###
    def with_mod(self, func):
        #Calls the provided function on all characters.
        #Should be a lambda
        for x in self.all_characters:
            func(x)
        
        return self
    #
#
