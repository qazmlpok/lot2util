import re
import math
from lot2data import affinities, monster_types

#Skill evaluation needs full formation data.
#No point trying to use anything less.
#This will include all 12 characters, and the full data.
#so "position" can be removed as a parameter; fetch the position from the formation data.
#do I need both user and owner?

#----------------------
class SkillCollection:
    def __init__(self, skills):
        #Or should this take in a character list?
        self.skills = skills
    def GetCounters(self):
        """ Returns all "counters" that are used in the current skill set.
        Intent is that the caller can inspect this list and provide real-world potential values
        """
        return set([x.CounterName() for x in self.skills.values() if x.CounterName() is not None])
    def SetCounter(self, name, val):
        for x in self.skills.values():
            x.SetCounterValue(name, val)
    def SetAllCounters(self, val):
        """ Set all counters to the same value. Intention is that you can just pass in 1000
        and that'll activate every skill. The skill in question will restrict the real value
        """
        for n in self.GetCounters():
            self.SetCounter(n, val)
    def __repr__(self):
        return f'  Skills: [{", ".join([x.name for x in self.skills.values()])}]'
#----------------------

#Populated by decorators.
skill_list = {}
def skillname(func):
    #print(func)
    skill_list[func.__name__] = func
    
    return func

def get_skill(full_name, owner, formation):
    """ Perform a lookup on the skill name to find the appropriate class.
    This should be a static method in Skill but whatever.
    """
    name = skill_to_class_name(full_name)
    if name in skill_list:
        ret = skill_list[name](owner)
    else:
        ret = Noop(owner)
    #Or add it as a parameter.
    ret.name = full_name
    ret.level = owner.get_skill_level(full_name)
    ret.formation = formation
    return ret

def skill_to_class_name(name):
    """ Do a bunch of transformations to get a real skill name into something that looks more like 
    a Python class name.
    """
    name = name.replace(u'’', "'").replace("'s", "").replace("s'", '').replace(u'⑨', 'Nine').replace('-', ' ') \
            .replace("I'm", '').replace('+', 'Plus').replace('7', 'Seven').replace('5', 'Five')
            
    #remove certain characters
    name = re.sub(r'[?!()&,.]', '', name)
    #Remove leading "The"
    name = re.sub(r'^[Tt]he', '', name)
    #Remove lower case words, e.g. "of"
    name = re.sub(r'\b[a-z]+\b', '', name)
    return name.replace(' ', '')

class Skill:
    """
    """
    def __init__(self, owner):
        #This is the in-game description; will be taken from the spreadsheet
        #e.g. When Mokou is on the front line, increase Fire damage output by (SLv * 15)% for all frontliners.
        #...is there any point?
        self.description = ''
        
        #Will be set by the caller.
        self.name = None
        self.level = None
        
        #The character that owns this skill.
        self.owner = owner
        
        #List of "counters" - these are settings that can't really be determined automatically
        #e.g. the number of Fighting Spirit stacks. How long do you anticipate staying out?
        #Each skill will need to report which "types" it tracks (a handful share them)
        #and change behavior accordingly. The skills will also need to clamp the input
        #e.g. you can't have more than 6 Fighting Spirit stacks (actually slvl * 3).
        self.counters = {
            #hp etc should be assumed to be full (100%)
            'hp' : 100,
            'mp' : 100,
            'target_hp' : 100,
        }
        
        #Configuration; subclasses should overwrite these in the constructor.
        #Most skills only affect the user. The ones that don't are almost all front only.
        self.self_only = True
        self.front_only = True
    def PreApply(self, spell):
        """A small number of skills do need to be processed first.
        Specifically, anything that alters the spell's elements _must_ be done here
        otherwise there's no guarantee the element-boost skills would correctly affect it.
        There may be others. Some can probably be done at either point.
        I don't think anything but 'spell' is needed here.
        """
        pass
    def Apply(self, user, spell, target, attacking=True):
        """ For applying modifications while attacking a target (leave target None for 'generic')
        'Owner' is the character that possess the skill. Used to get skill levels.
        'user' is the character that is attacking. Not always owner.
        'position' is of the Owner; is needed to know if this is frontline or not. A few skills require specific slots.
        It is assumed that user is in the frontline (otherwise they can't attack).
        'spell' is needed to know the element and atk/mag usage.
        """
        #raise Exception('Implement in subclass.')
        pass
    def CounterName(self):
        """ Intended for use with skills that have a "counter" or "stacks" or similar mechanism
        (except kinship bonuses - those can be determined)
        e.g. number of defeated characters (last fortress), turns spent in combat (fighting spirit, overheat)
        Anything where the only way to do anything with this is to ask the user.
        """
        return None
    def SetCounterValue(self, name, value):
        #_maybe_ add a handful of special cases, like setting hp=1 also sets "low_hp"
        #or setting target_trr also sets target_ailment.
        self.counters[name] = value
    def IsActive(self, user, attacking=True):
        #This only needs to be overridden for the fixed-position skills (e.g. Kanako)
        #attacking is a TODO; I don't have any defense stuff even planned.
        if self.owner is not user and self.self_only:
            return False
        if self.front_only and not self.formation.IsInFront(user):
            return False
        return True
    def CounterActive(self):
        #TODO: It should be safe to delete this and do everything in IsActive
        #I shouldn't be filtering out IsActive pre-emptively.
        return True
    def IsApplicable(self, spell, target):
        """ Returns true if the skill is applicable to the selected spell.
        If the skill references a specific spell, it must be to that. 
        If the skill has an element, spell must include that. etc.
        """
        return True
    def Render(self, user):
        """ Return a text description of what this skill will do,
        with the current skill level applied. Position is used to filter conditions,
        but not spell type.
        """
        #raise Exception('Implement in subclass.')
        #Remove the parameters? Can I use IsActive to filter first?
        return ''
    def UniqueKey(self):
        """ Certain skills will not stack. Easiest example is the "+x dmg against <type>"
        skills. Only one can be active.
        Multiple copies of skills (from other people) will never stack.
        Use this to return a unique identifier, if multiple skills need to conflict.
        """
        return str(type(self))
    def __repr__(self):
        return f"Skill {self.name}, owner {self.owner.name} level {self.level}"

class CounterSkill(Skill):
    def __init__(self, owner):
        Skill.__init__(self, owner)
        #A bunch of counters are on/off.
        #Minimum possible value for the skill's counter (if it exists). Some skills are active on turn 1.
        self.min_counter = 0
        #Maximum possible value for the skill's counter. Some skills use slvl. This is just for when it's a fixed value.
        self.max_counter = 1
        #Minimum value for the skill to be active. Again, most are on/off.
        #Some skills (i.e. HP) use a maximum; do that in the specific skill.
        self.counter_active_min = 1
        #...move to constructor.
        self.counter_name = None
    def CounterName(self):
        if self.counter_name is None:
            raise Error("Configuration error.")
        return self.counter_name
    def CounterActive(self):
        #If has a counter, use this to filter it out.
        #Counters are vaguely dynamic, which is why this was extracted from 
        counter = self.CounterName()
        if (counter is not None):
            val = self.GetCounterValue(counter)
            if val < self.counter_active_min:
                return False
        return True
    def GetCounterValue(self, name):
        val = 0
        if name in self.counters:
            val = self.counters[name]
        if val < self.min_counter:
            val = self.min_counter
        if val > self.max_counter:
            val = self.max_counter
        return val
class StatSkill(Skill):
    """ A skill that boosts stats; conditionally, so not shown on the character screen
    (unlike the Boost skills, or the other non-conditional skills, which _do_ show)
    This class is mostly just to signal what the skill does.
    """
    def __init__(self, owner):
        Skill.__init__(self, owner)
        #These are always self-only, but that's the default
        #frontline only is iffy. It only matters if they boost SPD
        #But I'm pretty sure they _are_ active even in the back.
        self.front_only = False
        
        #Not implemented. But these should always be attack+defense.
        self.attacking = True
        self.defending = True
    def _boost_stat(self, stat, c, factor, counter):
        if stat == 'ALL':
            stat = ['ATK','DEF','MAG','MND','SPD']
        if type(stat) == str:
            stat = [stat]
        for s in stat:
            c[s] *= (1 + ((factor/100) * counter))
            c[s] = int(c[s])
class StatReductionSkill(Skill):
    """ Like stat skill but modifies the target's stat instead.
    These are not always self=true; Kaguya, I think, has one that lowers def while she's in front
    """
    def __init__(self, owner):
        #I don't think there's an atk/def difference; but it'd only matter for speed.
        #Not implemented. But these should always be attack+defense.
        self.attacking = True
        self.defending = True
    def _lower_stat(self, stat, target, factor, counter):
        if stat == 'ALL':
            stat = ['ATK','DEF','MAG','MND','SPD']
        if type(stat) == str:
            stat = [stat]
        for s in stat:
            c[s] *= (1 - ((factor/100) * counter))
            c[s] = int(c[s])
class DamageBoost(Skill):
    """ Skill boosts spell damage directly.
    """
    def _spell_mult(self, spell, factor):
        spell['Multiplier'] *= (1 + ((factor/100)))
#

class Noop(Skill):
    def IsActive(self, user, attacking=True):
        return False

#How to evaluate a skill? It will do one of these:
#1. Increase stats, on the character screen (boost skills, but also others). This is already done
#1.a. Boost stats conditionally, e.g. via kinship bonuses. This requires full party knowledge.
#2. Provide some uncapturable benefit, e.g. efficient formation change or +xp. Leave as noop.
#3. Provide a self benefit
#3.a. ...based on a counter
#3.b. ...based on some condition
#4. Provide a party-wide benefit
#5. Buff another skill - "Last fortress's effect is doubled"
#6. Buff a specific spellcard

@skillname
class Bloodsuck(DamageBoost):
    #Additionally, if the attack was single-target, buff user's all stats by 8% and increase the damage done by 16%.
    #Skip the hp regen.
    def IsApplicable(self, spell, target):
        return spell['Target'] == 'Enemy'
    def Apply(self, user, spell, target, attacking=True):
        mult = 16
        self._spell_mult(spell, mult)
@skillname
class HakkeroChargeMode(DamageBoost, CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.counter_name = 'HakkeroCharge'
        self.max_counter = 25
        self.min_counter = 1
    #Charge works on everything.
    #Charge wins if both are learned.
    def Apply(self, user, spell, target, attacking=True):
        counter = self.GetCounterValue(self.CounterName())
        self._spell_mult(spell, counter * 4)
@skillname
class HakkeroCustomMode(DamageBoost):
    personal_skills = ['Magic Missile', 'Asteroid Belt', 'Master Spark']
    #This only works on personal skills.
    def IsApplicable(self, spell, target):
        s = super(spell, target)
        if not s:
            return False
        return spell['Name'] in HakkeroCustomMode.personal_skills
    def IsActive(self, user, attacking=True):
        charge = owner.get_skill_level('Hakkero Charge Mode')
        if charge > 0:
            return False
        return super(user, attacking)
    def Apply(self, user, spell, target, attacking=True):
        self._spell_mult(spell, 25)

@skillname
class AssaultPoint(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.counter_name = 'AssaultPoint'
        self.front_only = False
    #When the user inflicts damage on an enemy, inflict the special effect ""Assault Point"". Enemies with this effect suffer 25% more damage from allies. This effect has a 50% chance of wearing off when the afflicted enemy takes a turn.
    #okay, so this is going to be weird. If it's active, it doesn't even require the user to be in the front.
    def Apply(self, user, spell, target, attacking=True):
        mult = 25
        self._spell_mult(spell, mult)
#Grand Incantation - no idea what to do about this. I guess average it out?

#-----------------------
# Skills that modify specific spells
#-----------------------

@skillname
class ShinigamiScythe(Skill):
    mag_skills = ['Short Life Expectancy','Ferriage in the Deep Fog','Scythe that Chooses the Dead']
    atk_skills = ['Narrow Confines of Avici']
    def __init__(self, owner):
        Skill.__init__(self, owner)
        
        #Adds a (SLv * 10)% ATK factor into Narrow Confines of Avici's base formula, 
        #along with a (SLv * 10)% MAG factor into Short Life Expectancy, Ferriage in the Deep Fog, 
        #and Scythe that Chooses the Dead's base formulas.
    def Apply(self, user, spell, target, attacking=True):
        #Note - spell should always be a _copy_ as it will be modified
        #(I don't want to make a new copy each time)
        #I need to get the skill level.
        if spell['Name'] in ShinigamiScythe.atk_skills:
            #Narrow Confines
            spell['ATK'] = 10 * 1
        if spell['Name'] in ShinigamiScythe.mag_skills:
            #Her other 3 spells
            spell['MAG'] = 10 * 1
        #Should this return anything?
        return
    def IsApplicable(self, spell, target):
        #Since these needs to be False for a subclass skill, or basic attack.
        #Honestly I should be using names, since those are globally unique...
        return spell['Name'] in ShinigamiScythe.mag_skills or spell['Name'] in ShinigamiScythe.atk_skills
#Enhanced Shikigami Control - Shikigami ""Ran Yakumo +"" will receive the same damage boost and delay reduction from Ran and Chen in the back
#That needs its own class...
#

#The Lost Emotion - Modifies concentrate

#SevenElementalTransformations
#I guess this should just add a counter, and then modify all of the user's spells?
#HighSpeedNormalAttack  - only modifies delay

#TrueAdministrator
#This is stat boosts, but also modifies Tradition of Just Rewards
#Modified by Transcendental Administrator

#Kokoro's Masks
#I have no idea what to do about these.
#It's a 12% bonus/debuff. 30% to herself with the modifier skill (66 Emotions Convergence) (I think this includes the debuffs)
#Two skills also reduce/eliminate te debuff effect: Empty-Hearted Masks Dance, Power of the Mask's Creator (requires Miko)

#Kokoro also has Fighting Spirit from a _spellcard_ not a skill.



#History Accumulation - this has two tokens...
#SwordSpirit
    #When Youmu concentrates, gain the ""Sword Spirit"" effect. If she attacks while having full HP and this effect, remove the effect and reduce her HP by 20% to increase the damage by 50%. (Plus Disk only)
#AsuraBlood
    #(bonus is 10% at max HP, and then increases per each % of lost HP)
#TomboyishGirlVengeance
    #Increases damage dealt with personal spellcards on speed debuffed enemies by Debuff*2.5 (max 125%).
#JealousyManipulation
    #Parsee's stats will increase the more units (allies and enemies) are affected by Debuffs (5% stat increase per Debuffed unit)
    #Ugh.
#LunarPower
    #When the user is in the front, all other frontliners ignore 25% of enemy defense when attacking
#ImperishableShooting
    #Increase ATK commensurate with TP lost. For each TP missing, increase ATK by 1%.
    #Unlike hp/mp, that's not a %
#Proof of the Fastest
    #Counter; 4% spd and 10% per. Cap 10.
#Trauma Recollection - 12% * lvl if weakness. For everyone
#Terrifying Hypnotism Additional lvl * 12%, but user only
#MonsterTanukiWisdom - it's basically fighting spirit


#Other generator type skills:
#Kinship (just need a list of characters and the stat bonus)
#stat boost only skills (these are already handled elsewhere, so maybe noop is better)
#Honestly most skills should be a generator - only a custom "is this applicable" is really needed.

#-----------------------
#Conditional stat boosts
#-----------------------
@skillname
class LastFortress(CounterSkill, StatSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        StatSkill.__init__(self, owner)
        self.counter_name = 'LastFortress'
        self.max_counter = 11
    #Increases Yuugi's stats for every character downed in battle. (~4% stat increase per character)
    #Is that not exact?
    def Apply(self, user, spell, target, attacking=True):
        modifier = 4
        extra = self.owner.get_skill_level("Last Fortress+")
        if extra > 0:
            modifier = 8
        counter = self.GetCounterValue(self.CounterName())
        self._boost_stat('ALL', user, modifier, counter)
@skillname
class ShikigamiHeavyAccelAttack(CounterSkill, StatSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        StatSkill.__init__(self, owner)
        self.max_counter = 10
        self.min_counter = 2
        self.counter_name = 'HeavyAccel'
    def Apply(self, user, spell, target, attacking=True):
        counter = self.GetCounterValue(self.CounterName())
        self._boost_stat('ATK', user, 5, counter)
@skillname
class BishamontenWrath(CounterSkill, StatSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        StatSkill.__init__(self, owner)
        self.max_counter = 50
        self.min_counter = 0
        self.counter_name = 'BishamontenWrath'
    def Apply(self, user, spell, target, attacking=True):
        counter = self.GetCounterValue(self.CounterName())
        self._boost_stat('ATK', user, 5, counter)
@skillname
class FantasySealBlink(CounterSkill, StatSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        StatSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.max_counter = 25
        self.counter_name = 'FantasySealBlink'
    def Apply(self, user, spell, target, attacking=True):
        #Okay, this skill is weird. It actually has 2 effects.
        #all stats are increased by (counter * 5)%
        #all other frontliners' SPD is increased by (counter * 3)%
        counter = self.GetCounterValue(self.CounterName())
        if counter > self.level:
            counter = self.level
        self._spell_mult(spell, 5 * counter)
        #Figure the speed thing out later.
#-----------------------
#Ailment based skills
#-----------------------
@skillname
class Adversity(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.counter_name = 'ailment'
    #This is effectively a counter skill - active if a ailment is present
    #It is also modified by another skill - Adversity+
    def Apply(self, user, spell, target, attacking=True):
        mult = 10
        #I'm assuming this is just additive.
        lvl = self.level + self.owner.get_skill_level('Adversity+')
        self._spell_mult(spell, mult * lvl)
@skillname
class TwoWayCurse(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.counter_name = 'ailment'
    #Defensive as well.
    def Apply(self, user, spell, target, attacking=True):
        mult = 12
        if attacking:
            self._spell_mult(spell, mult * self.level)
        else:
            #I don't have a defensive equivalent.
            pass
@skillname
class HealthySpirit(CounterSkill, StatSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        StatSkill.__init__(self, owner)
        self.counter_name = 'ailment'
    #This is basically !'ailment'. Except also !debuff
    def CounterActive(self):
        #Active if no ailment. It's the inverse of Adversity, basically.
        #If adversity does fancy checking for specific ailments, od that here too.
        val = self.GetCounterValue(self.CounterName())
        if val == 0:
            return True
        return False
    def Apply(self, user, spell, target, attacking=True):
        self._boost_stat(['ATK', 'DEF', 'MAG', 'MND'], user, 10, 1)
@skillname
class FinalBlow(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.counter_name = 'target_ailment'
    #This is effectively a counter skill - but if the target has a ailment.
    #Boosted by Jealousy-Fueled Final Blow
    def Apply(self, user, spell, target, attacking=True):
        mult = 16
        if self.owner.get_skill_level('Jealousy-Fueled Final Blow') > 0:
            mult = 32
        self._spell_mult(spell, mult * self.level)
@skillname
class WaterproofGhostUmbrella(DamageBoost):
    def __init__(self, owner):
        DamageBoost.__init__(self, owner)
    def Apply(self, user, spell, target, attacking=True):
        mult = 33
        self._spell_mult(spell, mult * self.level)
    #Which should (somehow) imply "target_ailment"...
    def CounterName(self):
        return 'target_terror'
@skillname
class AstonishingGhostUmbrella(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.counter_name = 'target_terror'
    def Apply(self, user, spell, target, attacking=True):
        mult = 40
        #This is defensive.
        #self._spell_mult(spell, mult * self.level)
@skillname
class TerrorUntoDeath(CounterSkill, DamageBoost):
    kogasa_spells = ['Karakasa Surprising Flash', "A Rainy Night's Ghost Story", 'Drizzling Large Raindrops']
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.counter_name = 'target_terror'
    def IsApplicable(self, spell, target):
        #Since these needs to be False for a subclass skill, or basic attack.
        #Honestly I should be using names, since those are globally unique...
        return spell['Name'] in TerrorUntoDeath.kogasa_spells
    def Apply(self, user, spell, target, attacking=True):
        mult = 10
        self._spell_mult(spell, mult * self.level)
@skillname
class SilentSingingVoice(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.counter_name = 'sil_count'
    #Wriggle has one too, I think.
    #Modified by Deaf to All but the Song
@skillname
class CursedHinaDoll(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        #Sum of all debuffs, I think.
        self.counter_name = 'debuff'
#Lunar Sage's Wisdom is PSN, PAR or TRR. ugh.

#-----------------------
#HP/MP/TP based skills
#-----------------------
@skillname
class Desperation(CounterSkill, StatSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        StatSkill.__init__(self, owner)
        #Low HP
        self.counter_name = 'hp'
    def CounterActive(self):
        val = self.GetCounterValue(self.CounterName())
        #"HP is less than (20 + SLv * 20)%"
        if val > (20 + self.level * 20):
            return False
        return True
    def Apply(self, user, spell, target, attacking=True):
        self._boost_stat('ALL', user, 25, 1)
@skillname
class PandemonicSprinkle(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        #Full hp
        self.counter_name = 'hp'
    def CounterActive(self):
        val = self.GetCounterValue(self.CounterName())
        #"HP is full" (pretty sure overheal counts)
        if val >= 100:
            return True
        return False
    def Apply(self, user, spell, target, attacking=True):
        self._spell_mult(spell, self.level * 5)
@skillname
class AbilityCausePhenomena(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        #Full mp
        self.counter_name = 'mp'
@skillname
class AdamantHelix(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        #
        self.counter_name = 'target_hp'
@skillname
class FreeSpiritedOni(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        #
        self.counter_name = 'target_hp'
@skillname
class TormentingNature(CounterSkill):
    #Yuuka will deal bonus damage the lower the target's health is. The damage bonus maxes at 40%. No damage bonus will be given when the target is at full HP.
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        #
        self.counter_name = 'target_hp'
#-----------------------

@skillname
class HoshigumaDish(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        #Bunch of weird stuff.
        self.counter_name = 'target_count'


#-----------------------
# Defensive skills
#-----------------------

#Cleansed Crystal Mirror - Reduces all damage taken by (SLv * 5)% if Eiki is on the front line
#Modified by Ability to Judge Morality. Except it might not work? I can't remember.

@skillname
class SacredAuthorityGods(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.max_counter = 5
        self.counter_name = 'Onbashira'
    #When the user uses Mad Dance on Medoteko, increase Onbashira counter by 1. Increase user's damage output by (counter * 10)% and decrease user's damage intake by (counter * 5)%. The counter maxes at 5.
    def Apply(self, user, spell, target, attacking=True):
        counter = self.GetCounterValue(self.CounterName())
        if attacking:
            self._spell_mult(spell, counter * 10)
        else:
            pass

@skillname
class ChinaQigong(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.max_counter = 8
        self.min_counter = 1
        self.counter_name = 'ChinaQigong'
    def Apply(self, user, spell, target, attacking=True):
        counter = self.GetCounterValue(self.CounterName())
        if counter > self.level:
            counter = self.level
        mult = 10
        superQigong = self.owner.get_skill_level("Chinese Girl's Super Qigong")
        if superQigong is not None and superQigong > 0:
            mult = 20
        self._spell_mult(spell, mult * counter)
    def CounterName(self):
        #Modified by Chinese Girl's Super Qigong
        #Also this should just be hardcoded to be 1, lol.
        return 'ChinaQigong'
@skillname
class Overheating(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.max_counter = 5
        self.min_counter = 0
        self.counter_name = 'Overheating'
    def Apply(self, user, spell, target, attacking=True):
        #Can be modified by Enhanced Versatile Machine
        mult = 15
        extra = self.owner.get_skill_level("Enhanced Versatile Machine")
        if extra > 0:
            mult = 20
        counter = self.GetCounterValue(self.CounterName())
        self._spell_mult(spell, mult * counter)
@skillname
class FightingSpirit(CounterSkill, DamageBoost):
    #Whenever the skill holder takes an action, she gains a "Fighting Spirit level" that reduces damage taken and increases damage dealt by (Fighting Spirit level * 5)%, up to a maximum of (SLv * 3) stacks. Wears off if she switches out.
    #Can be modified by Morale Maintenance. But doesn't really matter.
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.max_counter = 15
        self.min_counter = 0
        self.counter_name = 'FightingSpirit'
    def Apply(self, user, spell, target, attacking=True):
        counter = self.GetCounterValue(self.CounterName())
        if counter > self.level * 3:
            counter = self.level * 3
        if attacking:
            self._spell_mult(spell, counter * 5)
@skillname
class HighBlazing(CounterSkill, DamageBoost):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        DamageBoost.__init__(self, owner)
        self.max_counter = 15
        self.min_counter = 0
        #Uses fighting spirit. Despite 'blazing' in name, self-only.
        self.counter_name = 'FightingSpirit'
    def Apply(self, user, spell, target, attacking=True):
        counter = self.GetCounterValue(self.CounterName())
        #Same rules as Fighting, since it uses that token.
        if counter > self.level * 3:
            counter = self.level * 3
        if attacking:
            self._spell_mult(spell, self.level, counter)
    def IsApplicable(self, spell, target):
        #Check element. Reminder; spell can be multi element.
        if 'FIR' in spell['Element']:
            #FIR only.
            return True
        return False


 #Five Impossible Requests - screw that.
 #Extra Attack - this is also gonna be kinda weird.
 #Modified by Vengeful Cat's Erratic Step
@skillname
class KodokuPlatePileup(CounterSkill):
    #Using Futo-only spells will increase the Sake Cups counter by 2. The counter maxes out at (SLv). Damage dealt is raised by (counter * 3)%. When the user is hit, the counter will be decreased by 1 and damage taken is reduced by 16%.
    #Modified by Offering - Okami Omononushi. Unless Offering - Mikoto Nigihayahi. Unless unless Leyline to a Dragon's Nest
    #Sigh.
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.max_counter = 10
        self.min_counter = 0
        self.counter_name = 'SakeCup'

@skillname
class TokikoThickBookCQC(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.counter_name = 'Reading'
    #Reading actually froms the spellcards directly. But this is close enough.
    #If the skill holder is under the effect of "Reading", increase DEF and MND by 25%. If the skill holder is not under the effect of "Reading", increase ATK and MAG by 25%.
@skillname
class BookwormYoukaiArdor(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.counter_name = 'Reading'
    #When the skill holder is under the effect of "Reading", "The Count of Monte Cristo" and "Musketeer d'Artagnan"'s special effects are further strengthened, and the spells' power is also increased. When this effect activates, there is a low chance that "Reading" effect will disappear.
@skillname
class JackRipperSilverKnife(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.min_counter = 1
        #"J.t. Ripper Lv"
        self.counter_name = 'JackRipper'
    #When the user receives a turn, increase Jack the Ripper counter by 1. When attacking, the damage is increased by (counter * 5)%. When the user is attacked, the existing counter is halved. The counter maxes at 20.
@skillname
class FroggyHibernation(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.counter_name = 'Hibernation'
#Destruction Roulette another pita one.

@skillname
class SkyCreation(DamageBoost):
    def __init__(self, owner):
        DamageBoost.__init__(self, owner)
    def Apply(self, user, spell, target, attacking=True):
        self._spell_mult(spell, 16 * self.level)
    def IsActive(self, user, attacking=True):
        #Always call super - this is to get the is_self stuff.
        s = Skill.IsActive(self, user, attacking)
        if s is False:
            return False
        return self.formation.IsInPosition(user, lambda x: x == 3)
        #return position == 3
@skillname
class EarthCreation(DamageBoost):
    def __init__(self, owner):
        DamageBoost.__init__(self, owner)
    def Apply(self, user, spell, target, attacking=True):
        self._spell_mult(spell, 12 * self.level)
    def IsActive(self, user, attacking=True):
        #Always call super - this is to get the is_self stuff.
        s = Skill.IsActive(self, user, attacking)
        if s is False:
            return False
        return self.formation.IsInPosition(user, lambda x: x == 0)
        #return position == 0

#-----------------------
# Target modifying skills
#-----------------------
#Ash Rekindling - ignore 30% defense
#Sheer Force - reduce enemy's elemental affinity to (100 + (affinity - 100) / 2) if above 100
#Enhanced Doll Mobility - ignore (SLv * 10)% of enemy defenses
#Precisely Controlled Dolls - there is a (SLv * 10)% chance to use the lower of enemy's defenses for damage calculations
    #That's a chance? How annoying
#Girl of Knowledge and Shade: When attacking with an element the enemy resists, reduce enemy's elemental affinity to (100 + (affinity - 100) / 3)
#Modified by Infinite Book Collection - reduces the activation threshold of Girl of Knowledge and Shade, making it reduce affinity to (50 + (affinity - 50) / 3) as long as the target has more than 52 affinity to the element.
# Hagoromo Like Sky - Normal attacks will bypass (SLv * 40) % of the enemy's Defense/Mind, and deal (SLv * 20) % more damage (also affects Magic Counter)
    # I guess this should be under "specific card"
#Magic Counter+ - same. Move.


#This annoying effect is random. Use the counter to say if it "works" or not.
#No reason to have a separate name.
@skillname
class PeopleMoon(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.counter_name = 'Eientei_Random'
        #Modified by Mountain Vaporous Red Eyes. Reisen only.
@skillname
class RoyalPeopleMoon(CounterSkill):
    def __init__(self, owner):
        CounterSkill.__init__(self, owner)
        self.counter_name = 'Eientei_Random'

#-----------------------
# Kinship
#-----------------------
@skillname
class GoingAlone(StatSkill):
    def __init__(self, owner):
        StatSkill.__init__(self, owner)
    def Apply(self, user, spell, target, attacking=True):
        self._boost_stat('ALL', user, 16, 1)
    def IsActive(self, user, attacking=True):
        #Always call super - this is to get the is_self stuff.
        s = Skill.IsActive(self, user, attacking)
        if s is False:
            return False
        #What this needs to do is check the frontline to see if anyone is part of team 9.
        #If there's more than 1 member (and, I think, the user knows Team 9), return false.
        return False
#

#Figure out kinship skills.
#Fight Starter - technically kinship, I guess.

#Super Youkai Buster buffs Youkai Buster. 8% instead of 10%.

#Generators for extremely similar skills.
#------
ele_off_lookup = {
    'FIR' : 'Blazing',
    'CLD' : 'AbilityManipulateWater',
    #'WND' : None,
    'NTR' : 'NativeGodEarth',
    'MYS' : 'MagicTraining',
    'SPI' : 'PowerLivingGod',
    'DRK' : 'FlamesJealousy',
    'PHY' : 'RuinousSuperStrength',
}
ele_def_lookup = {
    'FIR' : 'RobeFireRat',
    'CLD' : 'AbilityManipulateIce',
    'WND' : 'AbilityManipulateWind',
    #'NTR' : None,
    'MYS' : 'WavelengthInsanity',
    'SPI' : 'ArmoredYinYangOrb',
    'DRK' : 'RealmEternalDarkness',
    'PHY' : 'FreeWorldlyThoughts',
}
type_off_lookup = {
    'HUM' : 'YoukaiKnowledge',
    'YOU' : 'YoukaiBuster',
    'GST' : 'NetherworldDweller',
    'PNT' : 'SymbolHarvest', 
    'BST' : 'AbilityGuideAnimals',
    'FLY' : 'TenguWatchfulEye',
    'INS' : 'InsectCommander', 
    'AQA' : 'KappaEcologyObservation', 
    'INO' : 'ManipulationDolls', 
    #'ONI' : None,
    #'DRG' : None,
    'DVN' : 'BishamontenBlessing', 
    'OTH' : 'WeirdCreaturesKnowledge', 
}
#https://stackoverflow.com/questions/15247075
#Dynamically create some very-similar skills.
class ElementBoost(DamageBoost):
    def __init__(self, owner):
        DamageBoost.__init__(self, owner)
        self.self_only = False
        self.element = None
    def IsApplicable(self, spell, target):
        #Check element. Reminder; spell can be multi element.
        if self.element in spell['Element']:
            return True
        return False
    def Apply(self, user, spell, target, attacking=True):
        self._spell_mult(spell, 15 * self.level)
class TypeBoost(DamageBoost):
    def __init__(self, owner):
        DamageBoost.__init__(self, owner)
        self.self_only = False
        self.typ = None
    def IsApplicable(self, spell, target):
        #Check target type.
        #No - this needs to be in IsActive
        #Otherwise a level2 Anti-HUM will prevent a level1 Anti-INS against a non-human insect.
        #Which means I need to change Active. Sigh. Or rework this type system
        #Both are bad.
        return False
    def Apply(self, user, spell, target, attacking=True):
        self._spell_mult(spell, 10 * self.level)
    def UniqueKey(self):
        #Only one of these skills can be active at a time.
        return 'TypeBoost'
#class ElementDefense(Skill):
#
def element_boost_factory(element):
    def __init__(self, owner):
        ElementBoost.__init__(self, owner)
        self.element = element
    newclass = type(ele_off_lookup[element], (ElementBoost,),{"__init__": __init__})
    return newclass
def type_boost_factory(typ):
    def __init__(self, owner):
        TypeBoost.__init__(self, owner)
        self.typ = typ
    newclass = type(type_off_lookup[typ], (TypeBoost,),{"__init__": __init__})
    return newclass
for element in ele_off_lookup:
    off_skill = element_boost_factory(element)
    skill_list[off_skill.__name__] = off_skill
    #Also do the defense skills. Later.
for t in type_off_lookup:
    sk = type_boost_factory(t)
    skill_list[sk.__name__] = sk
#------
#Skills that are implemented in other skills. Classes exist just to hide the "Not implemented" message

@skillname
class LastFortressPlus(Noop):
    pass
@skillname
class AdversityPlus(Noop):
    pass
@skillname
class JealousyFueledFinalBlow(Noop):
    pass
@skillname
class ChineseGirlSuperQigong(Noop):
    pass
@skillname
class EnhancedVersatileMachine(Noop):
    pass
#Not implemented, but should be.
#@skillname
#class SuperYoukaiBuster(Noop):
#    pass
#Deaf to All but the Song
@skillname
class MoraleMaintenance(Noop):
    #Modifies fighting spirit, but not in a useful way.
    pass

#------

#print(skill_list)
