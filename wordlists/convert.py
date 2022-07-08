import jpype
import asposecells
jpype.startJVM()
from asposecells.api import Workbook
workbook = Workbook("english.txt")
# First row of txt file is attribute-name in json file
workbook.save("english.json")
jpype.shutdownJVM()