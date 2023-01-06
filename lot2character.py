# -*- coding: utf-8 -*-

from lot2helper import *
#from lot2data import *
from lot2speed import Speed
from DataTemplate import *
from SpellData import SpellData

import os
import copy
import math

#Call data import functions in lot2helper
#(Probably should be in an init function or something)
#spreadsheets
subclass_bonuses = loadSubclassBonuses()
#Taken from FabulaFares's excel sheet
character_basestats = loadCharacterBasestats()

#Parsed from the wiki pages
character_skills = loadCharacterSkills()
character_spells = loadCharacterSpells()
character_titles = loadCharacterTitles()
item_stats = loadItemData()

#Dict of functions within the character class that can be called by with_mod
#Populate this by adding "@mods" in front of the function, which will call function mod in this file.
#(I wanted this to be in Save but the decorator functions are called before Save's __init__)
character_mods = {}

#I don't know how to actually make use of this.
def mods(func):
    """Decorator function (I think?) for specific functions in the Character class.
    Aggregates these functions in a dict."""
    character_mods[func.__name__] = func
    
    return func

class CharacterTemplate(DataTemplate):
    def __init__(self):
        self.fields = [
            Field('level', 4)
            ,Field('exp', 8)
            ,ArrayField('libstats', (stats+affinities), 4)
            ,ArrayField('levelstats', (stats), 4)
            ,Field('subclass_id', 4, validator=lambda x: x in subclasses)
            ,PositionAssert(0x60)
            ,ArrayField('skills', range(SKILL_COUNT), 2)
            ,PositionAssert(0xB0)
            ,ArrayField('subskills', range(SUBCLASS_SKILL_COUNT), 2)
            ,PositionAssert(0xD8)
            ,ArrayField('boost_1s', boost_stats, 1, validator=lambda x: x in (0,1))
            ,PositionAssert(0xE4)
            ,ArrayField('boost_2s', boost_2_stats, 1, validator=lambda x: x in (0,2,3))
            ,PositionAssert(0xEC)
            ,Field('skp_sign', 1)
            ,Field('unused_skill_points', 2)
            ,Field('bns_sign', 1)
            ,Field('unused_bonus_points', 4)
            ,PositionAssert(0xF4)
            ,ArrayField('gems', gem_stats, 2, validator=lambda x: x <= 20)
            ,PositionAssert(0x104)
            ,Field('training_manuals', 1)
            ,Field('unknown', 1)
            ,Field('BP', 3)
            ,PositionAssert(0x109)
            ,ArrayField('items', range(0, 4), 2, validator=lambda x: x <= 980)
        ]
#
class Character:
    """Represents data loaded from a C file in the save folder. Tracks the raw data and has utility functions for dealing with it"""
    template = CharacterTemplate()
    
    def __init__(self, id, filedata):
        self.id = id
        #print (character_basestats)
        self.basestats = character_basestats[id]
        self.skilldata = character_skills[id]
        self.spelldata = character_spells[id]
        #print(self.spelldata)
        self.formatted_spelldata = {id: SpellData(self, self.spelldata[id]) for id in self.spelldata}
        
        if (not id in character_ids):
            raise Exception("Invalid character id - " + id)
        self.name = character_ids[id]
        
        #"name" is easier to work with most of the time.
        self.full_name = character_titles[id]['Name']
        self.title = character_titles[id]['Title']
        
        Character.template.Read(self, filedata)

        self.subclass = subclasses[self.subclass_id]

        #Combine boost skills: first, copy boost1, which is always 0 or 1.
        #Then, if boost2 is set to 2 or 3, overwrite with that value
        #TODO: Check if the character naturally knows the skill and set boost=1 based on that
        #Writing this will be a pain.
        self.boosts = {}
        for f in self.boost_1s:
            self.boosts[f] = self.boost_1s[f]
        for f in self.boost_2s:
            if self.boost_2s[f] > 0:
                self.boosts[f] = self.boost_2s[f]
        
        #Post-process the weird sign byte.
        if self.skp_sign:
            self.unused_skill_points *= -1
            self.skp_sign = 0
        if self.bns_sign:
            self.unused_bonus_points *= -1
            self.bns_sign = 0

        #Everything after this appears to be unused.
        
        #I don't know if this is a common pattern, but if changes are made to the character, they need to be temporary (unless they're saved to disk and the save file is edited)
        #but something like "What-If Yuuka had maxed boost stats and 1000 library levels in Atk and Mag?" are temporary. Don't modify this object.
        #But if a copy is made, that can be modified, so set mutable=True
        #ok I think I do need to manually copy all data from __copy__ which I don't wanna do.
        #Figure this out later...
        #self._mutable = False
    def save_to_file(self, fh):
        """Writes character data to a file. Save hacking. Basically the opposite of the constructor."""
        #Assumes that the file already exists. If something isn't supported (e.g. items), it won't be modified
        #and relies on the old data already being there.
        
        #Sanity.
        fh.seek(0)
        
        #Need to pre-process; the opposite of the post-read post-process.
        #Unfuck the sign stuff.
        #Figure out the Boost stuff.
        self.skp_sign = 0
        if self.unused_skill_points < 0:
            self.skp_sign = 1
            self.unused_skill_points *= -1
        self.bns_sign = 0
        if self.unused_bonus_points < 0:
            self.bns_sign = 1
            self.unused_bonus_points *= -1
        
        #TODO: If also applied to read, figure out the character's base unlocked boost skills
        for f in self.boosts:
            if self.boosts[f] in (0, 1):
                self.boost_2s[f] = 0
                self.boost_1s[f] = self.boosts[f]
            elif self.boosts[f] in (2, 3):
                #I don't think this should set boost_1 because it's not known if this is a natural unlock or not
                self.boost_2s[f] = self.boosts[f]
        #
        
        #TODO: Subclass. I don't think I have a reverse lookup table.
        #Pretty sure I also can't change skills, so, it probably doesn't matter.
        
        Character.template.Write(self, fh)
    #

    #NOTE - this is the up-to-date copy, and probably the only one used.
    #I think the other two are experiments, and not in-use.
    def character_sheet(self):
        """Returns a string of all of the character stats formatted into a table.
        Suitable for printing to the console to see everything at once.
        Vaguely resembles the in-game display"""
        
        #See template.txt for the sketch of what this should look like. It's aiming for fitting in an 80x25 console.
        #Not available: Items (I have IDs but no names), TP, individual affinities and resistances (don't have base data, some skills split this)
        #HP/MP regen (this should be in the base data spreadsheet, but I don't parse skills for it)
        #EXP to next level (Don't know formula)     #TODO: This is known now. Could add.
        
        #Grab all stats. Convert to string. Left or right justify them.
        #This was a comprehension but then I moved the justification out here to make the fstring prettier
        #and god it just got too ugly. Especially after adding MP.
        _stats = {}
        for x in ['HP','MP','ATK','DEF','MAG','MND','SPD','EVA']:
            _stats[x] = str(int(self.get_stat(x)))
            if x in ('MP', 'TP'):
                _stats[x] = _stats[x].rjust(3)
            elif x == 'SPD':
                #A speed of 495000 is enough to go from 0 to 10,000
                _stats[x] = _stats[x].rjust(6)
            else:
                _stats[x] = _stats[x].rjust(18)
        _growths = {}
        for x in stats:
            _growths[x] = str(int(self.get_adjusted_growth(x))).rjust(3)
        #--TP should be included but that isn't implemented. There's also aff/res but ugh
        
        speedobj = Speed(from_game_speed=self.get_stat('SPD'))
        real_speed = ("[" + str(speedobj.GetRealValue()) + "]").rjust(7)
        
        name = self.full_name.ljust(24)
        title = self.title.ljust(60)       #Shows in-game as Class
        exp = str(self.exp).ljust(18)
        level = str(self.level).ljust(7)

        #Class name: The longest is Tenshi's, at 59 characters.
        #Longest name is 22, Eiki (of course)
        #I put them in titles.csv
        
        _levelstats = self.levelstats.copy()
        for x in _levelstats:
            _levelstats[x] = str(_levelstats[x]).rjust(9)
        
        _libstats = self.libstats.copy()
        for x in _libstats:
            _libstats[x] = str(_libstats[x]).rjust(9)
            
        _gems = self.gems.copy()
        for x in _gems:
            _gems[x] = str(_gems[x]).rjust(2)
        
        bp = str(self.BP).rjust(9)
        bonus_stock = str(self.unused_bonus_points).rjust(9)
        skp_stock = str(self.unused_skill_points).rjust(9)
        tms = str(self.training_manuals).rjust(9)
        
        items = []
        for i in self.items:
            i = int(self.items[i])
            if i == 0:
                items.append('None'.rjust(30))
                continue
            if i not in item_stats:
                raise Exception(f"Strange equipped item with id {i}")
            item_name = item_stats[i]['Name']
            item_type = item_stats[i]['Type']       #'main' or 'sub'
            #Longest item name is 27 characters (tied); Portable Oscillation Cannon
            items.append(item_name.rjust(30))
        
        ret = [
            "=" * 80,
            f"....NAME:...{name}.Exp:.{exp}.Lv:.{level}........",
            f"....CLASS:..{title}",
            f"....SUBCLASS:.{self.subclass}",  #Don't bother padding it, just give it the whole line.
            "-" * 80,
            "......STATS:...........GROWTH:.........STATS:...........GROWTH:.................",
            f".HP:..{_stats['HP' ]}..({_growths['HP' ]}).|.MP:..{_stats['MP' ]}..TP:...............................", #TODO: TP
            f".ATK:.{_stats['ATK']}..({_growths['ATK']}).|.DEF:.{_stats['DEF']}..({_growths['DEF']})................",
            f".MAG:.{_stats['MAG']}..({_growths['MAG']}).|.MND:.{_stats['MND']}..({_growths['MND']})................",
            f".SPD:.{_stats['SPD']}.{real_speed}......({_growths['SPD']}).|.EVA:.{_stats['EVA']}.......................",      #Can I fit anything else in EVA's extra space?
            "-" * 80,
            "...Level-up bonuses:............|......Library levels:..........................",
            f".HP:..{_levelstats['HP'] }.................|...HP:..{_libstats['HP']}...............................",
            f".ATK:.{_levelstats['ATK']}..DEF:.{_levelstats['DEF']}.|...ATK:.{_libstats['ATK']}..DEF:.{_libstats['DEF']}...............",
            f".MAG:.{_levelstats['MAG']}..MND:.{_levelstats['MND']}.|...MAG:.{_libstats['MAG']}..MND:.{_libstats['MND']}...............",
            f".SPD:.{_levelstats['SPD']}.................|...SPD:.{_libstats['SPD']}...............................",    #Oops, I forgot there's no eva levels. There's only 6 so it could be on 3 lines, but I do want to group atk/def and mag/mnd
            "",
            "...Gems:........................................................................",   #These could be one line.
            f"........HP:.{_gems['HP']}.MP:.{_gems['MP']}.TP:.{_gems['TP']}.ATK:.{_gems['ATK']}.DEF:.{_gems['DEF']}.MAG:.{_gems['MAG']}.MND:.{_gems['MND']}.SPD:.{_gems['SPD']}.............",
            "-" * 80,
            f"..Battle Points:.{bp}....Lv Bonus stock:...{bonus_stock}.......................",
            f"..Skill points:..{skp_stock}....Training Manuals:.{tms}.......................",
            "=" * 80,
            ".Equipment:.....................................................................",
            f"...{items[0]}...............................................",
            f"...{items[1]}...............................................",
            f"...{items[2]}...............................................",
            f"...{items[3]}...............................................",
            "",
            "",
        ]

        #I don't thiiiiink there will ever be decimals in here
        #The periods just make it easier to visualize within template.txt
        return "\n".join(ret).replace('.', ' ')
    #
    def list_skills(self):
        """List all the skills this character has learned.
        Primarily a debug method to make sure skill IDs match up."""

        ret = []
        for i in range(len(self.skills)):
            level = self.skills[i]
            if level == 0:
                #This includes skipping all the placeholders.
                continue

            maxlvl = None
            s = ""
            if i <= len(boost_stats):
                #All characters have all boost stats...
                name = boost_stats[i] + ' Boost'     #Ignoring high/giga/mega/2 boost for now.
                maxlvl = 5
            elif i >= 30:
                #This is a spellcard.
                data = self.spelldata[i]
                name = data['Name']
                s = "Spellcard: "
                #Wiki doesn't list spellcard costs, not even for awaken skills
                #max level data isn't available, since it was always 5 pre-plusdisk.
            else:
                #Skill.
                data = self.skilldata[i]
                name = data['Name']
                maxlvl = data['Max Lvl']
            s += name + (" - level %d" % level)
            if maxlvl is not None:
                s += '/' + str(maxlvl)
            ret.append(s)
        
        return ret
    #
    def list_spells(self, override_speed=None):
        """List all of the character's spellcards. Uses the speed stat and compares against delay to
        determine the number of ticks it takes to use, then what the upper and lower bounds of that are
        i.e. how close you are to using the spell one tick faster, and how much extra speed you have now
        (But it can't take 90% of stat boosts into account, nor buffs)"""
        #TODO: Subclass spells. Don't have a spreadsheet.
        #TODO: Satori
        
        #Speedy formation change: When the user uses "Formation Change" command, her delay is set to (7500 + SLv * 800).
        #Effective Formation Change: When the user performs a Form Change command to swap a reserve member into the active party, that member's ATB will be set at (7500 + SLv*800).

        #is it worth having a separate entry for these?
        
        #Patchy has a 50% chance to halve delay. I think that'd work better as a separate item;
        #Royal Flare (3200);  Royal Flare (halved) (6600)
        #But that can come later.
        
        #Longest spell name should be 31 characters.
        
        if (override_speed is None):
            speed = self.get_stat('SPD')
        else:
            speed = override_speed
        
        ret = []
        for spellid in (self.spelldata):
            spell = self.spelldata[spellid]
            
            delay = self.get_adjusted_delay(spell)
            spellname = spell['Name']
            formula = spell['Damage Formula']

            #Call helper function in lot2helper.
            ret.append(format_spell(spellname, delay, formula, speed))
        #
        for spell in (attack_spell, formation_spell, concentrate_spell):
            delay = self.get_adjusted_delay(spell)
            
            spellname = spell['Name']

            ret.append(format_spell_oneline(spellname, delay, formula, speed))
        #
        #Basic attack, starting at 50%, form change
        #I think these should be made as psuedo-spells
        
        return ret
    #
    def get_adjusted_delay(self, spell):
        #Actually post-use
        """Returns the effective delay of the given spell. In most cases this is just the spreadsheet row.
        Monk reduces delay by 10%. A handful of awaken skills reduce delay as well.
        Some skills have conditional reductions, e.g. two of Yukari's skills. These are not accounted for."""

        delay = int(spell['Delay'])
        
        if self.id == 13 and spell['ID'] == 33 and self.skills[25] > 0:
            #Nitori's Portable Versatile Machine (33), with Enhanced Versatile Machine
            delay = 9320
            
        #Some skills modify formation change
        #But then it's divided into doing-switching and being-switched.
        
        #Mamizou's High-Speed Normal Attack
        if self.id == 50 and spell['ID'] == -1 and self.skills[23] > 0:
            delay = 8600
        
        #Sample data:                   #Normally       #With monk:
        #Fire Bird -Flying Phoenix-     5900            6310
        #Tsuki no Iwakasa's Curse       5000            5500
        #Fujiyama Volcano               2000            2800
        if self.subclass == 101 and self.subskills[3] > 0 and spell['ID'] not in (-2, -8, -9):
            #Monk
            #The dumb hardcoded IDs are for things explicitly unaffected by this skill:
            #formation change (-2) and the specific %s. Monk does have a skill for changing battle start ATB but it goes to 100%
            #...This can probably be simplified.
            delay = 10000 - ((10000 - delay) * 0.9)
        
        return delay
    #
    #TODO: This isn't called for HP, MP, EVA
    def get_equipment_stat(self, stat):
        """Gets the combined bonus (multiplier or flat boost; it depends on the stat)
        of all equipped items.
        Includes the Maintenance bonus."""
        bonus = 0
        for i in self.items:
            i = int(self.items[i])
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
        
        #Check easter egg bonus: If the following are equipped, add bonus stats
        #Cypress Stick (5), Bone Stake (257), Happy Hat (265), Bludgeon (249)
        #(It's a DQ reference). Order matters. This does not stack with maintenance.
        #Bonus is +50% all, +50 affinity, +20 resists
        if self.items[0] == 5 and self.items[1] == 257 and self.items[2] == 265 and self.items[3] == 249:
            if stat in stats or stat in affinities:
                bonus += 50
            elif stat in resistances:
                bonus += 20
        
        return bonus
    #
    def get_equipment_specials(self):
        """Returns all 'special' attributes of current equipment. This is things like a quartz charm's
        flat damage boost. There's no automatic parsing.
        Filters out empty results. [] means no items equipped with special attributes."""
        results = []
        for i in self.items:
            i = int(self.items[i])
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
        #Exact formula, datamined from the game.
        if level == None:
            #can't use self.level as a default value (unless python3 changes that)
            level = self.level
        levelrate = int(self.basestats['Leveling rate'])
        
        a = (level+1) * 20
        b = (level * 0.4) + 1
        
        c = int(a * b)
        return int((c * levelrate) / 100.0)
        #I think there's some kind of level cap of 9999999 or an exp cost of 900,000,000,000
        #but I'm not entirely sure what happens there.
    #
    def get_xp_to_level(self, target):
        level = self.level
        total = 0
        while (level < target):
            total += self.get_xp_to_next(level)
            level += 1
        return total
    #
    def level_if_able(self):
        needed = self.get_xp_to_next(self.level+1)
        if (self.exp > needed):
            self.exp -= needed
            self.level += 1
            self.unused_bonus_points += 1
            self.unused_skill_points += 1
            return True
        return False
    #
    def get_total_xp(self):
        """Calculates the total amount of XP this character has earned 
        (equivalent to resetting their level back to 1).
        This includes the "spare" exp. """
        level = self.level
        total = self.exp
        while (level > 1):
            level -= 1
            total += self.get_xp_to_next(level)
        return total
    #
    def get_money_to_next(self, stat, level=None):
        #TODO: Test this, make sure I didn't mess anything up
        #Especially test affinity, since the float errors might cause issues.
        #I'm hoping using a while loop insead of exp duplicates the drift
        #TODO: Actually do something with this function.
        if not (stat in stats or stat in affinities):
            raise Exception("Unrecognized stat: " + str(stat))
        if level == None:
            level = self.libstats[stat]
        #print(stat, level)
        multiplier = int(self.basestats['Library'])
        #normal stats and affinities use a different formula.
        if stat in stats:
            #a = floor((level+2)*2.5) * multiplier; b = floor(a / 112) * level; final cost = a + b
            a = int(int(int((level+2)*2.5) * multiplier) / 100)
            b = int(a / 112) * level
            return a+b
        elif stat in affinities:
            #floor((level+4) * 1200 * (1.04 ^ level) / 100) * multiplier
            a = (level+4) * 1200
            for i in range(level):
                #Oh. Maybe int was all that was needed. Need to double check with larger values
                a = int(a * 1.04)
            return int(int(a / 100) * multiplier / 100)
            #Max level is 100
        #Else, already threw
    #
    def get_total_money(self, stat=None):
        """Calculates the total amount of money spent on a single stat
        (equivalent to using a tome of reincarnation, but only on one stat)
        If stat is None, call the function again for every stat and return that sum.
        """
        total = 0
        if stat is None:
            for s in self.libstats:
                total += self.get_total_money(s)
            return total
        level = self.libstats[stat]
        
        #TODO: This is going to be non-trivial time for levels in the 10ks, for all stats and all characters...
        #Is it possible to combine it to a single operation instead of a loop?
        while (level > 0):
            level -= 1
            total += self.get_money_to_next(stat, level)
        return total
    #
    #TODO: Function for "get total money spent (on stat)"
    def get_offense_stat(self):
        """Determines if this character is a MAG or ATK attacker. Only checks growth, not spellcards.
        For composite attackers, it is assumed that if the stats are the same, it doesn't matter
        which is boosted, so there's no special casing for composite.
        There is a special case for Yuuka because she is silly."""
        maggrowth = self.get_adjusted_growth('MAG')
        atkgrowth = self.get_adjusted_growth('ATK')
        if self.id == 43:       #Yuuka
            #Her atk growth is higher, even though all her cards are MAG based
            #it's possible she's being built as an atk user (subclasses)
            #so try to figure out if she's being treated as an attacker.
            #If more levelup bonuses are put into ATK than MAG, treat her as a physical attacker
            #If these are the same (probably means both are 0), check library levels as well. 
            #Otherwise, she's magic.
            #(Reasoning is that lvlup bonuses are a finite resource; lib levels can just be spammed)
            libatk = self.libstats['ATK']
            libmag = self.libstats['MAG']
            lvlatk = self.levelstats['ATK']
            lvlmag = self.levelstats['MAG']
            if lvlatk > lvlmag:
                return 'ATK'
            if lvlatk == lvlmag and libatk > libmag:
                return 'ATK'
            #But return MAG if she has no (or equal) stat allocations
            return 'MAG'
        if (maggrowth > atkgrowth):
            return 'MAG'
        else:
            return 'ATK'
    #
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
    def set_free_bonuses_to_stat(self, stat):
        """Same as set_bonuses_to_stat, but only moves unallocated points"""
        totalbonuses = self.unused_bonus_points
        self.unused_bonus_points = 0
        self.levelstats[stat] += totalbonuses
    #
    @mods
    def set_bonuses_to_offense(self):
        """Redistribute all level up bonuses to either Mag or Atk, depending on the user's adjusted growth."""
        return self.set_bonuses_to_stat(self.get_offense_stat())
    #
    @mods
    def set_free_bonuses_to_offense(self):
        """Redistribute all unused level up bonuses to either Mag or Atk, depending on the user's adjusted growth."""
        return self.set_free_bonuses_to_stat(self.get_offense_stat())
    #
    @mods
    def set_free_bonuses_to_most_used(self):
        """Redistribute all unused level up bonuses to the stat
        that currently has the highest number of bonus points.
        If there aren't any points allocated it won't do anything."""
        maxstat = ""
        maxvalue = 0
        for x in self.levelstats:
            if self.levelstats[x] >= maxvalue:
                maxstat = x
                maxvalue = self.levelstats[x]
        if maxvalue == 0:
            return None
        return self.set_free_bonuses_to_stat(maxstat)
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
#
