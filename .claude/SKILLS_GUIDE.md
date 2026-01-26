# Claude Code Skills 指南

## 什么是 Skills

Skills 是 Claude Code 的自定义功能模块，可以让 Claude 执行特定的任务。类似于给 Claude 添加新的"技能"。

## 目录结构

```
.claude/
└── skills/
    ├── skill-name-1/
    │   └── SKILL.md
    ├── skill-name-2/
    │   └── SKILL.md
    └── skill-name-3/
        └── SKILL.md
        └── (可选的脚本或资源文件)
```

**重要**：文件名必须是 `SKILL.md`（全大写）

## SKILL.md 格式

### 基本结构

```markdown
---
name: my-skill
description: 一句话描述这个技能做什么
---

# 技能标题

技能的详细说明...

## 执行步骤

1. 第一步做什么
2. 第二步做什么

## 其他章节

根据需要添加更多说明
```

### 必需部分

| 部分 | 说明 |
|------|------|
| YAML Frontmatter | 包含 `name` 和 `description` |
| 正文内容 | 告诉 Claude 如何执行这个技能 |

### 可选部分

- 使用示例
- 注意事项
- 配置选项
- 参数说明

## 使用 Skills

### 调用 Skill

```
/<skill-name> [参数]
```

### 示例

```bash
# 调用名为 add-comments 的 skill
/add-comments module_admin/service/user_service.py

# 调用名为 format-code 的 skill
/format-code
```

## 创建新 Skill

### 方法一：手动创建

1. 在 `.claude/skills/` 下创建新文件夹
2. 创建 `SKILL.md` 文件
3. 添加 YAML frontmatter 和指令内容

### 方法二：使用 create-skill

```bash
/create-skill
```

然后按提示输入：
- skill 名称
- 功能描述

## Skill 最佳实践

### ✅ 好的 Skill

- **专注单一任务**：每个 skill 只做一件事
- **指令清晰**：明确告诉 Claude 要做什么
- **有示例**：提供输入输出示例
- **适合重复任务**：用于频繁执行的操作

### ❌ 避免的 Skill

- 过于宽泛的任务
- 一次性操作
- 与现有 skill 重复

## 常见问题

**Q: Skill 不生效？**
A: 检查文件名是否为 `SKILL.md`（大写），YAML 格式是否正确

**Q: 如何调试 Skill？**
A: 在 SKILL.md 中添加更详细的日志输出指令

**Q: Skill 可以调用其他工具吗？**
A: 可以，在指令中明确说明需要使用哪些工具

## 参考资源

- [官方 Skills 仓库](https://github.com/anthropics/skills)
- [Agent Skills 官方文章](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Claude Code Skills 详解](https://mikhail.io/2025/10/claude-code-skills/)
