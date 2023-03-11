from lot2helper import *
from DataTemplate import *

class MiscDataTemplate(DataTemplate):
    def __init__(self):
        self.fields = [
            Field('total_exp', 8)           # Cumulative EXP
            ,Field('total_money', 8)        # Cumulative Money
            ,Field('money', 8)              # Current money
            ,Field('total_battles', 8)      # Number of battles
            ,Field('gameovers', 4)          # Number of game overs
            ,Field('playtime', 4)           # Play time in seconds
            ,Field('total_treas', 4)        # Number of treasures
            ,Field('total_craft', 4)        # Number of crafts
            ,Field('unk_1', 4)              # Unused data
            ,Field('highest_floor', 1)      # Highest floor
            ,Field('locked_treas', 4)       # Number of locked treasures
            ,Field('escape_count', 4)       # Number of escaped battles
            ,Field('dung_count', 4)         # Number of dungeon enters
            ,Field('item_drops', 4)         # Number of item drops
            ,Field('foe_count', 4)          # Number of FOEs killed
            ,Field('step_count', 8)         # Number of steps taken
            ,Field('shop_money', 8)         # Money spent on shop
            ,Field('sold_money', 8)         # Money sold on shop
            ,Field('most_exp', 8)           # Most EXP from 1 dive
            ,Field('most_money', 8)         # Most Money from 1 dive
            ,Field('most_drops', 4)         # Most Drops from 1 dive
            ,Field('unk_2', 1)              # Unknown data
            ,Field('lib_enhance', 8)        # Number of library enhances
            ,Field('most_battle', 4)        # Highest battle streak
            ,Field('most_escape', 4)        # Highest escape streak
            ,Field('hardmode', 1)           # Hard mode flag
            ,Field('ic_avail', 1)           # IC enabled flag
            ,BytesField('unk_bytes', 0x26)  # Unknown data
            ,Field('ic_floor', 4)           # IC floor
            ,Field('akyuu_trades', 4)       # Number of akyuu trades
            ,PositionAssert(0xB6)
        ]

class MiscData:
    """Represents data loaded from file PEX01 in the save folder. 
    Tracks various misc fields, e.g. total exp, total money, current money, steps walked, etc.
    """
    template = MiscDataTemplate()
    def __init__(self, filedata):
        MiscData.template.Read(self, filedata)
    
    def save_to_file(self, fh):
        MiscData.template.Write(self, fh)
    
    def print_all(self):
        print(f'Cumulative EXP: {self.total_exp}')
        print(f'Cumulative Money: {self.total_money}')
        print(f'Current money: {self.money}')
        print(f'Number of battles: {self.total_battles}')
        print(f'Number of game overs: {self.gameovers}')
        print(f'Play time in seconds: {self.playtime}')
        print(f'Number of treasures: {self.total_treas}')
        print(f'Number of crafts: {self.total_craft}')
        print(f'Highest floor: {self.highest_floor}')
        print(f'Number of locked treasures: {self.locked_treas}')
        print(f'Number of escaped battles: {self.escape_count}')
        print(f'Number of dungeon enters: {self.dung_count}')
        print(f'Number of item drops: {self.item_drops}')
        print(f'Number of FOEs killed: {self.foe_count}')
        print(f'Number of steps taken: {self.step_count}')
        print(f'Money spent on shop: {self.shop_money}')
        print(f'Money sold on shop: {self.sold_money}')
        print(f'Most EXP from 1 dive: {self.most_exp}')
        print(f'Most Money from 1 dive: {self.most_money}')
        print(f'Most Drops from 1 dive: {self.most_drops}')
        print(f'Number of library enhances: {self.lib_enhance}')
        print(f'Highest battle streak: {self.most_battle}')
        print(f'Highest escape streak: {self.most_escape}')
        print(f'Hard mode flag: {bool(self.hardmode)}')
        print(f'IC enabled flag: {bool(self.ic_avail)}')
        #IC floor appears to be working but I'm getting odd results for ic_available.
        print(f'IC floor: {self.ic_floor}')
        print(f'Number of akyuu trades: {self.akyuu_trades}')
        print("Something:", self.unk_bytes)
