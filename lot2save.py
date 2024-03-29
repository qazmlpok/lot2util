from lot2helper import *
import lot2data
from lot2character import Character
from lot2events import EventData
from lot2misc import MiscData
from lot2items import Items
from lot2formation import CharacterList, Formation, ExtremelyFakeFormation

import os
import copy
import math
import re
import io
from operator import xor
from itertools import cycle

class FileHandleWrapper():
    def __init__(self, fh, endian):
        """Create a wrapper around a file-like object. This will either be an actual filehandle
        or a BytesIO object for a block of data within the Steam combined file.
        This is used to pass in default endian information to the templates.
        I believe everything uses the same endianness, so there isn't actually any need to specify it in the template.
        """
        self.fh = fh
        self.endianness = endian
        #Copy methods to act as a wrapper.
        self.read = self.fh.read
        self.write = self.fh.write
        self.tell = self.fh.tell
        self.seek = self.fh.seek

    def readbytes(self, bytecount, endianness=None):
        if endianness is None:
            endianness = self.endianness
        position = self.tell()
        bytes = self.read(bytecount)
        if len(bytes) < bytecount:
            raise Exception("Couldn't read file. Starting position " + str(position))
        return converttoint(bytes, bytecount, endian=endianness)
    #
    def writebytes(self, value, bytecount, endianness=None):
        if endianness is None:
            endianness = self.endianness
        position = self.tell()
        bytes = convertfromint(value, bytecount, endian=endianness)
        written = self.write(bytes)
        if written < bytecount:
            raise Exception("Couldn't write to file. Starting position " + str(position))
        return
    #
    def __enter__ (self):
        return self
    def __exit__ (self, exc_type, exc_value, traceback):
        self.fh.close()

class StandaloneData:
    """ Manager for dealing with the Standalone (dlsite) version's save data
    Does nothing special; just opens the file by name.
    """
    def __init__(self, basepath):
        self._folder = basepath
    def GetFile(self, filename, writable=False):
        """ Just opens the file and returns the stream. It is expected the caller will close it. """
        fullpath = os.path.join(self._folder, filename)
        mode = 'r+b' if writable else 'rb'
        f = open(fullpath, mode)
        return FileHandleWrapper(f, BIG_ENDIAN)
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
    
    class SteamFileWrapper(FileHandleWrapper):
        def __init__(self, SteamObj, offset, size):
            """ Create a wrapper around the Steam decrypted data. Functions a lot like FileHandleWrapper
            except I couldn't get that to (sensibly) write back to the source.
            This approach is still not really ideal and has a lot of potential concurrency issues
            Basically, just don't open a single file _twice_ and it should be good.
            """
            self.SteamObj = SteamObj
            self.offset = offset
            data = SteamObj._decoded_data[offset:offset+size]
            fh = io.BytesIO(bytes(data))
            super().__init__(fh, LITTLE_ENDIAN)
        def __enter__ (self):
            return self
        def __exit__ (self, exc_type, exc_value, traceback):
            #Read in all the data. Then write back to the original.
            #Can I have it just write directly to the srcData? I can potentially have multiple "filehandles"
            #open at once, with different read positions. Is that safe?
            self.fh.seek(0)
            newdata = list(self.fh.read())
            self.SteamObj.WriteToData(newdata, self.offset)
            self.fh.close()
    #
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
    def GetFile(self, filename, writable=False):
        """ Returns a stream of data sourced from the combined steam save file,
        modified to look/act like a standalone file.
        """
        #Set in the if chain
        data = None

        (letter, number) = self._getSaveName(filename)
        if letter == 'C':
            #Only time number matters...
            #Expected Cxx filesize is 373 bytes or 0x175
            #But it looks like nothing after 0x109 is used.
            #0x109 is probably padded up to 0x10f
            offset = 0x9346 + 0x10f * (number-1)
            data = self._decoded_data[offset:offset+0x10F]
        elif letter == 'EEF':
            #item discovery flags
            offset = 0x7bd6
            data = self._decoded_data[offset:offset+0x7CF]
        elif letter == 'EEN':
            #item inventory count
            offset = 0x83a6
            data = self._decoded_data[offset:offset+(0x7CF*2)]
        elif letter == 'EVF':
            #event flags
            offset = 0x54c6
            data = self._decoded_data[offset:offset+(0x13EC)]
            #File should be 10,000 bytes but maybe the rest just isn't used.
            #The last non-zero byte I have in my save1 is at 0x13EB
            #saveFile[0x54c6:0x68b2]
        elif letter == 'FOE':
            #FOE respawn timers (not in the converter)
            raise Exception("File not used / supported")
        elif letter == 'PAC':
            #achievement notification status flags
            #saveFile[0x130:0x1d2]
            #(This is split into two sections in the converter, but this isn't necessary)
            raise Exception("File not supported")
        elif letter == 'PAM':
            #achievement status flags
            #saveFile[0x130:0x1d2]
            raise Exception("File not supported")
        elif letter == 'PCF':
            #character unlock flags
            #saveFile[0x5:0x3d] = data[0x1:0x39]
            #i.e. go back 1 character
            raise Exception("File not supported")
        elif letter == 'PEX':
            #misc information
            offset = 0x540c
            data = self._decoded_data[offset:offset+0xBA]
        elif letter == 'PKO':
            #bestiary information
            #saveFile[0x2c2:0x4c22] = data[0xca:0x4a2a]
            #and then reverse endian
            #Remember to go pad 0xCA to be consistent.
            #I think this could just be copied as well, but why bother
            raise Exception("File not supported")
        elif letter == 'PPC':
            #party formation
            offset = 0x5018
            data = self._decoded_data[0x5018:0x5024]
            assert len(data) == 12
        elif letter == 'SHD':
            #Save summary data; shows on the load screen, but doesn't affect real values.
            raise Exception("File not used / supported")
        else:
            raise Exception(f"Unrecognized filename: {filename}")

        #Writable is currently ignored; the wrapped fh is always writable.
        return SteamData.SteamFileWrapper(self, offset, len(data))
    def WriteToData(self, newdata, offset):
        """I didn't want to do this but I can't find any alternative.
        Write data at a certain position to the locally stored decrypted copy of the data.
        Needs to be a function because bytes objects don't support modification.
        It needs to create a new bytes object, meaning it needs to be internal.
        """
        #Lists support assignment; bytes doesn't. Convert back to a bytes obj by creating a new one.
        dec_data = list(self._decoded_data)
        dec_data[offset:offset+len(newdata)] = newdata[:]
        self._decoded_data = bytes(dec_data)
    def Finish(self):
        encoded_data = bytes(map(xor, self._decoded_data, cycle(xorkey)))
        with open(self.basepath, 'wb') as outf:
            outf.write(encoded_data)
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
        
        #Initialize; for the case of no save data
        self.party = None
        self.misc_data = None
        self.items = None
        self.events = None
        
        if basepath is None or basepath == '':
            #If no path provided, can still "load" character data. This should be initialized
            #to roughly match a newly created save file.
            #There's no point in trying to do this with other files.
            characters = [None] * (len(character_ids))
            for i in character_ids:
                characters[i-1] = Character(i)
            self.characters = CharacterList(characters)
            self.party = ExtremelyFakeFormation(characters)
            self.fake_party = self.party
        else:
            #will set self.characters.
            self._load_files(basepath)
            self.fake_party = ExtremelyFakeFormation(self.characters.all_characters)
        #
        
    #
    def _load_files(self, basepath):
        """ Separate function to actually load in character/etc data from the provided file.
        """
        characters = [None] * (len(character_ids))
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
                characters[i-1] = Character(i, f)
        self.characters = CharacterList(characters)
        #
        with self.manager.GetFile('PPC01.ngd') as f:
            self.party = self.load_current_party(f)
        #Should also do items.
        
        with self.manager.GetFile('PEX01.ngd') as f:
            self.misc_data = MiscData(f)
            self.misc_data.print_all()
            #There's currently no other way to interact with this file.
        
        with self.manager.GetFile('EEF01.ngd') as disc_fh:
            with self.manager.GetFile('EEN01.ngd') as item_fh:
                self.items = Items(disc_fh, item_fh)
        
        with self.manager.GetFile('EVF01.ngd') as f:
            #with open('EVF-extract.FILE', 'wb') as outfile:
            #    outfile.write(f.read())
            #print("Wrote to 'EVF-extract.FILE'")
            self.events = EventData(f)
            #self.events.print_all()
    #
    def write_characters(self):
        #TODO: Add an optional parameter for a filter (using get_characters semantics)
        #Largely unnecessary since it uses characters, but it'd still be nice.
        
        ret = []
        for c in self.characters:
            ngdfile = 'C%02d.ngd' % c.id
            with self.manager.GetFile(ngdfile, True) as fh:
                c.save_to_file(fh)
            ret.append("Wrote save data for " + c.name + " to path: " + ngdfile)
        self.manager.Finish()
        return ret
    #
    def write_misc(self):
        #Probably need a better way to call this.
        with self.manager.GetFile('PEX01.ngd', True) as fh:
            self.misc_data.save_to_file(fh)
        self.manager.Finish()
    def write_items(self):
        #Probably need a better way to call this.
        #Yeah I can't do this with 2 files.
        with self.manager.GetFile('EEF01.ngd', True) as disc_fh:
            with self.manager.GetFile('EEN01.ngd', True) as item_fh:
                self.items.save_to_file(disc_fh, item_fh)
        self.manager.Finish()
    def reset(self):
        """Undoes all changes. Reverts back to the original data read in from the save files"""
        #TODO: This should undo other files too, I guess. Except the modification really was only for characters...
        self.characters.reset()
    #
    def load_current_party(self, filedata):
        """Gets the current party, from PPC01.ngd. Returns a list of ids.
        This is just 12 bytes, one for each character, laid out:
        9ABC
        5678
        1234"""
        
        data = filedata.read(12)
        return Formation(list(data), self.characters)
    #
    def get_character(self, name):
        return self.characters.get_character(name)
    #
    def get_characters(self, names):
        #This should be *args
        return self.characters.get_characters(names)
    #
#
