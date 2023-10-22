from lot2helper import BIG_ENDIAN, LITTLE_ENDIAN
import sys

class DataTemplate():
    """I don't think I need this; I think each file needs its own.
    Is there common behavior?
    """
    def Read(self, dst, fh):
        for f in self.fields:
            f.Read(dst, fh)
    def Write(self, src, fh):
        for f in self.fields:
            f.Write(src, fh)
    def Init(self, src):
        for f in self.fields:
            f.Init(src)

    
class FieldBase():
    """ Base class for the fields used in the templating.
    """
    #init?
    def Read(self, dst, fh):
        raise Exception('Implement in subclass.')
    def Write(self, src, fh):
        raise Exception('Implement in subclass.')
    def Init(self, src):
        raise Exception('Implement in subclass.')
    @staticmethod
    def noop(x):
        return True
    #
class Field(FieldBase):
    """ Represents a single field with a known size
    Only int values are supported.
    """
    def __init__(self, field_name, size, validator=None):
        self.field_name = field_name
        self.size = size
        self.validator = validator
        if validator is None:
            self.validator = FieldBase.noop
        if not callable(self.validator):
            raise Exception('validator must be a function/lambda')
    def Read(self, dst, fh):
        data = fh.readbytes(self.size)
        if (not self.validator(data)):
            raise Exception(f"Validator failed for {self.field_name} with value {data}.")
        setattr(dst, self.field_name, data)
    def Write(self, src, fh):
        data = getattr(src, self.field_name)
        fh.writebytes(data, self.size)
        #validate on write too?
    def Init(self, dst):
        data = 0
        setattr(dst, self.field_name, data)

class ArrayField(FieldBase):
    """ Represents a collection of fields, each with the same size
    These will be read together and stored into an array/dictionary
    """
    def __init__(self, field_name, fields, size, validator=None):
        self.field_name = field_name
        self.fields = fields
        self.size = size
        self.validator = validator
        if validator is None:
            self.validator = FieldBase.noop
    def Read(self, dst, fh):
        arr = {}
        for f in self.fields:
            data = fh.readbytes(self.size)
            arr[f] = data
            if (not self.validator(data)):
                raise Exception(f"Validator failed for {self.field_name}, subfield {f} with value {data}.")
        setattr(dst, self.field_name, arr)
    def Write(self, src, fh):
        arr = getattr(src, self.field_name)
        for f in self.fields:
            data = arr[f]
            fh.writebytes(data, self.size)
            #validate on write too?
    def Init(self, dst):
        arr = {}
        for f in self.fields:
            arr[f] = 0
        setattr(dst, self.field_name, arr)

class BytesField(FieldBase):
    """Represents a sequence of unknown bytes.
    These will be read in and then spit back out.
    """
    def __init__(self, field_name, size):
        self.field_name = field_name
        self.size = size
    def Read(self, dst, fh):
        data = fh.read(self.size)
        setattr(dst, self.field_name, data)
    def Write(self, src, fh):
        data = getattr(src, self.field_name)
        assert len(data) == self.size
        fh.write(data)
    def Init(self, src):
        data = 0
        setattr(dst, self.field_name, data)

class NegativeNumber(FieldBase):
    """ 3peso did some really weird shit with potentially-negative numbers in the dlsite version
    Cubetype fixed it. This also means that the size of the data is different.
    Fun.
    The endianness is used as a proxy for the version to use. (dlsite is big, steam is little)
    """
    def __init__(self, field_name, size):
        self.field_name = field_name
        self.size = size
        #endianness isn't available in init.
    def Read(self, dst, fh):
        if fh.endianness == BIG_ENDIAN:
            sign_byte = fh.readbytes(1)
            data = fh.readbytes(self.size)
            if sign_byte != 0:
                data = -data
        else:
            data = fh.readbytes(self.size)
            #https://stackoverflow.com/a/37075643
            #Probably the easiest way to do this.
            b = data.to_bytes(self.size, byteorder=sys.byteorder, signed=False)
            data = int.from_bytes(b, byteorder=sys.byteorder, signed=True)
        setattr(dst, self.field_name, data)
    def Write(self, src, fh):
        data = getattr(src, self.field_name)
        if fh.endianness == BIG_ENDIAN:
            sign_byte = 0
            if data < 0:
                sign_byte = 1
                data = -data
            fh.writebytes(sign_byte, 1)
            fh.writebytes(data, self.size)
        else:
            b = data.to_bytes(self.size, byteorder=fh.endianness, signed=True)
            fh.write(b)
    def Init(self, dst):
        data = 0
        setattr(dst, self.field_name, data)
    #

class PositionAssert(FieldBase):
    """Validation pretending to be an input.
    Read/Write will not actually read/write anything, and will instead check the stream position
    and throw if it doesn't match the expected value.
    """
    def __init__(self, pos):
        self.pos = pos
    def Read(self, dst, fh):
        currpos = fh.tell()
        if currpos != self.pos:
            raise Exception(f"Position validation failed on read: Expected {self.pos}, actually at {currpos}.")
    def Write(self, src, fh):
        currpos = fh.tell()
        if currpos != self.pos:
            raise Exception(f"Position validation failed on write: Expected {self.pos}, actually at {currpos}.")
    def Init(self, src):
        pass
#