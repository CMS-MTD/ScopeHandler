"""
Run in the directory above as:

python -m unit_test.test_merge_scope_etroc
"""

import unittest
import filecmp #helps compare files and directories!
import uproot
import awkward as ak
import os

from merge_scope_etroc import merge_trees

class TestFinalMerge(unittest.TestCase):
    """
    Test the final output of merge scope etroc
    """

    def test_merge_trees(self):
        """
        Simply compares the bytes of the output file of merge scope etroc to a known good output.

        Typically this is used for the refactoring of the scipt. Because obviously any changes to how the numbers are calculted (for example the clock fitting), will make this fail.
        
        Needs to be ran one directory up with: python -m unit_test.test_merge_scope_etroc
        """

        unit_test_array = uproot.open('unit_test/run_6685_rb0.root')['pulse'].arrays()

        #will be obtained from running the merge trees function
        reco_data_path = "unit_test/converted_run6685.root"
        scope_data_path = "unit_test/run_scope6685.root"
        etroc_data_path = "unit_test/output_run_6685_rb0.root"
        
        out_path = "./unit_test/_temp_data.root"
        try: #could move this sort of book keeping check of the file as a decorator
            merge_trees(
                [reco_data_path, scope_data_path, etroc_data_path], 
                ['pulse','pulse','pulse'], 
                out_path
            )
            input_array = uproot.open(out_path)['pulse'].arrays()
        except Exception as e:
            if os.path.isfile(out_path):
                print('Error, found output file, removing it first!')
                os.remove(out_path)
            raise ValueError(str(e))
        os.remove(out_path)
        self.assertTrue(
            # for some reason ak.array_equal cannot be imported, so I set the tolerances to 0 on almost working
            ak.almost_equal(unit_test_array, input_array, atol=0.0001)
        )

if __name__ == '__main__':
    unittest.main()