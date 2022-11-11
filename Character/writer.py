from lot2helper import *

import os
import copy
import math

def save_to_file(self, fh):
    """Writes character data to a file. Save hacking. Basically the opposite of the constructor."""
    #Assumes that the file already exists. If something isn't supported (e.g. items), it won't be modified
    #and relies on the old data already being there.
    
    #Sanity.
    fh.seek(0)
    
    writebytes(fh, self.level, 4)
    writebytes(fh, self.exp, 8)
    
    for stat in stats:
        #6 total
        writebytes(fh, self.libstats[stat], 4)
    for aff in affinities:
        #8 total
        writebytes(fh, self.libstats[aff], 4)
    for stat in stats:
        #6 total
        writebytes(fh, self.levelstats[stat], 4)
    assert fh.tell() == 0x5C
    #Subclass, skills
    #I don't want to worry about these. Skip ahead a bit.
    fh.seek(0xD8)
    #Boosts. Still don't wanna deal with it.
    #Note - these are combined into one internal variable. First block should be 'unlocked > 0 ? 1 : 0'
    #Second should be 'unlocked > 1 ? 0 : unlocked'   -- I _think_
    #Actually I think I was stomping the first variable, oops. Gotta fix that too... Right now it's JUST boost_2/3
    #for stat in boost_stats:
    #    unlocked = self.boosts[stat]
    #    assert unlocked in (0,1)
    #    writebytes(fh, unlocked, 1)
    #for stat in boost_2_stats:
    #    unlocked = self.boosts[stat]
    #    assert unlocked in (0,2,3)
    #    writebytes(fh, unlocked, 1)
    #assert fh.tell() == 0xEC
    fh.seek(0xEC)
    #writebytes(fh, self.unused_skill_points, 3)
    #unknown single byte
    fh.seek(0xF0)
    writebytes(fh, self.unused_bonus_points, 4)    #This one I do modify.
    for stat in gem_stats:
        assert self.gems[stat] <= 20
        writebytes(fh, self.gems[stat], 2)
    assert fh.tell() == 0x104
    #writebytes(fh, self.training_manuals, 1)   #Don't modify
    #1 unknown byte
    fh.seek(0x106)
    writebytes(fh, self.BP, 3)        #Dunno if this is really 3 bytes
    
    #Everything left over is equipment.
#
