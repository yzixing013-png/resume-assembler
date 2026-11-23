"""Shared evidence validation and LaTeX rendering for the Skill and web app."""
from pathlib import Path, PurePosixPath
import io, re, shutil, subprocess, zipfile
from resume_evidence import chunks

def safe_extract(raw,destination):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos=archive.infolist()
        if len(infos)>1500 or sum(x.file_size for x in infos)>300*1024*1024: raise ValueError('模板解压大小或文件数量超限')
        for info in infos:
            name=info.filename.replace('\\','/')
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or ':' in name or (info.external_attr>>16)&0o170000==0o120000: raise ValueError('模板包含非法路径或符号链接')
            if path.suffix.lower() in {'.exe','.bat','.cmd','.ps1','.dll','.sh'}: raise ValueError('模板 ZIP 不应包含可执行程序')
        archive.extractall(destination)
    tex=list(destination.rglob('*.tex'))
    candidates=[p for p in tex if p.name in ['main.tex','resume.tex'] and '\\documentclass' in p.read_text('utf-8',errors='replace')]
    if not candidates: candidates=[p for p in tex if '\\documentclass' in p.read_text('utf-8',errors='replace')]
    if not candidates: raise ValueError('ZIP 中没有 LaTeX 主文件')
    main=sorted(candidates,key=lambda p:(len(p.parts),p.name!='main.tex',p.name))[0]
    content=main.read_text('utf-8',errors='replace')
    # First version supports resume-class templates and explicit content markers.
    if '{{CONTENT}}' in content: adapted=content
    elif '\\section' in content and '\\documentclass{resume}' in content:
        adapted=content[:re.search(r'\\section\s*\{',content).start()]+ '{{CONTENT}}\n\\end{document}\n'
    else: raise ValueError('模板需使用 resume 类，或在正文中加入 {{CONTENT}} 占位符。DOCX 暂未支持。')
    if re.search(r'\\(?:write18|input\s*\|)',content): raise ValueError('不支持包含外部命令的模板')
    (main.parent/'adapter.tex.txt').write_text(adapted,'utf-8')
    return main.parent

def tex(s):
    table={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(table.get(c,c) for c in str(s))

def evidence_texts(project):
    evidence={f['id']:f['text'] for f in project['facts']}
    for report in project.get('reports',[]):
        # Reports remain source material, not independently verified achievements.
        evidence[report['id']]=report.get('content','')
        for chunk in chunks(report): evidence[chunk['id']]=chunk['content']
    return evidence


def validate(result,library):
    projects={p['id']:p for p in library['projects']};seen=set()
    if not result.get('selected'): raise ValueError('没有选中项目，请补充经历库')
    if len(result['selected'])>5: raise ValueError('最多选择5个项目')
    for entry in result['selected']:
        if entry['id'] not in projects or entry['id'] in seen: raise ValueError('出现未知或重复项目')
        seen.add(entry['id']);project=projects[entry['id']]
        facts=evidence_texts(project)
        if not entry.get('bullets'): raise ValueError('选中的项目至少需要一条描述')
        for bullet in entry['bullets']:
            if not bullet['evidence'] or any(x not in facts for x in bullet['evidence']): raise ValueError('描述缺少有效的原始事实引用')
            source=' '.join(facts[x] for x in bullet['evidence'])
            for qualifier in re.findall(r'（(截至[^）]+)）',source):
                if qualifier not in bullet['text']:
                    bullet['text']=bullet['text'].rstrip('。')+'（'+qualifier+'）。'
            # Numeric preservation is a mechanical check, not a semantic truth claim.
            source+=' '+project.get('tags','')+' '+project.get('date','')+' '+project.get('title','')
            available={n.replace(',','') for n in re.findall(r'\d[\d,]*(?:\.\d+)?',source)}
            for number in re.findall(r'\d[\d,]*(?:\.\d+)?',bullet['text']):
                if number.replace(',','') not in available: raise ValueError('描述出现来源中没有的数字：'+number)
            if len(bullet['text'])>450: raise ValueError('单条描述过长')
    return result

def render(result,library,folder,data_directory,engine=None):
    import pymupdf
    template=library.get('template','public')
    if template!='public':
        source=Path(data_directory)/'templates'/template
        source=next(source.rglob('adapter.tex.txt')).parent
        for item in source.iterdir():
            if item.is_dir(): shutil.copytree(item,folder/item.name,dirs_exist_ok=True)
            elif item.suffix not in ['.pdf','.log','.aux','.out']: shutil.copy2(item,folder/item.name)
        shell=(source/'adapter.tex.txt').read_text('utf-8')
    else:
        shell=(Path(__file__).resolve().parents[1]/'assets/public.tex').read_text('utf-8')
    profile=library['profile'];projects={p['id']:p for p in library['projects']}
    def section(title,lines):
        return '\\section{'+tex(title)+'}\n'+'\n'.join(tex(x)+r'\par' for x in lines)+'\n'
    prefix=''
    if template=='public': prefix=r'\begin{center}{\LARGE\bfseries '+tex(profile['name'])+r'}\par '+tex(profile['contact'])+r'\par '+tex(result['role']+'｜'+profile['availability'])+r'\end{center}'
    content=prefix+section('教育经历',profile['education'])+r'\section{项目经历}'+'\n'
    for selected in result['selected']:
        project=projects[selected['id']]
        content+=r'\subsection*{\textbf{'+tex(project['title'])+r'}\hfill {\small '+tex(project['date'])+'}}\n'+r'{\small '+tex(project['tags'])+'}\n'+r'\begin{itemize}'+'\n'
        content+='\n'.join(r'\item '+tex(b['text']) for b in selected['bullets'])+ '\n'+r'\end{itemize}'+'\n'
    content+=section('技能',profile['skills'])+section('获奖与补充',profile['awards'])
    for title,field in [('论文与出版','publications'),('证书','certifications')]:
        if profile.get(field): content+=section(title,profile[field])
    for marker,value in {'NAME':profile['name'],'CONTACT':profile['contact'],
                         'ROLE':result['role'],'AVAILABILITY':profile['availability']}.items():
        shell=shell.replace('{{'+marker+'}}',tex(value))
    engine=engine or shutil.which('tectonic')
    if not engine: raise ValueError('找不到 tectonic。请在 local-settings.json 配置编译器路径。')
    # Fill loop increases readable type and spacing while staying on one page.
    chosen=None
    for index,(size,leading) in enumerate([(10,12),(10.3,12.8),(10.5,13.4),(11,14)]):
        fit=f'\\AtBeginDocument{{\\fontsize{{{size}pt}}{{{leading}pt}}\\selectfont}}\n'
        document=shell.replace('{{CONTENT}}',content).replace('\\begin{document}',fit+'\\begin{document}')
        name=f'resume_{index}'
        (folder/(name+'.tex')).write_text(document,'utf-8')
        run=subprocess.run([engine,'-X','compile',name+'.tex','--untrusted'],cwd=folder,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        (folder/(name+'.log.txt')).write_text(run.stdout+run.stderr,'utf-8')
        pdf=folder/(name+'.pdf')
        if run.returncode or not pdf.exists(): raise ValueError('模板编译失败，详情见任务目录编译日志。')
        doc=pymupdf.open(pdf)
        if len(doc)!=1:
            doc.close();break
        if abs(doc[0].rect.width-595.28)>2 or abs(doc[0].rect.height-841.89)>2:
            doc.close();raise ValueError('模板需使用 A4 纸张')
        if not doc[0].get_text().strip():
            doc.close();raise ValueError('PDF 未提取到文字，请检查模板与字体')
        blocks=doc[0].get_text('blocks');bottom=max((b[3] for b in blocks),default=0)
        if bottom>doc[0].rect.height-20: doc.close();break
        doc[0].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(str(folder/'preview.png'))
        chosen=(pdf,folder/(name+'.tex'),round(bottom/doc[0].rect.height,2));doc.close()
    if not chosen: raise ValueError('内容超出一页，请在编辑区减少描述或项目，再重新排版；不会静默丢弃内容。')
    shutil.copy2(chosen[0],folder/'resume.pdf');shutil.copy2(chosen[1],folder/'resume.tex')
    return {'pages':1,'content_bottom_ratio':chosen[2],'review_required':True}
