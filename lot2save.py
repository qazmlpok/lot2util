from lot2helper import *
import lot2data
from lot2character import Character
from lot2misc import MiscData

import os
import copy
import math
import re
import io
from operator import xor
from itertools import cycle

class StandaloneData:
    """ Manager for dealing with the Standalone (dlsite) version's save data
    Does nothing special; just opens the file by name.
    """
    def __init__(self, basepath):
        self._folder = basepath
    def GetFile(self, filename):
        """ Just opens the file and returns the stream. It is expected the caller will close it. """
        fullpath = os.path.join(self._folder, filename)
        f = open(fullpath, 'rb')
        return f
    def WriteData(self, filename, func):
        """ Opens the specified file in append mode and writes data. """
        fullpath = os.path.join(self._folder, filename)
        #Make sure it already exists
        if (not os.path.exists(fullpath)):
            raise Exception("Path doesn't already exist: " + fullpath)
        #
        with open(fullpath, 'r+b') as fh:
            #Call c.saveCharacter (or whatever) on the file handle.
            func(fh)
            #And then that's it.
    def Finish(self):
        #Only needed for Steam
        pass
#
class SteamData:
    """ Manager for dealing with the Steam save data.
    Everything is combined into a single file. It is also encrypted.
    This class enables treating the steam data in the same way as the original standalone data,
    by requesting a file with the original name, it will create a temporary stream that emulates the original file.
    """
    #See Thurler's converter for converting data. 
    #https://github.com/Thurler/thlaby2-save-convert/blob/main/convert_save.py
    def __init__(self, basepath):
        with open(basepath, 'rb') as f:
            raw_data = f.read()
            #Files are always the same size, regardless of where they are in-game.
            assert len(raw_data) == 257678
            self._decoded_data = bytes(map(xor, raw_data, cycle(xorkey)))
        self.basepath = basepath
        self.filename_re = re.compile(r'^([a-zA-Z]+)(\d+)(?:\.ngd)?$')
    def _getSaveName(self, filename):
        m = self.filename_re.match(filename)
        if not m:
            raise Exception(f"Invalid filename: {filename}")
        (letter, number) = m.group(1, 2)
        return (letter, int(number))
    def GetFile(self, filename):
        """ Returns a stream of data sourced from the combined steam save file,
        modified to look/act like a standalone file.
        """
        (letter, number) = self._getSaveName(filename)
        
        #Set in the if chain
        data = None
       
        if letter == 'C':
            #Only time number matters...
            number = number - 1
            data = self.extractCharacter(number)
        elif letter == 'EEF':
            #item discovery flags
            #This is massively more sparse than the original.
            pass
        elif letter == 'EEN':
            #item inventory count
            #Same as EEF
            pass
        elif letter == 'EVF':
            #event flags
            #saveFile[0x54c6:0x68b2]
            pass
        elif letter == 'FOE':
            #FOE respawn timers (not in the converter)
            raise Exception("File not used / supported")
        elif letter == 'PAC':
            #achievement notification status flags
            #saveFile[0x130:0x1d2]
            #(This is split into two sections in the converter, but this isn't necessary)
            pass
        elif letter == 'PAM':
            #achievement status flags
            #saveFile[0x130:0x1d2]
            pass
        elif letter == 'PCF':
            #character unlock flags
            #saveFile[0x5:0x3d] = data[0x1:0x39]
            #i.e. go back 1 character
            pass
        elif letter == 'PEX':
            #misc information
            offset = 0x540c
            #Size is the same, but it needs to be inverted.
            data = list(self._decoded_data[offset:offset+0xBA])
            self._invertPEX(data)
            pass
        elif letter == 'PKO':
            #bestiary information
            #saveFile[0x2c2:0x4c22] = data[0xca:0x4a2a]
            #and then reverse endian
            #Remember to go pad 0xCA to be consistent.
            #I think this could just be copied as well, but why bother
            pass
        elif letter == 'PPC':
            #party formation
            data = self._decoded_data[0x5018:0x5024]
            assert len(data) == 12
            pass
        elif letter == 'SHD':
            #Save summary data; shows on the load screen, but doesn't affect real values.
            raise Exception("File not used / supported")
        else:
            raise Exception(f"Unrecognized filename: {filename}")

        return io.BytesIO(bytes(data))
    
    def WriteData(self, filename, func):
        """ Creates a filehandle-like object pointing to a block of memory representing
        the DLSite-equivalent of a Steam combined save of a specific name.
        This can then be written to as if it was a file...
        it will then be re-converted to the Steam format,
        and written to disk
        """
        with self.GetFile(filename) as fh:
            #Call c.saveCharacter (or whatever) on the file handle.
            func(fh)
            #Now convert the file back to Steam format and write to disk
            fh.seek(0)
            data = list(fh.read())
            self.writeToDisk(filename, data)
    #
    def Finish(self):
        #Do this later; only write the actual file once.
        #I think the writing is currently in writeToDisk?
        pass
    def writeToDisk(self, filename, data):
        """Actually write the data to disk.
        Filename is the standalone equivalent filename, e.g. C01. This is used to get the offset to use
        data is the data to write, in standalone format. Must be a list of binary values (since it will be inverted, etc)
        """
        (letter, number) = self._getSaveName(filename)
        if letter == 'C':
            #Assert len(data)? I should know it, but I'm also ignoring a lot of junk that's normally at the end.
            number = number - 1
            offset = 0x9346 + 0x10F * number

            #Now remove the 2 padding bytes. This is the opposite of extractCharacter.
            data = self.storeCharacter(data)
            dec_data = list(self._decoded_data)
            dec_data[offset:offset+len(data)] = data[:]
            #
            self._decoded_data = bytes(dec_data)
            encoded_data = bytes(map(xor, self._decoded_data, cycle(xorkey)))
            #TODO: This will write the save 56 times, once for each character. Fix that.
            with open(self.basepath, 'wb') as outf:
                outf.write(encoded_data)

        elif letter == 'PEX':
            offset = 0x540c
            #TODO: I bet the inversion could be handled in the template.
            data = self._invertPEX(data)
            #Store into the saved copy; this doesn't go in Finish
            #It's a common operation so it should probably be done somewhere else?
            dec_data = list(self._decoded_data)
            dec_data[offset:offset+len(data)] = data[:]
            #This is what belongs in finish
            self._decoded_data = bytes(dec_data)
            encoded_data = bytes(map(xor, self._decoded_data, cycle(xorkey)))
            with open(self.basepath, 'wb') as outf:
                outf.write(encoded_data)
            
        else:
            raise Exception("Writing not supported.")
    def extractCharacter(self, number):
        """ One way function; pull the data from the combined save file and create a chunk
        that looks like standalone data.
        The spacing is slightly different, so it can only be done in one direction
        There are also a lot of inversions; try to extract those, since that part is bidirectional.
        """
        #Expected Cxx filesize is 373 bytes or 0x175
        #But it looks like nothing after 0x109 is used.
        #0x109 is probably padded up to 0x10f
        #...F? not 0? Really?
        srcData = self._decoded_data
        offset = 0x9346 + 0x10f * number
        data = [0] * 0x175
        #Offsets match for most of the early data, up to the boost2 flags.
        data[0:0xEC] = srcData[offset:offset+0xEC]
        #0xEC maps to xED, then EE maps to F0
        data[0xED:0xEF] = srcData[offset+0xEC:offset+0xEE]
        data[0xF0:0xF4] = srcData[offset+0xEE:offset+0xF2]
        #Everything after this is just shifted by 2
        data[0xF4:0x111] = srcData[offset+0xF2:offset+0x10F]
        
        #Then invert the data. Reminder; when writing, invert first, then shift.
        self._invertCharacter(data)
        return data
    def storeCharacter(self, data):
        """ One way function; turn Character standalone data into combined data
        This is the opposite of extractCharacter
        The output must not include the "offset"; this will be done by the calling function
        (this is to enable a sparse write)
        """
        outData = [0] * 0x10F
        
        #Same operation as reading; this is reversable. Modifies in-place.
        self._invertCharacter(data)

        #Offsets match for most of the early data, up to the boost2 flags.
        outData[0:0xEC] = data[0:0xEC]
        #0xEC maps to xED, then EE maps to F0
        outData[0xEC:0xEE] = data[0xED:0xEF]
        outData[0xEE:0xF2] = data[0xF0:0xF4]
        #Everything after this is just shifted by 2
        outData[0xF2:0x10F] = data[0xF4:0x111]
        return outData
    #
    def _invertCharacter(self, data):
        """ Change the endianness of various values within the character data.
        This needs to be done in both reading/writing, hence it's a separate function.
        Modifies data in-place.
        """
        #4 bytes: level, exp, library levels, subclass
        #2 bytes: skills, subskills
        #Then it inverts some 1 byte blocks, but...
        #Later on (0xF2, I think), 2 bytes for gems
        #0x105:0x109 - BP
        #0x109, 2 bytes: 4 equipment slots
        
        #Alternative, shorter approach: list of tuples of (values, size)
        #and just loop over that until the last few.
        #Probably not worth it.
        
        size = 4
        offset = 0
        data[offset:offset+size] = data[offset:offset+size][::-1]#Level
        offset = 4
        data[offset:offset+8] = data[offset:offset+8][::-1]#Exp
        offset = 12
        #Library bonuses (stats+affin), bonuses (stats), subclass (the +1)
        for i in range(len(lot2data.stats) + len(lot2data.affinities) + len(lot2data.stats) + 1):
            data[offset:offset+size] = data[offset:offset+size][::-1]
            offset += size
        size = 2
        assert offset == 0x60
        for i in range(40 + 20):
            #TODO: That should be in lot2data. It's SKILL_COUNT + SUBCLASS_SKILL_COUNT
            data[offset:offset+size] = data[offset:offset+size][::-1]
            offset += size
        assert offset == 0xD8
        #Skip ahead to equipment.
        offset = 0xEC+1   #Unused skp; but skip the sign
        # --- bonus stock, skp stock are wrong. BP is correct. Odd.
        data[offset:offset+size] = data[offset:offset+size][::-1]# Unused skill points
        offset = 0xF0
        size = 4
        data[offset:offset+size] = data[offset:offset+size][::-1]# Unused level up bonus
        offset = 0xF4
        size = 2
        for i in range(len(lot2data.gem_stats)):
            data[offset:offset+size] = data[offset:offset+size][::-1]
            offset += size
        offset = 0x105
        size = 4
        data[offset:offset+size] = data[offset:offset+size][::-1]# BP Count
        size = 2
        offset = 0x109
        for i in range(4):
            #Equipment
            data[offset:offset+size] = data[offset:offset+size][::-1]
            offset += size
    #

    def _invertPEX(self, data):
        """ Applies byte data inversions as described in Thurler's converter 
        Basically entirely copied/adapted from there.
        Should be applied to the extracted bin data to ensure the offsets matchup.
        """

        #This was just copied from Thurler's converter; I haven't made any attempt to combine
        #expressions into loops.
        data[0x00:0x08] = data[0x00:0x08][::-1] # Cumulative EXP
        data[0x08:0x10] = data[0x08:0x10][::-1] # Cumulative Money
        data[0x10:0x18] = data[0x10:0x18][::-1] # Current money
        data[0x18:0x20] = data[0x18:0x20][::-1] # Number of battles
        data[0x20:0x24] = data[0x20:0x24][::-1] # Number of game overs
        data[0x24:0x28] = data[0x24:0x28][::-1] # Play time in seconds
        data[0x28:0x2c] = data[0x28:0x2c][::-1] # Number of treasures
        data[0x2c:0x30] = data[0x2c:0x30][::-1] # Number of crafts
        data[0x30:0x34] = data[0x30:0x34][::-1] # Unused data
        data[0x34] = data[0x34] # Highest floor
        data[0x35:0x39] = data[0x35:0x39][::-1] # Number of locked treasures
        data[0x39:0x3d] = data[0x39:0x3d][::-1] # Number of escaped battles
        data[0x3d:0x41] = data[0x3d:0x41][::-1] # Number of dungeon enters
        data[0x41:0x45] = data[0x41:0x45][::-1] # Number of item drops
        data[0x45:0x49] = data[0x45:0x49][::-1] # Number of FOEs killed
        data[0x49:0x51] = data[0x49:0x51][::-1] # Number of steps taken
        data[0x51:0x59] = data[0x51:0x59][::-1] # Money spent on shop
        data[0x59:0x61] = data[0x59:0x61][::-1] # Money sold on shop
        data[0x61:0x69] = data[0x61:0x69][::-1] # Most EXP from 1 dive
        data[0x69:0x71] = data[0x69:0x71][::-1] # Most Money from 1 dive
        data[0x71:0x75] = data[0x71:0x75][::-1] # Most Drops from 1 dive
        data[0x75] = data[0x75] # Unknown data
        data[0x76:0x7e] = data[0x76:0x7e][::-1] # Number of library enhances
        data[0x7e:0x82] = data[0x7e:0x82][::-1] # Highest battle streak
        data[0x82:0x86] = data[0x82:0x86][::-1] # Highest escape streak
        data[0x86] = data[0x86] # Hard mode flag
        data[0x87] = data[0x87] # IC enabled flag
        data[0x88:0xae] = data[0x88:0xae] # Unknown data
        data[0xae:0xb2] = data[0xae:0xb2][::-1] # IC floor
        data[0xb2:0xb6] = data[0xb2:0xb6][::-1] # Number of akyuu trades
        data[0xb6:0xba] = data[0xb6:0xba][::-1] # Unknown data
        return data
    def reverse_endianness_block2(self, block):
        #Entirely copied from Thurler's converter.
        even = block[::2]
        odd = block[1::2]
        res = []
        for e, o in zip(even, odd):
            res += [o, e]
        return res

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
    
    #For steam, see https://github.com/Thurler/thlaby2-save-convert/blob/main/convert_save.py
    #for Thurler's work on getting the offsets.
    
    #Note on characters
    #There are three lists: original_characters, all_characters, characters
    #original_characters should never be modified and is a deep copy. It allows resetting without re-reading the files.
    #all_characters is every character. The contents can be modified but the list itself shouldn't.
    #characters is initially a copy of all_characters, but is intended to be modified. The sort functions will change the order and filtering can be done.
    
    def __init__(self, basepath):
        """Creates the Save wrapped object. The path needs to be one of the SaveX folders, i.e. all the *.ngd files must exist here"""
        self._folder = basepath
        self.all_characters = [None] * (len(character_ids))
        
        if os.path.isdir(basepath):
            print("Using DLSite save format.")
            self.manager = StandaloneData(basepath)
        elif os.path.isfile(basepath):
            print("Using Steam save format.")
            self.manager = SteamData(basepath)
        else:
            raise Exception(f"{basepath} doesn't exist.")
        for i in character_ids:
            ngdfilename = 'C%02d.ngd' % i

            with self.manager.GetFile(ngdfilename) as f:
                self.all_characters[i-1] = Character(i, f)

        #Add to dict
        #self.characters[self.all_characters[i-1].name] = self.all_characters[i-1]
        #TODO: Extend this to support short name and full name.
        #Actually, use a function so I can use case-insensitive.
        #
        self.original_characters = copy.deepcopy(self.all_characters)
        self.characters = copy.copy(self.all_characters)
        
        with self.manager.GetFile('PPC01.ngd') as f:
            self.party = self.load_current_party(f)
        #Should also do items.
        
        with self.manager.GetFile('PEX01.ngd') as f:
            self.misc_data = MiscData(f)
            self.misc_data.print_all()
            #There's currently no other way to interact with this file.
    #
    def write_characters(self):
        #TODO: Add an optional parameter for a filter (using get_characters semantics)
        #Largely unnecessary since it uses characters, but it'd still be nice.
        
        ret = []
        for c in self.characters:
            ngdfile = 'C%02d.ngd' % c.id
            self.manager.WriteData(ngdfile, c.save_to_file)
            ret.append("Wrote save data for " + c.name + " to path: " + ngdfile)
        return ret
    #
    def write_misc(self):
        #Probably need a better way to call this.
        
        self.manager.WriteData('PEX01.ngd', self.misc_data.save_to_file)
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
