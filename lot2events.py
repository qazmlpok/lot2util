from lot2helper import *
from DataTemplate import *

event_data = loadEvents()

class EventDataTemplate(DataTemplate):
    def __init__(self):
        self.fields = [
            ArrayField('eventFlags', range(0, 0x13EC), 1)
        ]

class EventData:
    """Represents data loaded from file EVF01 in the save folder. 
    These are event flags. Most are unknown.
    """
    template = EventDataTemplate()
    def __init__(self, filedata):
        EventData.template.Read(self, filedata)
    
    def save_to_file(self, fh):
        #I don't think there's any reason to allow this, at least until all red/boss/relay icons are mapped out
        #Which I'm not about to do.
        raise Exception("Not going to allow writes.")
        EventData.template.Write(self, fh)
    
    def print_all(self):
        for addr in event_data:
            #addr is an int; event_data[addr] is a hex string.
            event = event_data[addr]
            data = self.eventFlags[addr]
            print(f"{event['Address']}: {event['Floor']} {event['Event']}: {data}")
    #Or maybe take a filter. This is only going to be used for the stones of awakening.
    def all_events(self):
        #A more seamless interface would be to just put the savefile's data into event_data
        #or otherwise permanently combine them.
        #Maybe after I support writing (i.e. map out the events)
        data = event_data.copy()
        for addr in data:
            data[addr]["value"] = self.eventFlags[addr]
        return data
#