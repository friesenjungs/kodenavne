import jpype
jpype.startJVM()
from asposecells.api import Workbook
workbook = Workbook("wordlists/english.txt")
# First row of txt file is attribute-name in json file
workbook.save("wordlists/english.json")
jpype.shutdownJVM()

