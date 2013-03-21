import trtools.util.testing as tm
import trtools.io.api as trio
import trtools.tools.pload as pload

# TODO add a generic testing file
import sys; sys.exit(0)
store = trio.MetaFileCache('/Volumes/tradedata/dataload/mb_data2', leveled=2)
d = pload.pload(store)
for k in d:
    test = d[k]
    correct = store[k]
    tm.assert_frame_equal(test, correct)
