from DataTemplate import *
from lot2helper import *

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
            #There's probably no reason to un-discover an item...
        #TODO: Get changes from self.items
        #ItemDiscovery flag needs to be set if Count is anything other than None.
        Items.discTemplate.Write(self, disc_fh)
        Items.itemsTemplate.Write(self, items_fh)
    
    def get(self, name):
        name = self._normalize(name)
        if name in self.items:
            return self.items[name]
        raise Exception(f"Invalid item: {name}")
    
    @staticmethod
    def _normalize(name):
        if isinstance(name, int):
            return name
        #Maybe also remove commas, apostrophes, etc?
        return name.lower()
#