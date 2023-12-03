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
        
        #Can't import reference. Cheat instead.
        self.chara_type = type(characters[0])
    def reset(self):
        """Undoes all changes. Reverts back to the original data read in from the save files"""
        self.all_characters = copy.deepcopy(self.original_characters)
        self.characters = self.all_characters
    #
    def get_character(self, name):
        #Allow this to be an echo. No reason not to.
        if type(name) == self.chara_type:
            return name
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

from lot2skill import get_skill, SkillCollection, Noop


class Formation:
    #To iterate over the formation data in order.
    order = list(range(8, 12)) + list(range(4, 8)) + list(range(0, 4))
    def __init__(self, ids, character_list):
        self.character_list = character_list
        self.characters = [character_list.get_character(x) for x in ids]
        self.allow_duplicates = False
    def GetCharacter(self, name):
        return self.character_list.GetCharacter(name)
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
        if c is None:
            return None
        for index in range(12):
            i = Formation.order[index]
            if self.characters[i] == c:
                return index
        return None
    def SetCharacters(self, clist, reverse=True):
        #I guess this should always have a length of exactly 12.
        self.characters = [None] * 12
        if reverse:
            for i in range(len(clist)):
                rev_i = Formation.order[i]
                self.characters[rev_i] = self.character_list.get_character(clist[i])
        else:
            for i in range(len(clist)):
                self.characters[i] = self.character_list.get_character(clist[i])
        #self.characters = [self.character_list.get_character(x) for x in clist]
    def GetCharacterSkills(self, user):
        """ Fetches the skill data for all characters in the current formation.
        Filters out any inapplicable skills, e.g. because the user is in the back row
        This needs to be called once per user, since many skills are "self only"
        """
        all_chara = self.GetCharacterList()
        all_skills = {}
        #2. Get every skill from these characters. Remove duplicates
        for ch in all_chara:
            #level 0 skills are already removed.
            for s_name in ch.list_skills():
                #TODO: I don't need both 'formation' and 'position'
                obj = get_skill(s_name, ch)
                if type(obj) is Noop:
                    print(f"Skill '{s_name}' has no implementation.")
                    continue
                pos = self.GetPosition(ch)
                #print('TEST', s_name, ' -- ', type(obj), pos)
                if not obj.IsActive(user, pos, True):
                    #print(f"{s_name} is not active.")
                    continue
                key = obj.UniqueKey()
                print(obj, key)
                if key in all_skills:
                    if all_skills[key].level > obj.level:
                        #print(f"{s_name} is lower level.")
                        continue
                    #else:
                    #    print(f"{s_name} is same or higher level.")
                all_skills[key] = obj
        return SkillCollection(all_skills)
#
class FakeFormation(Formation):
    """Intended to act as a placeholder for if real formation isn't available
    Used by skills. The user can't be outside of the active party, so as long as you have a user,
    you have a "formation"
    """
    def __init__(self, c):
        self.c = c
        self.characters = [c]
    def GetCharacterList(self):
        return self.characters
    def GetPosition(self, c):
        #ok this isn't quite right, because ideally it should be "whatever damn position you want"
        #both Suwako and Kanako's skills should be active, but that can't be done with a single return.
        return 1
#