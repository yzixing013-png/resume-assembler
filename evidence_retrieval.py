"""Lexical TF-IDF + MMR for report excerpts, not an ATS or hiring probability.

MMR: Carbonell/Goldstein, relevance minus maximum selected-item redundancy.
All project identities and atomic facts remain available to the final LLM selector.
"""
import copy, math, re
from collections import Counter

REFERENCES = [
    'https://students.lti.cs.cmu.edu/11899/files/Final-p181-goldstein.pdf',
    'https://arxiv.org/abs/2605.05257',
    'https://ocs.yale.edu/resources/writing-impactful-resume-bullets/',
]

WRITING_RULES = '''写作依据Yale职业指导的Action–Project–Result及成果–衡量–方法结构：
先解析JD硬条件、核心任务和加分项；项目组合覆盖不同要求，避免反复证明同一能力。
每条写具体个人行动、解决的问题和有依据的结果；有对照就写基线、变化、单位、时间窗。
规模（条数、数据量）、质量改善和业务收益必须区分，不能将测试通过包装为用户增长。
优先展示结果与关键技术决策，避免堆技术名词、空泛动词或只列工作流程。
负结果可体现诊断与决策价值，不写成成功提升；开发回放、前瞻测试、单题和全量基准严格区分。
用户确认的contribution_confirmation是个人研究归属声明；可使用设计、实现、研究等主动表述。
仍需说明复用系统/框架，不能虚构第一作者、已录用、实盘收益或他人系统的原创归属。
来源中的阶段排名日期、在投状态和结果适用范围不可删；详细限制保留档案，简历简洁表述。
这是写作指导，不是已经验证的录用效果或ATS评分算法。'''

def chunks(report, limit=1600):
    if report.get('is_excerpt'): return [report]
    content=report.get('content','');parts=[];buffer=''
    for line in content.splitlines(keepends=True):
        while len(line)>limit:
            if buffer:parts.append(buffer);buffer=''
            parts.append(line[:limit]);line=line[limit:]
        if len(buffer)+len(line)>limit: parts.append(buffer);buffer=''
        buffer+=line
    if buffer.strip():parts.append(buffer)
    return [dict(report,id=report['id']+'::c'+str(i+1),content=text,is_excerpt=True,parent_report_id=report['id']) for i,text in enumerate(parts)]

def terms(text):
    text=text.lower();out=re.findall(r'[a-z][a-z0-9+#.-]*',text)
    for segment in re.findall(r'[\u4e00-\u9fff]+',text):
        out.extend(segment[i:i+2] for i in range(len(segment)-1))
    return out

def cosine(a,b):return sum(value*b.get(key,0) for key,value in a.items())

def prepare_context(library,jd,budget=7,weight=0.7):
    context=copy.deepcopy(library);audit=[]
    for project in context['projects']:
        rows=[chunk for report in project.get('reports',[]) for chunk in chunks(report)]
        docs=[Counter(terms(jd))]+[Counter(terms(row['content'])) for row in rows]
        df=Counter(token for doc in docs for token in doc)
        vectors=[]
        for doc in docs:
            vec={t:(1+math.log(n))*(math.log((len(docs)+1)/(df[t]+1))+1) for t,n in doc.items()}
            norm=math.sqrt(sum(v*v for v in vec.values())) or 1
            vectors.append({t:v/norm for t,v in vec.items()})
        selected=[];scores=[]
        while len(selected)<min(budget,len(rows)):
            candidates=[]
            for i in range(len(rows)):
                if i in selected:continue
                relevance=cosine(vectors[0],vectors[i+1])
                novelty=max((cosine(vectors[i+1],vectors[k+1]) for k in selected),default=0)
                candidates.append((weight*relevance-(1-weight)*novelty,-i,i,relevance))
            score,_,index,relevance=max(candidates);selected.append(index)
            scores.append({'id':rows[index]['id'],'lexical_relevance':round(relevance,4),'mmr':round(score,4)})
        project['reports']=[rows[i] for i in selected]
        audit.append({'project_id':project['id'],'available_chunks':len(rows),'selected':scores})
    return context,{'method':'TF-IDF cosine + MMR report retrieval; LLM selects projects','lambda':weight,'calibrated':False,'references':REFERENCES,'projects':audit}
