import math
import copy

#Can also be used as a standalone program, for converting speed values.
#See bottom of module.

class Speed:
    """An attempt to handle the different values of speed;
    there's the in-game displayed value and the underlying "gain per tick" value.
    Has a constructor that will create a value from either, 
    and some functions for handling division."""
    def __init__(self, *, from_real_speed=None, from_game_speed=None):
        self._speed = 0
        self.SetValue(from_real_speed=from_real_speed, from_game_speed=from_game_speed)
    
    def SetValue(self, *, from_real_speed=None, from_game_speed=None):
        """Convert a speed value into a speed object. As both are just numbers, the only way to
        differentiate between them is to just one of the two mutually-exclusive parameters"""
        if from_real_speed is None and from_game_speed is None:
            raise Exception("One of from_real_speed or from_game_speed must be provided.")
        if from_real_speed is not None and from_game_speed is not None:
            raise Exception("Exactly one of from_real_speed or from_game_speed must be provided, not both.")
        #Internally the speed value is stored as the in-game display.
        #This is to avoid potential rounding issues (200=201 in practice, but "new Speed(201).Value" should return 201.
        if from_real_speed is not None:
            self._speed = self.db_to_game(from_real_speed)
        else:
            self._speed = from_game_speed
    #
    def __rtruediv__(self, other):
        #Decimal division is not meaningful.
        if not isinstance(other, (int, float)):
            return NotImplemented
        return math.ceil(other / self.GetRealValue())
    def __rfloordiv__(self, other):
        #This is actually ceil, not floor. But whatever. The alternative is throw an exception.
        return self.__truediv__(other)
    #
    def __rmul__(self, other):
        #Multiplication works using the in-game value. So doubling your speed doesn't double your tickrate.
        return Speed(from_game_speed=(self._speed * other))
    #
    def __mul__(self, other):
        #Multiplication works using the in-game value. So doubling your speed doesn't double your tickrate.
        return Speed(from_game_speed=(self._speed * other))
    #
    def __imul__(self, other):
        #Multiplication with assignment
        self._speed *= other
        return self
    #
    def __ifloordiv__(self, other):
        #Division with assignment is not meaningful
        return NotImplemented
    #
    #I don't think add/sub is worth implementing. Multiplication at least corresponds to buffs.
    #Comparisons: These all use db-time. 200 speed and 201 speed are the same.
    def __eq__(self, other):
        return Speed.game_to_db(self._speed) == Speed.game_to_db(other._speed)
    def __lt__(self, other):
        return Speed.game_to_db(self._speed) <  Speed.game_to_db(other._speed)
    def __le__(self, other):
        return Speed.game_to_db(self._speed) <= Speed.game_to_db(other._speed)
    def __gt__(self, other):
        return Speed.game_to_db(self._speed) >  Speed.game_to_db(other._speed)
    def __ge__(self, other):
        return Speed.game_to_db(self._speed) >= Speed.game_to_db(other._speed)
    #
    def GetGameValue(self):
        """Gets the speed value, as displayed in-game"""
        return self._speed
    def GetRealValue(self):
        """Gets the speed value, as used internally (i.e. gauge-per-tick)"""
        return Speed.game_to_db(self._speed)
    #
    def __str__(self):
        """Just for debugging. Not useful otherwise."""
        return f"Game: {self.GetGameValue()}, Real: {self.GetRealValue()}"

    #0-200: No conversion
    #200-300 maps to 200-400. Each db point is 2 game points
    #300-400 maps to 400-700. Each db point is 3 game points
    #400-500 maps to 700-1100. Each db point is 4 game points. Etc.
    @staticmethod
    def game_to_db(value):
        if value <= 200:
            return value
        ret = 200
        value -= 200
        step = 2
        while (value > 0):
            if (value > 100*step):
                ret += 100
                value -= 100*step
                step += 1
            else:
                ret += int(value / step)
                value = 0
        return ret
    #
    @staticmethod
    def db_to_game(value):
        if value <= 200:
            return value
        ret = 200
        value -= 200
        step = 2
        while (value > 0):
            if (value > 100):
                ret += step * 100
                value -= 100
                step += 1
            else:
                ret += step * value
                value = 0
        return ret
    #
#

def tests():
    print("Running some simple tests...")
    #Do some simple tests
    assert Speed.game_to_db(200) == 200
    assert Speed.db_to_game(200) == 200
    assert Speed.game_to_db(100) == 100
    assert Speed.db_to_game(100) == 100
    
    assert Speed.game_to_db(400) == 300
    assert Speed.db_to_game(300) == 400
    
    #Test those fancy operators...
    spd = Speed(from_game_speed=200)
    spd *= 2
    assert spd.GetGameValue() == 400
    assert (spd*2).GetGameValue() == 800
    assert (spd*2).GetGameValue() == 800    #Repeat - this shouldn't modify spd
    assert (2*spd).GetGameValue() == 800    #Other direction...
    
    #eq
    assert Speed(from_game_speed=200) == Speed(from_game_speed=201)
    assert Speed(from_game_speed=200) < Speed(from_game_speed=300)
    assert Speed(from_game_speed=200) <= Speed(from_game_speed=300)
    assert Speed(from_game_speed=200) <= Speed(from_game_speed=200)
    assert Speed(from_game_speed=300) > Speed(from_game_speed=200)
    assert Speed(from_game_speed=300) >= Speed(from_game_speed=200)
    assert Speed(from_game_speed=200) >= Speed(from_game_speed=200)
    
    assert 10000 / Speed(from_game_speed=200) == 50
    assert 10000 / spd == 34    #Since this one is 300 real-speed. 33.333, rounds up to 34.
    assert 10000 / Speed(from_real_speed=400) == 25
    
    #Just make sure the "useless" extra bit isn't lost.
    assert Speed(from_game_speed=201).GetGameValue() == 201
    
    #Print mostly just to verify this is actually being called.
    print("10000 / Speed(from_game_speed=400):", 10000 / Speed(from_game_speed=400) )
    print(spd)
#

#This should use a arg-parsing module but whatever.
if __name__ == "__main__":
    import sys
    type=''
    value=''
    if (len(sys.argv) == 1):
        print(f"USAGE: {sys.argv[0]} (Type) (Value)")
        print("Converts input value of Type (either [in-game] 'Speed' or 'Ticks' to the alternate type.")
        print(f"Example: '{sys.argv[0]} speed 1000'")
        print(f"Or:      '{sys.argv[0]} Ticks=300'")
        exit()
    elif (len(sys.argv) == 2):
        text = sys.argv[1].lower()
        if text == 'test' or text == 'tests':
            tests()
            exit()
        elif (text.find('=') >= 0):
            type, value = text.split('=')
        else:
            raise Exception("Couldn't parse input: " + text)
    elif (len(sys.argv) == 3):
        type = sys.argv[1].lower()
        value = sys.argv[2]
    else:
        raise Exception("Too many command line arguments.")
    
    value = int(value)      #Throws...
    if (type[0] == 's'):
        #Speed
        spd = Speed(from_game_speed=value)
        print(f"{value} Speed stat is equal to {spd.GetRealValue()} Ticks.")
    elif (type[0] == 't'):
        #Ticks (any other synonyms?)
        spd = Speed(from_real_speed=value)
        print(f"{value} Ticks is equal to {spd.GetGameValue()} in-game Speed.")
    else:
        raise Exception("Type must be 'Speed' or 'Ticks' (or shorthand)")
    exit()
#
