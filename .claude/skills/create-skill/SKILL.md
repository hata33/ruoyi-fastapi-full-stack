---
name: create-skill
description: 创建新的 Claude Code skill
---

# 创建新的 Claude Code Skill

帮助用户快速创建符合规范的 Claude Code skill。

## 执行步骤

1. **询问用户信息**（使用 AskUserQuestion 工具）：
   - skill 名称（英文，小写，用连字符分隔）
   - skill 功能描述（一句话说明）
   - 是否需要帮助编写内容

2. **创建目录结构**：
   ```
   .claude/skills/<skill-name>/SKILL.md
   ```

3. **生成 SKILL.md 模板**，包含：
   - YAML frontmatter（name、description）
   - 技能说明
   - 执行步骤
   - 使用示例（可选）

4. **告知用户**：
   - 文件创建位置
   - 如何使用新 skill

## SKILL.md 模板格式

```markdown
---
name: <skill-name>
description: <一句话描述>
---

# <技能标题>

<技能详细说明>

## 执行步骤

1. <步骤1>
2. <步骤2>

## 注意事项

<重要提示>
```

## 示例

用户输入：创建一个名为 "format-code" 的格式化代码 skill

输出：
```
✓ 已创建: .claude/skills/format-code/SKILL.md

使用方式: /format-code
```
