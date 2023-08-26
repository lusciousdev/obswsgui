from string import Template
import datetime as dt

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class DeltaTemplate(Template):
    delimiter = "%"

def strfdelta(tdelta : dt.timedelta, fmt : str):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)