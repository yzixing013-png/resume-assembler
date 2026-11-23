# Resume Assembler

让 Agent 收集项目、论文和证书等资料，维护完整经历库，再根据 JD 和 LaTeX 模板生成有事实依据的单页 PDF。

## 让 Agent 安装和使用

在支持 Skill 安装的 Codex 中发送下面这段话。

```text
请使用 skill-installer 安装这个 Skill
https://github.com/yzixing013-png/resume-assembler/tree/main/skills/resume-assembler
安装后使用 resume-assembler 引导我提供经历资料和简历模板，建立本地经历库，再根据目标 JD 生成简历。
```

之后可以直接说“补充这个项目”或“根据这个 JD 再生成一份”。Skill 首次使用会检查已有资料、收集缺失材料与模板，整理档案后再询问 JD。用户可以先提供部分材料，模板缺省时使用公开默认模板。

Skill 目录自包含操作说明、Python 脚本和公开模板，单独安装该目录即可使用。其他支持 Agent Skills 的客户端可将 `skills/resume-assembler` 目录安装到其识别的位置，然后调用 `resume-assembler`。具体安装方式取决于客户端。

需要 Python 3.10+、PyMuPDF 和 Tectonic。Agent 会检查依赖并协助配置。Skill 模式由当前 Agent 负责理解材料和写作，脚本负责归档、提取文字、校验和编译。数据默认放在当前工作目录的 `resume-data/`，也可以指定已有资料目录。旧版网页的 `data/` 可以直接作为 `--data` 使用。

## 三个工具入口

以下示例从仓库根目录运行。独立安装后，Agent 会使用安装目录内脚本的绝对路径。

```sh
python skills/resume-assembler/scripts/resume.py init --data ./resume-data
python skills/resume-assembler/scripts/resume.py import --data ./resume-data --file ./report.pdf
python skills/resume-assembler/scripts/resume.py import --data ./resume-data --file ./template.zip --kind template
python skills/resume-assembler/scripts/resume.py render --data ./resume-data --assembly ./assembly.json --jd ./jd.txt
```

`import` 也支持 `--github https://github.com/owner/repo` 归档公开仓库 README。项目目录与更深入的代码、实验材料由 Agent 查看并选取相关文件导入。PDF、DOCX、Markdown 和文本可提取文字，图片与扫描件保留原文件，交由 Agent 可用的图像/OCR 工具阅读。重复材料按 SHA-256 去重。

Agent 按固定格式更新 `library.json` 中的完整项目报告和事实，编辑前运行 `init` 留存备份。脚本写库时也会备份并原子替换。每次生成单独保存 PDF、TeX、预览、经历库快照和事实引用。数据格式与完整引导流程见 [Skill](skills/resume-assembler/SKILL.md) 和 [格式说明](skills/resume-assembler/references/formats.md)。

单独安装 Skill 的测试方式是只复制 `skills/resume-assembler` 目录，在独立资料目录运行三个命令。字体、照片和个人资料由用户自己提供。仓库默认模板使用 TeX 发行版字体。

## 本地网页

需要 Python 3.10+、已登录的 Codex CLI 和 Tectonic。

Windows 运行 `start.ps1`，首次创建虚拟环境并安装 PyMuPDF。或执行：

```sh
python -m pip install -r requirements.txt
python app.py
```

默认打开 http://127.0.0.1:8766 ，只监听本机。若可执行程序不在 PATH，在不纳入Git的 `local-settings.json` 中填写 `codex` 和 `tectonic` 的绝对路径。

## 日常使用

经历库采用两层资料：`facts` 保存可复用的简短事实，`reports` 保存完整项目档案、实验报告和方法细节，生成内容可以引用事实ID或项目内报告ID。报告应说明背景、本人职责、数据、实验设置、基线、结果、失败与局限。原始资料属于证据，不代表其中所有内容均已核验，也不能把计划写成已完成成果。详细报告可在项目编辑区保存，现阶段不会自动整理全部本地实验目录。

1. 首次在经历库保存个人信息和项目。可提取 PDF/文字或本地目录，预览后让Codex整理为草稿，人工确认后追加项目。
2. 粘贴完整 JD，点击生成。无需单独填写模型API密钥，使用已登录的Codex认证和额度。
3. 查看项目取舍、岗位缺口、事实ID与PDF预览。修改JSON中的描述可重新排版，不再次调用AI。

读取本地目录仅检查根目录的 README/Markdown/Python，显示预览后再发给Codex。GitHub导入只读取公开仓库README；深入源码可克隆后本地导入。自动脱敏不是绝对保障，请检查预览。

## 模板

默认提供本项目原创公开模板。支持上传LaTeX ZIP：resume类模板会保留首个section前的头部；其他模板在正文加入 `{{CONTENT}}`。内容使用标准section/subsection/itemize，不保证兼容任意宏包或任意ZIP。DOCX待实现。

公开模板的个人信息来自资料库。自定义模板支持 `{{NAME}}`、`{{CONTACT}}`、`{{ROLE}}`、`{{AVAILABILITY}}` 头部占位符；原有硬编码头部保留上传文件的文字，需检查并自行更新后重新上传。

编译使用Tectonic `--untrusted`，不运行ZIP中的脚本，不启用shell escape。模板仅导入到本地；不要把私人字体、照片和原始项目数据打包进公开仓库。

## 出版与事实边界

网页生成采用 TF-IDF 余弦相似度与 MMR 去重，保留全部项目和原子事实，由 Codex 最终选择项目组合。每个项目默认提供 7 个可追踪报告片段，完整报告保留，检索记录存为任务目录的 retrieval.json。Skill 模式由当前 Agent 阅读档案并选择项目，附带 JD 时同时保存检索诊断记录。相似度不代表 ATS 匹配率或录用概率。共享实现位于 skills/resume-assembler/scripts/resume_evidence.py，依据与适用边界见 [方法说明](docs/methodology.md)。

- 选择2至4个相关项目为提示目标，后端最多接受5个；不承诺每次生成都能满足单页。
- 项目标题、时间和技术来自原项目；每条生成描述引用项目内事实ID，拒绝来源中未出现的数字。
- 自动尝试10至11pt排版，检查单页及底部边界；超页会保留编辑结果并提示减少内容，不静默删改。
- 数字检查不证明语义正确；页面检查不代替人工视觉检查。无法自动确认作者贡献、技术熟练度或第三方数据权利。所有生成品仍需事实审核。
- 首次Tectonic可能下载标准TeX依赖。编译错误保留在任务目录。

## 文件与隐私

`data/` 内保存资料、模板、任务、原始结果、日志、PDF和资料快照，整体被Git忽略；`local-settings.json`同样忽略。点生成/提取会将相应文字发送给用户现有Codex服务；文件存本地不意味着推理离线。

当前版本为单人本机使用，不适合直接暴露到公网；不包含账号、协作、自动投递和云端存储。

## 检验

```sh
python -m unittest discover -s tests -v
```

AI运行结果依赖当前Codex版本和登录状态。调用依据：[OpenAI非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)，使用结构化输出而非让模型生成可执行代码。调用忽略桌面应用配置以避免内部模型别名和MCP冲突；如CLI默认模型不可用，可在local-settings.json填写codex_model。

MIT许可仅覆盖本项目原创代码与公开模板。用户上传内容保留其原有权利。你的个人模板不属于公开发行内容。
