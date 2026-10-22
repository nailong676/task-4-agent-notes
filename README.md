learning-notes-ch5
Coding Agent 与代码生成
为什么"会写代码"是通用 Agent 的问题求解方式
第 5 章学习笔记 · 两个实验的完整过程，外加一次真实的排错：从"工具执行成功"到"结果符合要求"之间差了什么
 学习日期：2026-10-21 ~ 10-22  跑通实验：2 个  自测题：5 / 5  顺手修了 1 个真 bug
目录
引言：我原来的理解是错的
实验一：code-for-logic — 让确定性代码接管推理
实验二：coding-agent — 拆开看那个循环
排错复盘：155 → 161，我完整走了一遍 Agent 循环
自测题回答
总结与反思
引言：我原来的理解是错的
坦白说，翻开这一章之前，我心里想的是："Coding Agent？不就是会自动补全代码、能帮我写函数的那个东西吗。" 学完之后我意识到这个理解差得很远。能生成代码的助手是"开环"的，Coding Agent 是"闭环"的—— 它把代码写进文件、跑一遍、看到真实输出、再决定下一步。代码只是媒介，闭环 才是本体。
这一章更大的主张是：代码不只是写给程序员的，它是 "能创造新工具的工具" 。 模型不需要预装一个专用工具去解决每一类问题——用 Python 加几个通用库，就能现场把问题形式化、写成程序、 交给确定性的执行环境算出答案。这在实验一里看得特别清楚。
我选了两个实验来跑：一个验证"代码接管推理"，一个拆开看"Agent 循环本身"。后面还有一个计划外的收获——测试失败，我顺着排了一遍错，恰好把本章的核心概念全部亲身经历了一遍。
实验一：code-for-logic — 让确定性代码接管推理
实验在做什么
把"骑士与无赖"逻辑谜题翻译成约束满足问题（CSP），用 python-constraint 穷举求解。 这条路径完全离线、不需要 API Key ——正好适合我这种没有配置模型 API 的情况，而且能干净地验证一个命题： 只要约束写对了，答案就一定对，与任何模型的推理强弱无关。
真实运行记录
命令：python demo.py --mode solver，逐题预测和金标准自动比对，输出如下（节选）：
$ python demo.py --mode solver
离线约束求解基线    题目数：12

== 约束求解(solver，离线) ==
  [solver] kk01 (2人) ✓  解数=1  预测={'A': 'knight', 'B': 'knave'}
  [solver] kk02 (2人) ✓  解数=1  预测={'A': 'knave', 'B': 'knight'}
  [solver] kk03 (2人) ✓  解数=1  预测={'A': 'knight', 'B': 'knave'}
  [solver] kk04 (3人) ✓  解数=1  预测={'A': 'knave', 'B': 'knight', 'C': 'knave'}
  ...
  [solver] kk11 (5人) ✓  解数=1  预测={'A': 'knight', 'B': 'knight', 'C': 'knave', 'D': 'knave', 'E': 'knight'}
  [solver] kk12 (5人) ✓  解数=1  预测={'A': 'knave', 'B': 'knave', 'C': 'knight', 'D': 'knave', 'E': 'knave'}

准确率            100.0%
约束求解   准确率: 100.0%  (12/12)
完整逐题记录已保存到 last_run.json
​
12/12
离线求解器准确率
0
API 调用次数
32
kk11 的穷举空间（2⁵）
让我卡了一会儿的地方：双条件，不是硬约束
最开始我想当然地以为：把每个人"说的话"直接当作约束加进去就行。但那样建模是错的—— 如果 A 说"B 是骑士"，把 B == True 当硬约束，那 A 自己是骑士还是无赖就完全没起作用了，无赖的存在感直接消失。
正确的建模是双条件（等价） ：对每位说话者 X， t[X] == (X 说的话为真)。 X 是骑士，他的话必须为真；X 是无赖，他的话必须为假。说话人身份和话语真值是 锁死在一起 的，这才是"骑士与无赖"世界观的数学表达。
以 kk11 为例走一遍完整路径
5 个人、5 句话（4 句链式指认 + 1 句计数）：
A 说："B 是骑士"
B 说："C 是无赖"
C 说："D 是骑士"
D 说："E 是无赖"
E 说："我们五人当中至少有两个骑士"
先用结构化 DSL 把每句话变成 JSON 节点，再翻译成约束程序——下面这段不是我抄教程，是本地演示脚本 demo_kk11_trace.py 的真实输出：
$ python demo_kk11_trace.py
【结构化 DSL 翻译】
  A: ['is', 'B', 'knight']
  B: ['is', 'C', 'knave']
  C: ['is', 'D', 'knight']
  D: ['is', 'E', 'knave']
  E: ['count', 'knight', '>=', 2]

【核心约束规则】
对每位说话者 X，加一条双条件约束：
    t[X] == (X 说的话为真)

【实际求解结果】
共找到 1 个解
  解 1: {'A': '骑士', 'B': '骑士', 'C': '无赖', 'D': '无赖', 'E': '骑士'}
与金标准对比: ✓ 完全匹配


from constraint import Problem
p = Problem()

# 变量：每人 True(骑士) / False(无赖)
for name in ['A', 'B', 'C', 'D', 'E']:
    p.addVariable(name, [True, False])

# 双条件约束：t[speaker] == (speaker 的话为真)
p.addConstraint(lambda a, b: a == (b == True),  ['A', 'B'])   # A 说 "B 是骑士"
p.addConstraint(lambda b, c: b == (c == False), ['B', 'C'])   # B 说 "C 是无赖"
p.addConstraint(lambda c, d: c == (d == True),  ['C', 'D'])   # C 说 "D 是骑士"
p.addConstraint(lambda d, e: d == (e == False), ['D', 'E'])   # D 说 "E 是无赖"

# E 的计数陈述，涉及全部变量
p.addConstraint(
    lambda a, b, c, d, e: e == ((a + b + c + d + e) >= 2),
    ['A', 'B', 'C', 'D', 'E']
)

solutions = p.getSolutions()   # → 唯一解：A=骑士, B=骑士, C=无赖, D=无赖, E=骑士
​
我学到的关键一点：
eval_stmt() 本身不做求解，它只在给定赋值下算出某句话的真值； 真正的求解是 python-constraint 在穷举。模型（或者我）负责"翻译"，代码负责"判定"—— 2⁵=32 种组合一个个检查，整个过程没有任何"感觉上应该是对的"，只有满足或不满足。 心算真值传播很容易错（尤其链式 + 自指的时候），但穷举不会。
实验二：coding-agent — 拆开看那个循环
真实运行记录：先看看它有哪些手
命令：python main.py --list-tools，16 个工具全部注册：
$ python main.py --list-tools
共 16 个工具：

  Task           Launch a new agent to handle complex, multi-step tasks autonomously.
  Bash           Executes a given bash command in a persistent shell session with optional timeout...
  Glob           - Fast file pattern matching tool that works with any codebase size
  Grep           A powerful search tool built on ripgrep
  LS             Lists files and directories in a given path...
  ExitPlanMode   Use this tool when you are in plan mode and have finished presenting your plan...
  Read           Reads a file from the local filesystem...
  Edit           Performs exact string replacements in files.
  MultiEdit      This is a tool for making multiple edits to a single file in one operation...
  Write          Writes a file to the local filesystem.
  NotebookEdit   Completely replaces the contents of a specific cell in a Jupyter notebook...
  WebFetch / WebSearch / TodoWrite / BashOutput / KillBash  ...
​
类别
工具
作用
文件操作
Read / Write / Edit / MultiEdit
读写改文件，Write/Edit 写入后自动做语法检查
搜索
Grep / Glob / LS
正则搜索、模式匹配、目录列表
Shell
Bash / BashOutput / KillBash
持久会话执行命令、后台输出、终止
任务管理
TodoWrite / ExitPlanMode / Task
TODO 列表、计划模式、子代理
其他
NotebookEdit / WebFetch / WebSearch
Notebook 编辑、网页抓取/搜索
循环本体：Read → Think → Edit → Execute → Observe
flowchart TD
    A[用户输入] --> B[添加到 messages + 时间戳]
    B --> C{每轮迭代}
    C --> D[注入 system_hint<br/>工具计数 / TODO / 环境]
    D --> E[调用 LLM API<br/>流式响应]
    E --> F{LLM 输出}
    F -- 纯文本 --> G[无工具调用 → 任务完成]
    F -- 工具调用 --> H[执行工具]
    H --> I[工具结果追加到 messages]
    I --> C
    G --> J[输出最终答案]

    style C fill:#fdf3ef,stroke:#c75b3a
    style H fill:#e8f0eb,stroke:#5b8a72
    style G fill:#e8f0eb,stroke:#5b8a72
    style J fill:#fdf3ef,stroke:#c75b3a
纯文本

工具调用

用户输入

添加到 messages + 时间戳

每轮迭代

注入 system_hint
工具计数 / TODO / 环境

调用 LLM API
流式响应

LLM 输出

无工具调用 → 任务完成

执行工具

工具结果追加到 messages

输出最终答案

​
Figure 1: agent.py run() 的核心循环
读 agent.py 的 run() 方法时，有三处设计让我停下来想了很久：
1\. 文件系统是"外部记忆"，不是"存储柜"
模型上下文塞不下整个代码库，也不需要塞——Read/Grep/Glob 按需取用就行。 而且写好的代码、测试输出、日志都留在文件系统里，多轮迭代随时有"抓手"。 上下文是易失的，文件系统是持久的。
2\. 工具结果"回灌"进 messages
Bash 执行完，输出不是打给用户看的，而是追加回 messages ，成为下一轮 LLM 决策的输入。 这就是"Observe"的实现本质——Agent 不会幻想执行结果，它必须看到真实输出才能继续。
3\. 停止条件是"模型不再调用工具"
Agent 什么时候认为任务完成？——当 LLM 只输出纯文本、不再发起工具调用的时候。 但这只是模型的"声明"，不是验收。 真实验收要靠测试套件或人类。这一点我在下一节的排错里体会得特别深——工具层明明返回 success，测试照样一片红。
每轮注入的 System Hint
每次 API 调用前注入：当前时间 / 工作目录 / OS / Python 版本、工具调用计数（重复 ≥3 次告警防死循环）、当前 TODO。 本质是第 2 章讲的上下文工程：让模型知道自己在哪、做过什么、还剩什么。
排错复盘：155 → 161，我完整走了一遍 Agent 循环
这部分是计划外的。跑 pytest tests/ 验收 coding-agent 时失败了 10 个测试。 按参考学习策略的要求"区分模型说完成了和结果确实符合要求"，我决定不跳过，把根因挖出来。 事后看，这个过程本身就是本章最好的教材——我人肉扮演了一遍 Read → Think → Edit → Execute → Observe 。
第 1 步：Execute — 先看真实失败清单
$ python -m pytest tests/ -q   （修复前）
FAILED tests\test_bash_output_tool.py::...::test_retrieve_background_output - assert 'background output' in ''
FAILED tests\test_bash_output_tool.py::...::test_background_job_inherits_persistent_environment
    - assert 'persisted' in '#< CLIXML
<Objs Version="1.1.0.1" xmlns="<http://schemas.microsoft.com/powershell/2004/04>">...'
FAILED tests\test_bash_tool.py::...::test_command_with_exit_code - assert 1 == 0
FAILED tests\test_bash_tool.py::...::test_persistent_shell_session - assert 'hello' in ''
FAILED tests\test_bash_tool.py::...::test_subsecond_timeout_ms_allows_fast_command - assert -1 == 0
FAILED tests\test_edit_tool.py::...::test_lint_check_after_edit
    - AssertionError: assert 'lint_check' in {'file_path': '...test.py', 'replacements': 1, ...}
FAILED tests\test_edit_tool.py::...::test_edit_creates_syntax_error       （同上，lint_check 缺失）
FAILED tests\test_multi_edit_tool.py::...::test_lint_check_after_multi_edit（同上）
FAILED tests\test_write_tool.py::...::test_python_lint_check_success      （同上）
FAILED tests\test_write_tool.py::...::test_python_lint_check_failure      （同上）
======================= 10 failed, 155 passed in 28.48s =======================
​
先"Think"：10 个失败不是 10 个问题。粗看可以分成两组—— 5 个 bash 类 （persistent shell / exit code / background output）和 5 个 lint 类 （断言 'lint_check' in result.data，但 data 里根本没有这个键）。 注意失败的断言里有个细节：ToolResult(success=True, ...)——工具层自己认为执行成功了。 这就是"文件写入成功"≠"结果符合要求"的活例子。
第 2 步：Read + Grep — 定位 lint 组根因
搜 lint_check 定位到三个工具文件，读 write_tool.py 的检查逻辑：
# tools/write_tool.py（修复前）
result = subprocess.run(
    ["python3", "-m", "py_compile", str(file_path)],   # ← 问题在这
    capture_output=True, text=True, timeout=5
)
...
except FileNotFoundError:
    # Linter not installed
    return None          # ← 静默吞掉，lint_check 永远不出现
​
根因清楚了 ：lint 检查硬编码调用 python3 命令——这是 Linux/macOS 的叫法。 Windows 上的解释器叫 python.exe（我机器上是 Python313）。于是：
subprocess.run(["python3", ...]) 抛 FileNotFoundError
被 except FileNotFoundError 捕获，返回 None
调用方 if lint_result: result["lint_check"] = lint_result —— None 就不加键
结果：静默失败 ，工具照样 success，测试断言 lint_check in data 落空
验证猜想——where.exe python3 在本机确实找不到，而 where.exe python 返回 Python313\python.exe。猜想成立。
第 3 步：Edit — 最小修复
不想依赖 PATH 里的叫法，用 sys.executable（当前解释器的绝对路径）最稳。三个文件同样的改法：
# tools/write_tool.py / edit_tool.py / multi_edit_tool.py
import sys                                              # 新增
...
result = subprocess.run(
    [sys.executable, "-m", "py_compile", str(file_path)],   # python3 → sys.executable
    capture_output=True, text=True, timeout=5
)
​
第 4 步：Execute — 验收
$ python -m pytest tests/test_write_tool.py tests/test_edit_tool.py tests/test_multi_edit_tool.py -q
tests\test_write_tool.py .........          [ 29%]
tests\test_edit_tool.py ...........         [ 64%]
tests\test_multi_edit_tool.py ...........   [100%]
============================= 31 passed in 2.43s ==============================

$ python -m pytest tests/ -q   （全量回归）
======================= 4 failed, 161 passed in 30.35s =======================
​
155 → 161
通过测试数
10 → 4
失败数
5/5
lint 组全部修复
剩下的 4 个：为什么我选择不修
全部是 bash 工具测试——它们需要一个真的 bash 可执行文件。Windows 上走的是 PowerShell， 两者的会话模型、退出码语义、输出编码都不同。最有说服力的证据是测试失败时拿到的"输出"：
#< CLIXML
<Objs Version="1.1.0.1" xmlns="<http://schemas.microsoft.com/powershell/2004/04>">
  <Obj S="progress" RefId="0"...></Obj></Objs>
​
这是 PowerShell 的 CLIXML 序列化流，不是命令的真实 stdout——所以 assert 'persisted' in output 必然失败。 更巧的是，我在排错时跑 where.exe python3，PowerShell 连错误信息都用这坨 XML 包了一层。 要修这 4 个，得给 bash 工具做跨平台的 shell 抽象（检测平台、解析 CLIXML、统一退出码语义），那是另一个工程， 不是本章学习目标，如实记录比强行凑绿更有价值。
意外收获：亲眼见到 flaky
两次全量测试，失败清单不一样——第一次 test_retrieve_background_output 失败（assert 'background output' in ''）， 第二次它自己过了。时序依赖的后台输出测试，典型 flaky。 这直接呼应了自测题 4 我自己的答案：连续失败时，先怀疑测试本身 ——书上的话，我在第一次全量跑完后两个小时就撞上了。
这次排错教会我的三件事
静默失败比崩溃更危险 。except FileNotFoundError: return None 让问题被藏了两层——工具报 success，缺陷在测试层才暴露。生产代码里这种模式要警惕。
分组找根因，别逐个修症状 。10 个失败看着吓人，其实是 2 个根因。修 1 处，消 5 个测试。
验收必须回到测试 。修复后我跑了单组测试、又跑了全量回归——"lint 测试过了"不等于"没改坏别的东西"。这也是 Agent 循环里 Observe 之后还要再 Observe 的原因。
自测题回答
能生成一段代码的聊天助手，与 Coding Agent 的关键区别是什么？
开环 vs 闭环。
聊天助手输出代码就结束了，代码能不能跑、符不符合需求，它不知道也不关心，验证责任全在人。 Coding Agent 有 Read → Think → Edit → Execute → Observe 的闭环：写进文件、运行、看到真实输出、据此修正、再运行。 执行结果通过工具"回灌"进上下文，它才真正"知道"自己代码的效果。
具体到实验里的实现，闭环之外还有三样配套：文件系统（持久化中间产物）、工具注册表（16 个工具各有边界）、 状态追踪（system_hint 里的计数和 TODO）。
"文件写入成功""程序能运行""用户需求已满足"，为什么是三种不同的判断？
三个验证层级，逐层收窄，且上层永远不能由下层自动推出。
层级一：文件写入成功 ——字节落盘了。内容可能是语法垃圾，Write 返回 success 什么也保证不了。
层级二：程序能运行 ——exit_code=0。语法对、没有运行时错误，但输出可能完全答非所问。 用户问"算 1+1"，程序打印 "Hello World" 照样 exit_code=0。
层级三：需求已满足 ——需要人工验收或预设测试套件。离线求解器 12/12 全对，靠的是每道题都存了金标准解，自动比对。
这次排错给了我一个真实的层级一 vs 层级三案例：Edit 工具返回 success=True（层级一）， 但 lint_check 键从未出现在结果里，5 个测试全红（层级三）。 工具没报错 ≠ 事情做对了 ——静默失败专门在层级之间打洞。
为什么说代码可以是"创造新工具的工具"？请举一个非编程任务的例子。
因为代码用的是通用语言 + 通用库 ，而不是预装专用工具。 我没有"骑士无赖求解器"这个工具——但用 Python + python-constraint， 现场十几行就为 kk11 造了一个；换成 kk12，只改约束代码，底层工具不变。 专用工具是"一把钥匙开一把锁"，代码是"现场配钥匙的机床"。
非编程例子：帮朋友分析投资组合风险。
不写代码：凭印象说"这几只最近走势不错"——主观、不可复现。 写代码：Python + pandas + yfinance 拉三年股价，算协方差矩阵，跑一万次蒙特卡洛模拟，输出 VaR 和最大回撤—— 客观数值，任何人拿同样数据能跑出同样结果。
区分点：模型擅长理解问题、形式化、选策略；代码擅长精确计算、大数据量、可重复。 投资风险分析恰好是"需要可重复和可审查"的场景，理应交给代码。
如果 Agent 连续修改三次仍然测试失败，你希望它接下来检查什么，而不是继续盲改？
触发根因诊断，切换"诊断模式"。四个检查点：
测试本身可靠吗？ 预期行为和用户需求一致吗？有没有硬编码错误、flaky 因素（依赖时间/随机/网络）？ ——我在这次实验里亲历了：同一测试两次全量运行结果不同，"连续失败先怀疑测试"不是空话。
错误被正确理解了吗？ 区分 SyntaxError（没跑起来）/ RuntimeError（逻辑错）/ AssertionError（结果不对）； 看 traceback 定位到行号和调用栈，而不是只看最后一行。
修改对准根因了吗？ git diff 看三次累计改了什么；写 5 行最小复现脚本直接触发错误。 我这次就是先分组（5 bash + 5 lint），再各找一个根因——10 个症状、2 个病根，逐个修症状会改到天亮。
有遗漏的约束吗？ 对约束做反例检查：如果把它移除，解会怎么变？
机制上的建议 ：system_hint 里加 consecutive_failures 计数，超过阈值自动切换诊断模式 （Read 错误日志 → 搜调用链 → 最小复现），禁止继续盲目 Edit。Agent 的工程化，就该把"什么时候该停下来想"写进机制，而不是指望模型自觉。
什么情况下应该让代码执行计算或数据处理，而不是让模型直接给出答案？
四条判断标准：
正确性可被确定性验证 ——骑士谜题可穷举、数学题可用 sympy 对比。让代码判定，模型只负责翻译。
计算量超出模型"心算"能力 ——十位数乘法、百万行统计、蒙特卡洛一万次、矩阵分解。模型算会错，numpy 不会。
需要可重复、可审查 ——口头回答无法复现；.py 脚本谁跑都一样。金融、医疗、审计场景这条是硬要求。
数据在文件系统里 ——让模型 Read 一份 CSV 再"分析"，容易漏行错算；让它写 pandas 代码去读、清洗、计算，才是正路。
一句话总结：模型做理解和翻译，代码做判定和计算 ——实验一 12/12 的准确率就是这套分工给出的。
总结与反思
四条核心收获
1\. 代码是"能创造新工具的工具"。 通用 Python + 通用库就能现场为每道题造一个针对性求解程序。预装专用工具的路线走不远，代码的通用性碾压专用工具。
2\. 分工：模型管理解，代码管判定。 实验一 100% 的准确率来自"模型翻译 + 求解器穷举"的分工，正确性与模型强弱脱钩。这是整章最打动我的设计思想。
3\. 文件系统是外部记忆。 上下文易失，文件系统持久。按需 Read/Grep 比全量塞上下文高明得多，中间产物落盘让多轮迭代有抓手。
4\. 闭环是灵魂，但闭环的终点必须是人或测试。 Read → Think → Edit → Execute → Observe 防止 Agent 幻想执行结果；而"模型停止调工具"只是它的自我声明—— 真正的验收永远在闭环外面。这次 155 → 161 的排错，就是我给这个闭环补上的外部验收。
实验边界（如实记录）
没有模型 API Key，本章所有"LLM 把自然语言翻译成约束/代码"的在线环节没有实测—— code-for-logic 的 both 模式、coding-agent 的端到端编码任务都没跑。 离线部分证明了机制 的正确性，但"翻译质量"这个变量完全没有覆盖。 另外 README 记录的正式实验负结果（LLM 辅助代码路径 39.3% vs 纯思考 75.0%）也提醒： 翻译本身容易错，翻译错了求解器也救不回来。Agent 的真正价值不在"一次写对"，而在 "能反复迭代直到满足验收条件" 的工程能力——这一点，我在自己的排错里算是用人力模拟了一遍。
最后一句感想：
学这章之前我以为 Agent 的门槛是"模型够聪明"，学完发现门槛是"工程闭环够扎实"—— 工具边界、结果回灌、失败归因、外部验收，每一环都是工程问题。 模型只是循环里的那个"Think"，其他四步全是工程。
Sources
Chapter 5 主 README — 本章 16 个配套实验的索引与正式验收记录（含负结果）。
code-for-logic/demo.py --mode solver — 本次运行的离线求解入口（12/12 输出见上文）。
code-for-logic/csp_solver.py — eval_stmt() 递归求值 + solve() 双条件约束建模。
coding-agent/agent.py — CodingAgent.run() 循环：流式 LLM 调用 + 工具执行 + 结果回灌。
coding-agent/tools/write_tool.py、edit_tool.py、multi_edit_tool.py — lint 根因定位与修复（python3 → sys.executable）。
coding-agent/tests/ — pytest 修复前后两次全量输出（10 failed/155 passed → 4 failed/161 passed）。
python-constraint 库 — 离线 CSP 求解引擎。
