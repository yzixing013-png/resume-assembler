import unittest,sys,tempfile,io,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class CoreTests(unittest.TestCase):
    def library(self):
        return {'projects':[{'id':'p1','facts':[{'id':'f1','text':'验证7,266张快照'}]}]}
    def result(self,text='核对7,266张快照',evidence=None):
        return {'selected':[{'id':'p1','bullets':[{'text':text,'evidence':['f1'] if evidence is None else evidence}]}]}
    def test_valid_number(self): app.validate(self.result(),self.library())
    def test_invented_number(self):
        with self.assertRaises(ValueError):app.validate(self.result('提高99%'),self.library())
    def test_numeric_substring_is_not_evidence(self):
        with self.assertRaises(ValueError):app.validate(self.result('核对26张快照'),self.library())
    def test_missing_evidence(self):
        with self.assertRaises(ValueError):app.validate(self.result(evidence=[]),self.library())
    def test_cross_project_evidence(self):
        with self.assertRaises(ValueError):app.validate(self.result(evidence=['other-project-fact']),self.library())
    def test_unknown_project(self):
        value=self.result();value['selected'][0]['id']='invented'
        with self.assertRaises(ValueError):app.validate(value,self.library())
    def test_escape_tex(self):self.assertEqual(app.tex('50% & x_y'),r'50\% \& x\_y')
    def zip(self,name,text):
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr(name,text)
        return raw.getvalue()
    def test_zip_traversal(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaises(ValueError):app.safe_extract(self.zip('../escape.tex','bad'),Path(p))
    def test_zip_resume(self):
        with tempfile.TemporaryDirectory() as p:
            root=app.safe_extract(self.zip('resume.tex',r'\documentclass{resume}\begin{document}\section{old}old\end{document}'),Path(p))
            self.assertIn('{{CONTENT}}',(root/'adapter.tex.txt').read_text())
    def test_zip_reject_executable(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaises(ValueError):app.safe_extract(self.zip('run.exe','bad'),Path(p))

if __name__=='__main__':unittest.main()
