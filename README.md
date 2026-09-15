# output-format-guarantee

一个用于 **保证 LLM 输出格式绝对正确** 的 Agent Skill（contact-json）：将用户输入的姓名、地址、电话格式化为 JSON，并在输出前通过 pydantic 模型强制验证，不通过则修正后重新验证，直到通过为止——只有验证通过的 JSON 才会交付给用户。

## 输出格式保证的四个要点

### 1. pydantic 模型是格式的唯一权威（Single Source of Truth）

字段规则（类型、长度、字符集）不写死在自然语言指令里，而是定义在 `scripts/validate_contact.py` 的 pydantic 模型中。自然语言描述可能含糊、会被模型"自由发挥"，而代码定义的 schema 是确定性的、可执行的契约。当指令与验证器冲突时，以验证器为准。

### 2. 验证先行：没有通过验证的输出不得交付

Skill 的核心契约是：**任何 JSON 在展示给用户之前，必须先实际运行验证脚本并通过**。即使草稿"看起来没问题"也不能跳过验证——LLM 手写 JSON 容易漂移（缺引号、键名错误、空字段、非法字符），验证成本极低，而保证正是这个 skill 存在的意义。

### 3. 失败 → 修正 → 重验的闭环

验证失败时，脚本会输出**机器可读、人类可懂**的错误清单：哪个字段、什么问题、实际收到什么值，例如：

```
VALIDATION FAILED:
  - name: Value error, must not be empty or whitespace only (got: '  ')
  - phone: Value error, invalid phone: ... (got: 'abc#123')
```

模型据此精确修正后再次运行验证，循环往复，直到脚本输出 `VALID` 并以退出码 0 结束。这把"格式正确"从主观判断变成了**可机械判定的通过/失败信号**（exit code）。

### 4. 交付的就是验证器认可的那份输出

最终交付给用户的不是模型手里的草稿，而是验证脚本打印出的**规范化 JSON**（pydantic 清洗、去空格、序列化后的结果）。保证输出与验证通过的内容逐字节一致，杜绝"验的是一份、给的是另一份"的偏差。

## 工作流程

```
用户输入（姓名/地址/电话）
        │
        ▼
  提取字段，起草 JSON
        │
        ▼
  运行 validate_contact.py ──失败──► 读取错误清单，修正 JSON ──┐
        │                                                    │
     通过 (exit 0) ◄─────────────────────────────────────────┘
        │
        ▼
  输出验证器打印的规范化 JSON
```

## 字段规则

| 字段 | 规则 |
|------|------|
| `name` | 非空字符串，≤100 字符，自动去首尾空白 |
| `address` | 非空字符串，≤300 字符，自动去首尾空白 |
| `phone` | 5–25 位，仅允许数字及 `+ - ( ) .` 和空格，必须包含至少一位数字 |

完整规则以 `scripts/validate_contact.py` 中的 `ContactInfo` 模型为准。

## 文件结构

```
├── SKILL.md                    # Skill 定义：触发条件 + 验证工作流
├── scripts/
│   └── validate_contact.py     # pydantic 验证器（格式的唯一权威）
└── README.md
```

## 依赖与使用

依赖：Python 3 + pydantic v2。

验证器可独立使用：

```bash
# 通过 stdin
echo '{"name": "张三", "address": "北京市朝阳区建国路1号", "phone": "138-0000-0000"}' \
  | python3 scripts/validate_contact.py

# 通过文件
python3 scripts/validate_contact.py contact.json
```

- 验证通过：打印 `VALID` + 规范化 JSON，退出码 0
- 验证失败：打印逐字段错误清单，退出码 1

作为 Agent Skill 使用时，将整个目录放入 skills 目录（如 `~/.agents/skills/contact-json/`），Agent 会在用户要求"把联系信息输出成 JSON"时自动触发并执行上述验证闭环。

## 为什么这个模式是通用的

这个 skill 演示的模式可以推广到任何对输出格式有严格要求的场景：**用代码定义 schema（pydantic / JSON Schema 等），让模型在交付前实际运行验证器，失败后依据结构化错误信息迭代修正，直到 exit code 为 0**。LLM 负责生成与修正，确定性代码负责裁决——格式保证因此不再依赖模型"自觉性"。

## License

MIT
