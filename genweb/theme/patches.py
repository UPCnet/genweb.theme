from BTrees.IOBTree import IOBTree
try:
    from BTrees.LOBTree import LOBTree
    SavedDataBTree = LOBTree
except ImportError:
    SavedDataBTree = IOBTree

import time


def _addDataRow(self, value):
    self._migrateStorage()

    if isinstance(self._inputStorage, IOBTree):
        # 32-bit IOBTree; use a key which is more likely to conflict
        # but which won't overflow the key's bits

        id = self._inputItems
        self._inputItems += 1
    else:
        # 64-bit LOBTree
        id = int(time.time() * 1000)
        while id in self._inputStorage:  # avoid collisions during testing
            id += 1

    for i in range(len(value)):
        value[i] = value[i].decode('string_escape')

    self._inputStorage[id] = value
    self._length.change(1)
