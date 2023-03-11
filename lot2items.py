from DataTemplate import *
from lot2helper import *
import re

#EEF01
class ItemsDiscoveryTemplate(DataTemplate):
    def __init__(self):
        self.fields = [
            ArrayField('itemDiscovery', range(0, 0x7CF), 1)
        ]
#EEN01
class ItemsTemplate(DataTemplate):
    def __init__(self):
        self.fields = [
            ArrayField('itemCounts', range(0, 0x7CF), 2)
        ]

class Items():
    """ Deals with files EEF01 (Item Discovery flags) and EEN01 (Item Count)
    EEF is boolean data; it's always 0 or 1. There's little reason to do anything here
    but if granting yourself an item, the appropriate discovery flag needs to be set as well.
    EEN is the count of items in inventory. Anything equipped is not counted. Anything not
    discovered will be 0, but make sure to also set the EEF flag.
    """
    discTemplate = ItemsDiscoveryTemplate()
    itemsTemplate = ItemsTemplate()
    item_stats = loadItemData()
    
    def __init__(self, disc_fh, items_fh):
        Items.discTemplate.Read(self, disc_fh)
        Items.itemsTemplate.Read(self, items_fh)
        
        #Reminder; there are huge gaps in item ids. Last main equip is 60. First sub is 201.
        #Item 0 exists, including in the files, but should always have a count of 0.
        self.items = {}
        self.item_ids = []
        for id in Items.item_stats:
            item = Items.item_stats[id]
            
            item['Count'] = self.itemCounts[id]
            if self.itemDiscovery[id] == 0:
                item['Count'] = None
            #Track by both name and id. Names never look like ids so this is save.
            self.items[id] = item
            self.items[self._normalize(item['Name'])] = item
            self.item_ids.append(id)
        #Is None fine? Should I use a fake object?
        self.items[0] = None
        self.items[self._normalize('None')] = None
        for i in self.item_ids:
            item = self.items[i]
            #print(f"{i}: {item['Name']}, {item['Count']}")
    def save_to_file(self, disc_fh, items_fh):
        for id in Items.item_stats:
            item = Items.item_stats[id]
            if item['Count'] is not None:
                self.itemDiscovery[id] = 1
                #Need to copy over any changes to the source array.
                self.itemCounts[id] = item['Count']
            #There's probably no reason to un-discover an item...
        Items.discTemplate.Write(self, disc_fh)
        Items.itemsTemplate.Write(self, items_fh)
    
    def get(self, name):
        name = self._normalize(name)
        if name in self.items:
            return self.items[name]
        raise Exception(f"Invalid item: {name}")
        
    def Query(self, query, errorOnEmpty=False):
        return ItemCollection(self.items, self.item_ids, query, errorOnEmpty)
        
    @staticmethod
    def _normalize(name):
        if isinstance(name, int):
            return name
        #Maybe also remove commas, apostrophes, etc?
        return name.lower()
#

class ItemCollection():
    """ Collection of items.
    Querying the full list of items can be used to create a collection,
    then the item counts for every matching item can be adjusted at once.
    Querying uses a regex instead of glob simply because it's easier to code.
    Note - this will not use normalization. Search on the exact name.
    """
    
    def __init__(self, items, item_ids, query, errorOnEmpty=False):
        self.items = items
        self.item_ids = item_ids
        self.selection = set()
        self.Add(query, errorOnEmpty)
    
    def Add(self, query, errorOnEmpty=False):
        """ Add all items matching query to this collection.
        Duplicates will be removed.
        """
        if (isinstance(query, str)):
            query = re.compile(query)
        resp = self._doQuery(query)
        if errorOnEmpty and len(resp) == 0:
            raise Exception("Query produced no results.")
        self.selection |= resp
    def Sub(self, query):
        """ Remove all items matching query from this collection.
        """
        if (isinstance(query, str)):
            query = re.compile(query)
        resp = self._doQuery(query)
        self.selection -= resp
    def SetCount(self, val):
        """ Modify the count of every item in this collection.
        """
        l = list(self.selection)
        for item in l:
            item['Count'] = val
    def SetCountIfBelow(self, val):
        """ Modify the count of every item in this collection, but only if it is already below the
        given value. (i.e. only add items, never remove them)
        """
        l = list(self.selection)
        for item in l:
            if item['Count'] is None or item['Count'] < val:
                item['Count'] = val
    def Contents(self):
        #Can't iterate a set. Bleh.
        l = list(self.selection)
        return l
        #return [x['Name'] for x in l]
    def _doQuery(self, query):
        resp = set()
        for i in self.item_ids:
            item = self.items[i]
            if (query.search(item['Name'])):
                resp.add(item)
        return resp
    