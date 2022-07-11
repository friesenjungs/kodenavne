import jpype
import asposecells
jpype.startJVM()
from asposecells.api import Workbook
workbook = Workbook("wordlists/deutschKurz.txt")
# First row of txt file is attribute-name in json file
workbook.save("wordlists/deutschKurz.json")
jpype.shutdownJVM()