"""
演示 kk11（5人链式+计数）谜题的完整求解路径：
  自然语言 → 结构化DSL → 双条件约束 → python-constraint 穷举求解

这条路径直接回答了自测题3：代码如何成为"创造新工具的工具"
"""
import sys
sys.path.insert(0, 'code-for-logic')
from constraint import Problem

# ============================================================
# 第 1 步：原始自然语言题面
# ============================================================
print("=" * 60)
print("【kk11 题面】5 人链式 + 计数谜题")
print("=" * 60)
print("A 说：B 是骑士。")
print("B 说：C 是无赖。")
print("C 说：D 是骑士。")
print("D 说：E 是无赖。")
print("E 说：我们五人当中至少有两个骑士。")
print()

# ============================================================
# 第 2 步：把每句话翻译成结构化 DSL
# ============================================================
print("【结构化 DSL 翻译】")
print("-" * 60)
names = ['A', 'B', 'C', 'D', 'E']
structs = {
    "A": ["is", "B", "knight"],        # A 声称 B 是骑士
    "B": ["is", "C", "knave"],         # B 声称 C 是无赖
    "C": ["is", "D", "knight"],        # C 声称 D 是骑士
    "D": ["is", "E", "knave"],         # D 声称 E 是无赖
    "E": ["count", "knight", ">=", 2], # E 声称骑士总数 >= 2
}

for name in names:
    stmt = structs[name]
    print(f"  {name}: {stmt}")
print()

# ============================================================
# 第 3 步：建立变量（每人是骑士 True / 无赖 False）
# ============================================================
print("【变量定义】")
print("-" * 60)
print("每人一个布尔变量，True = 骑士（说真话），False = 无赖（说假话）")
print(f"总组合数 = 2^5 = {2**len(names)} 种")
print()

# ============================================================
# 第 4 步：关键建模规则 —— 双条件约束
# ============================================================
print("【核心约束规则】")
print("-" * 60)
print("对每位说话者 X，加一条双条件约束：")
print("    t[X] == (X 说的话为真)")
print()
print("这不是把 X 的话当作硬约束，而是说：")
print("  如果 X 是骑士(True)，那他的话必须为真；")
print("  如果 X 是无赖(False)，那他的话必须为假。")
print()

# ============================================================
# 第 5 步：手工写出约束程序
# ============================================================
print("【翻译成 python-constraint 代码】")
print("-" * 60)
print('''
from constraint import Problem
p = Problem()

# 变量
for name in ['A', 'B', 'C', 'D', 'E']:
    p.addVariable(name, [True, False])

# 双条件约束：t[speaker] == (speaker 的话为真)
p.addConstraint(lambda a, b: a == (b == True), ['A', 'B'])  # A 说 "B 是骑士"
p.addConstraint(lambda b, c: b == (c == False), ['B', 'C']) # B 说 "C 是无赖"
p.addConstraint(lambda c, d: c == (d == True), ['C', 'D'])  # C 说 "D 是骑士"
p.addConstraint(lambda d, e: d == (e == False), ['D', 'E'])  # D 说 "E 是无赖"

# E 的话：骑士数 >= 2（涉及所有变量）
p.addConstraint(
    lambda a, b, c, d, e: e == ((a + b + c + d + e) >= 2),
    ['A', 'B', 'C', 'D', 'E']
)

# 求解并打印
solutions = p.getSolutions()
''')

# ============================================================
# 第 6 步：实际求解
# ============================================================
print("=" * 60)
print("【实际求解结果】")
print("=" * 60)

p = Problem()
for name in names:
    p.addVariable(name, [True, False])

p.addConstraint(lambda a, b: a == (b == True), ['A', 'B'])
p.addConstraint(lambda b, c: b == (c == False), ['B', 'C'])
p.addConstraint(lambda c, d: c == (d == True), ['C', 'D'])
p.addConstraint(lambda d, e: d == (e == False), ['D', 'E'])
p.addConstraint(
    lambda a, b, c, d, e: e == ((a + b + c + d + e) >= 2),
    ['A', 'B', 'C', 'D', 'E']
)

solutions = p.getSolutions()
print(f"共找到 {len(solutions)} 个解")
for i, sol in enumerate(solutions):
    result = {n: ('骑士' if sol[n] else '无赖') for n in names}
    print(f"  解 {i+1}: {result}")

# 验证
expected = {'A': True, 'B': True, 'C': False, 'D': False, 'E': True}
actual = solutions[0]
match = all(actual[n] == expected[n] for n in names)
print(f"\n与金标准对比: {'✓ 完全匹配' if match else '✗ 不匹配'}")

# ============================================================
# 第 7 步：回答自测题 3 —— 代码是创造新工具的工具
# ============================================================
print()
print("=" * 60)
print("【自测题 3 的回答】代码是'创造新工具的工具'")
print("=" * 60)
print()
print("这个谜题的求解过程本身就是最好的例子：")
print()
print("  1. 我没有预装一个'骑士无赖求解器'专用工具。")
print("  2. 模型用通用语言 Python + 通用库 python-constraint,")
print("     现场创造了一个针对这道题的求解工具。")
print("  3. 同样的 python-constraint, 换一组约束代码就能解另一道题。")
print("")
print("对比：如果预先提供专用工具 solve_knights_and_knaves(),")
print("      那它只对这类题有用；")
print("      而写代码本身, 可以解决任何能被形式化的问题。")
print()
print("非编程任务例子：帮朋友分析投资组合风险。")
print("  - 不写代码: 我凭印象告诉你哪些股票涨跌了")
print("  - 写代码: 我用 Python + pandas 拉取股价数据,")
print("           计算各股票的协方差矩阵, 跑蒙特卡洛模拟,")
print("           量化组合的 VaR (在险价值), 给出客观数值")
print("  -> 代码让'风险评估'从主观印象变成了可重复的计算工具")
