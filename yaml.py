
from ruamel import yaml

data = """
def1: &ANCHOR1
    key1: value1
def: &ANCHOR
    <<: *ANCHOR1
    key: value
value:
    <<: *ANCHOR
"""

# This fails
#print yaml.load(data, Loader=yaml.RoundTripLoader)['value']

# This works
print yaml.load(data, Loader=yaml.SafeLoader)['value']
