import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidence_retrieval import chunks,prepare_context

class RetrievalTests(unittest.TestCase):
    def test_chunks_keep_every_character_and_stable_ids(self):
        report={'id':'r','content':('实验结果\n'*900)}
        rows=chunks(report)
        self.assertEqual(''.join(r['content'] for r in rows),report['content'])
        self.assertEqual(rows,chunks(report))
    def test_budget_does_not_remove_projects_or_atomic_facts(self):
        library={'projects':[{'id':'p','facts':[{'id':'f','text':'原事实'}],'reports':[{'id':'r','content':'Python数据清洗\n'*900}]}]}
        result,audit=prepare_context(library,'Python 数据清洗',budget=2)
        self.assertEqual(result['projects'][0]['facts'],library['projects'][0]['facts'])
        self.assertEqual(len(result['projects'][0]['reports']),2)
        self.assertNotIn('is_excerpt',library['projects'][0]['reports'][0])
        self.assertFalse(audit['calibrated'])
    def test_relevant_excerpt_first(self):
        library={'projects':[{'id':'p','facts':[],'reports':[{'id':'a','content':'gardening flowers'},{'id':'b','content':'python numpy pandas evaluation'}]}]}
        result,_=prepare_context(library,'python pandas',budget=1)
        self.assertEqual(result['projects'][0]['reports'][0]['parent_report_id'],'b')

if __name__=='__main__':unittest.main()
