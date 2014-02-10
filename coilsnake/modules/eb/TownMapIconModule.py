import yaml
from re import sub

from coilsnake.modules.eb import EbModule
from coilsnake.modules.eb.EbTablesModule import EbTable
from coilsnake.modules.Table import ValuedIntTableEntry
from coilsnake.Progress import updateProgress


class TownMapIconModule(EbModule.EbModule):
    NAME = "Town Map Icon Positions"
    FREE_RANGES = [(0x21f491, 0x21f580)]  # Pointer Table and Data

    _ASMPTR_PTR_TBL = 0x4d464

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._ptrTbl = EbTable(0xE1F491)
        self._entries = []
        self._entryIdField = ValuedIntTableEntry(None, None,
                                                 ["Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers"])
        self._iconField = ValuedIntTableEntry(None, None,
                                              ["0", "Hamburger Shop", "Bakery", "Hotel",
                                               "Restaurant", "Hospital", "Shop", "Dept Store", "Bus Stop",
                                               "South to Twoson", "North to Onett", "South to Threed",
                                               "West to Twoson", "East to Desert", "West to Desert",
                                               "East to Toto", "Hint", "Ness", "Small Ness",
                                               "North", "South", "West", "East"])

    def read_from_rom(self, rom):
        self._ptrTbl.readFromRom(rom,
                                 EbModule.toRegAddr(
                                     EbModule.readAsmPointer(rom,
                                                             self._ASMPTR_PTR_TBL)))
        updateProgress(5)
        for i in range(self._ptrTbl.height()):
            loc = EbModule.toRegAddr(self._ptrTbl[i, 0].val())
            entry = []
            while True:
                x = rom[loc]
                if x == 0xff:
                    break
                y = rom[loc + 1]
                icon = rom[loc + 2]
                flag = rom.readMulti(loc + 3, 2)
                entry.append((x, y, icon, flag))
                loc += 5
            self._entries.append(entry)
            i += 1
        updateProgress(45)

    def write_to_rom(self, rom):
        self._ptrTbl.clear(6)
        i = 0
        for entry in self._entries:
            writeLoc = rom.getFreeLoc(len(entry) * 5 + 1)
            self._ptrTbl[i, 0].setVal(
                EbModule.toSnesAddr(writeLoc))
            for (x, y, icon, flag) in entry:
                rom[writeLoc] = x
                rom[writeLoc + 1] = y
                rom[writeLoc + 2] = icon
                rom.writeMulti(writeLoc + 3, flag, 2)
                writeLoc += 5
            rom[writeLoc] = 0xff
            i += 1
        updateProgress(45)
        EbModule.writeAsmPointer(rom, self._ASMPTR_PTR_TBL,
                                 EbModule.toSnesAddr(
                                     self._ptrTbl.writeToFree(rom)))
        updateProgress(5)

    def read_from_project(self, resourceOpener):
        self._entries = [None] * 6
        with resourceOpener("TownMaps/icon_positions", "yml") as f:
            data = yaml.load(f, Loader=yaml.CSafeLoader)
            for name in data:
                entry = []
                for subEntry in data[name]:
                    self._iconField.load(subEntry["Icon"])
                    entry.append((
                        subEntry["X"],
                        subEntry["Y"],
                        self._iconField.val(),
                        subEntry["Event Flag"]))
                self._entryIdField.load(name)
                self._entries[self._entryIdField.val()] = entry
        updateProgress(50)

    def write_to_project(self, resourceOpener):
        out = dict()
        i = 0
        for entry in self._entries:
            outEntry = []
            for (x, y, icon, flag) in entry:
                self._iconField.setVal(icon)
                outEntry.append({
                    "X": x,
                    "Y": y,
                    "Icon": self._iconField.dump(),
                    "Event Flag": flag})
            self._entryIdField.setVal(i)
            out[self._entryIdField.dump()] = outEntry
            i += 1
        updateProgress(25)
        with resourceOpener("TownMaps/icon_positions", "yml") as f:
            s = yaml.dump(out, default_flow_style=False,
                          Dumper=yaml.CSafeDumper)
            s = sub("Event Flag: (\d+)",
                    lambda i: "Event Flag: " + hex(int(i.group(0)[12:])), s)
            f.write(s)
        updateProgress(25)

    def upgrade_project(self, oldVersion, newVersion, rom, resourceOpenerR,
                        resourceOpenerW, resourceDeleter):
        global updateProgress
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion <= 2:
            tmp = updateProgress
            updateProgress = lambda x: None
            self.read_from_rom(rom)
            self.write_to_project(resourceOpenerW)
            updateProgress = tmp
            self.upgrade_project(3, newVersion, rom, resourceOpenerR,
                                 resourceOpenerW, resourceDeleter)
        else:
            self.upgrade_project(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)