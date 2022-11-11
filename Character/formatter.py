from lot2helper import *

import os
import copy
import math

def character_sheet(self):
    """Returns a string of all of the character stats formatted into a table.
    Suitable for printing to the console to see everything at once.
    Vaguely resembles the in-game display"""
    
    #See template.txt for the sketch of what this should look like. It's aiming for fitting in an 80x25 console.
    #Not available: Items (I have IDs but no names), TP, individual affinities and resistances (don't have base data, some skills split this)
    #HP/MP regen (this should be in the base data spreadsheet, but I don't parse skills for it)
    #EXP to next level (Don't know formula)
    
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
    
    real_speed = game_to_db(self.get_stat('SPD'))
    real_speed = ("[" + str(real_speed) + "]").rjust(7)
    
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
        "",
        "",
        "",
    ]

    #I don't thiiiiink there will ever be decimals in here
    return "\n".join(ret).replace('.', ' ')
#
def list_skills(self):
    """List all the skills this character has learned.
    Primarily a debug method to make sure skill IDs match up."""
    
    #self.skilldata = character_skills[id]
    #self.spelldata = character_spells[id]
    #self.skills
    
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
    real_speed = game_to_db(speed)
    
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

        ret.append(format_spell(spellname, delay, formula, speed))
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
