from lot2helper import *

class MiscData:
    """Represents data loaded from file PEX01 in the save folder. 
    Tracks various misc fields, e.g. total exp, total money, current money, steps walked, etc.
    """
    def __init__(self, filedata):
        self.total_exp = readbytes(filedata, 8)         # Cumulative EXP
        self.total_money = readbytes(filedata, 8)       # Cumulative Money
        self.curr_money = readbytes(filedata, 8)        # Current money
        self.total_battles = readbytes(filedata, 8)     # Number of battles
        self.gameovers = readbytes(filedata, 4)         # Number of game overs
        self.playtime = readbytes(filedata, 4)          # Play time in seconds
        self.total_treas = readbytes(filedata, 4)       # Number of treasures
        self.total_craft = readbytes(filedata, 4)       # Number of crafts
        readbytes(filedata, 4)   # Unused data           
        self.highest_floor = readbytes(filedata, 1)     # Highest floor
        self.locked_treas = readbytes(filedata, 4)      # Number of locked treasures
        self.escape_count = readbytes(filedata, 4)      # Number of escaped battles
        self.dung_count = readbytes(filedata, 4)        # Number of dungeon enters
        self.item_drops = readbytes(filedata, 4)        # Number of item drops
        self.foe_count = readbytes(filedata, 4)         # Number of FOEs killed
        self.step_count = readbytes(filedata, 8)        # Number of steps taken
        self.shop_money = readbytes(filedata, 8)        # Money spent on shop
        self.sold_money = readbytes(filedata, 8)        # Money sold on shop
        self.most_exp = readbytes(filedata, 8)          # Most EXP from 1 dive
        self.most_money = readbytes(filedata, 8)        # Most Money from 1 dive
        self.most_drops = readbytes(filedata, 4)        # Most Drops from 1 dive
        readbytes(filedata, 1)  # Unknown data           
        self.lib_enhance = readbytes(filedata, 8)       # Number of library enhances
        self.most_battle = readbytes(filedata, 4)       # Highest battle streak
        self.most_escape = readbytes(filedata, 4)       # Highest escape streak
        self.hardmode = readbytes(filedata, 1)          # Hard mode flag
        self.ic_avail = readbytes(filedata, 1)          # IC enabled flag
        readbytes(filedata, 0x26)# Unknown data           
        self.ic_floor = readbytes(filedata, 4)          # IC floor
        self.akyuu_trades = readbytes(filedata, 4)      # Number of akyuu trades
        #readbytes(filedata, ...)# Unknown data
    
    def print_all(self):
        print(f'Cumulative EXP: {self.total_exp}')
        print(f'Cumulative Money: {self.total_money}')
        print(f'Current money: {self.curr_money}')
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