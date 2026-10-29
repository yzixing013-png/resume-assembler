# Resume Assembler

个人优先的本地简历组装工具：经历库 + 岗位描述 → Codex选择项目并改写 → 自选LaTeX模板 → 单页PDF与事实引用记录。

## 启动

需要 Python 3.10+、已登录的 Codex CLI 和 Tectonic。

Windows 运行 `start.ps1`，首次创建虚拟环境并安装 PyMuPDF。或执行：

```sh
python -m pip install -r requirements.txt
python app.py
```

默认打开 http://127.0.0.1:8766 ，只监听本机。若可执行程序不在 PATH，在不纳入Git的 `local-settings.json` 中填写 `codex` 和 `tectonic` 的绝对路径。

## 日常使用

1. 首次在经历库保存个人信息和项目。可提取 PDF/文字或本地目录，预览后让Codex整理为草稿，人工确认后追加项目。
2. 粘贴完整 JD，点击生成。无需单独填写模型API密钥，使用已登录的Codex认证和额度。
3. 查看项目取舍、岗位缺口、事实ID与PDF预览。修改JSON中的描述可重新排版，不再次调用AI。

读取本地目录仅检查根目录的 README/Markdown/Python，显示预览后再发给Codex。GitHub导入只读取公开仓库README；深入源码可克隆后本地导入。自动脱敏不是绝对保障，请检查预览。

## 模板

默认提供本项目原创公开模板。支持上传LaTeX ZIP：resume类模板会保留首个section前的头部；其他模板在正文加入 `{{CONTENT}}`。内容使用标准section/subsection/itemize，不保证兼容任意宏包或任意ZIP。DOCX待实现。

个人模板的头部信息（姓名、照片、实习安排）目前保留自上传文件，修改个人资料不会同步替换其中的硬编码文字。需要更新头部时重新上传模板。公开模板的个人信息来自资料库。

编译使用Tectonic `--untrusted`，不运行ZIP中的脚本，不启用shell escape。模板仅导入到本地；不要把私人字体、照片和原始项目数据打包进公开仓库。

## 出版与事实边界

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
