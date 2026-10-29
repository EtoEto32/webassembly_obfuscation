import random
import unittest
from audit_similarity_ties import choose_reference, summarize, MARKERS


class TieTests(unittest.TestCase):
    def test_anchors_and_ambiguous_nonanchors(self):
        row={'sha256':'b','ties':['a','b'],'exact_reference_member':True}
        for rule in ('lex_first','lex_last','ambiguous_singleton','random'):
            self.assertEqual(choose_reference(row,rule,random.Random(0)),'b')
        row['exact_reference_member']=False
        self.assertEqual(choose_reference(row,'lex_first'),'a')
        self.assertEqual(choose_reference(row,'lex_last'),'b')
        self.assertIsNone(choose_reference(row,'ambiguous_singleton'))

    def test_equal_group_weight_and_missing_denominator(self):
        rows=[{'sha256':str(i),'score':1,**{m:v for m in MARKERS}}
              for i,v in enumerate((True,False,False,None))]
        # Group A mean 1/3, group B has no observed value: denominator 1,
        # not 2 groups. A missing marker must never become a false marker.
        result=summarize(rows,['a','a','a','b'],.9)
        self.assertEqual(result['groups'],2)
        self.assertEqual(result[MARKERS[0]+'_groups_with_data'],1)
        self.assertEqual(result[MARKERS[0]+'_modules_with_data'],3)
        self.assertAlmostEqual(result[MARKERS[0]+'_equal_group_mean'],1/3)


if __name__=='__main__':unittest.main()
