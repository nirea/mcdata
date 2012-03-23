import mongoengine as mg
from models import Av
import pprint

mg.connect('mcdata')

pprint.pprint([a.to_lsl() for a in Av.objects.all()])


