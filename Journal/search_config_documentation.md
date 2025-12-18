# 搜索配置文件说明文档

本文档详细说明 `search_config.json` 文件中各配置项的含义和用途，帮助开发者理解和维护搜索系统配置。

## 1. 概述

`search_config.json` 是系统搜索功能的配置文件，用于控制搜索匹配规则、权重计算和特殊处理逻辑。通过修改此配置文件，可以在不修改代码的情况下调整搜索结果的排序和匹配行为。

## 2. 配置字段说明

### 2.1 related_keywords

定义搜索系统中的主题关键词集合，用于识别特定主题的搜索内容。

```json
"related_keywords": {
    "camping": ["露营", "露地", "营地", "露营地", "露", "帐篷"]
}
```

- **camping**: 露营主题的相关关键词列表
  - 这些关键词用于判断搜索是否与露营主题相关
  - 当搜索内容包含这些关键词时，可能会触发特殊的搜索逻辑或权重调整

### 2.2 similarity_thresholds

定义模糊匹配的相似度阈值，控制模糊匹配的严格程度。

```json
"similarity_thresholds": {
    "default": 0.7,
    "special_topic": 0.6
}
```

- **default**: 默认相似度阈值（0.7）
  - 适用于一般搜索场景的模糊匹配判断标准
  - 只有当文本相似度高于此值时，才会认为是相关匹配
- **special_topic**: 特殊主题相似度阈值（0.6）
  - 适用于特殊主题（如露营）的模糊匹配判断标准
  - 阈值较低，目的是提高相关内容的召回率

### 2.3 weight_config

定义不同匹配类型的权重配置，影响搜索结果的排序。权重越高，对应匹配类型在排序中的影响越大。

#### 2.3.1 default

默认情况下的权重设置，适用于大多数搜索场景。

##### 2.3.1.1 标题相关权重

```json
"title_exact_match": 100,        // 标题完全匹配的权重
"title_contains": 50,            // 标题包含关键词的权重
"title_position_weight": 30,     // 标题中关键词位置权重基数
"title_position_factor": 2,      // 标题中关键词位置权重衰减因子
"title_similarity": 50           // 标题模糊匹配的权重
```

- **title_exact_match**: 标题完全匹配时的权重值
- **title_contains**: 标题包含关键词时的权重值
- **title_position_weight**: 用于计算标题中关键词位置对权重的影响
- **title_position_factor**: 位置权重的衰减因子，位置越靠前权重越高
- **title_similarity**: 标题与关键词模糊匹配时的权重值

##### 2.3.1.2 地址相关权重

```json
"address_contains": 20,          // 地址包含关键词的权重
"address_position_weight": 10,   // 地址中关键词位置权重基数
"address_position_factor": 0.5,  // 地址中关键词位置权重衰减因子
"address_similarity": 20         // 地址模糊匹配的权重
```

- **address_contains**: 地址包含关键词时的权重值
- **address_position_weight**: 用于计算地址中关键词位置对权重的影响
- **address_position_factor**: 地址中位置权重的衰减因子
- **address_similarity**: 地址与关键词模糊匹配时的权重值

##### 2.3.1.3 内容相关权重

```json
"content_contains_base": 5,      // 内容包含关键词的基础权重
"content_contains_factor": 2,    // 内容包含关键词的次数加成因子
"content_similarity": 10         // 内容模糊匹配的权重
```

- **content_contains_base**: 内容包含关键词时的基础权重
- **content_contains_factor**: 用于计算关键词在内容中出现次数的加成，出现次数越多权重越高
- **content_similarity**: 内容与关键词模糊匹配时的权重值

##### 2.3.1.4 昵称相关权重

```json
"nickname_exact_match": 80,      // 昵称完全匹配的权重
"nickname_contains": 40,         // 昵称包含关键词的权重
"nickname_position_weight": 10,  // 昵称中关键词位置权重基数
"nickname_position_factor": 0.5, // 昵称中关键词位置权重衰减因子
"nickname_similarity": 40,       // 昵称模糊匹配的权重
"nickname_multi_keywords": 20,   // 多关键词在昵称中匹配的权重
"nickname_multi_keywords_similarity": 20 // 多关键词在昵称中模糊匹配的权重
```

- **nickname_exact_match**: 昵称完全匹配时的权重值
- **nickname_contains**: 昵称包含关键词时的权重值
- **nickname_position_weight**: 用于计算昵称中关键词位置对权重的影响
- **nickname_position_factor**: 昵称中位置权重的衰减因子
- **nickname_similarity**: 昵称与关键词模糊匹配时的权重值
- **nickname_multi_keywords**: 多个关键词在昵称中匹配时的权重值
- **nickname_multi_keywords_similarity**: 多个关键词与昵称模糊匹配时的权重值

#### 2.3.2 special_topic

特殊主题情况下的权重设置，适用于特定主题的搜索（如露营主题）。

```json
"special_topic": {
    "title_similarity": 70,    // 特殊主题下标题模糊匹配的权重
    "address_similarity": 30,  // 特殊主题下地址模糊匹配的权重
    "content_similarity": 15   // 特殊主题下内容模糊匹配的权重
}
```

- **title_similarity**: 特殊主题下标题模糊匹配的权重（高于默认值）
- **address_similarity**: 特殊主题下地址模糊匹配的权重（高于默认值）
- **content_similarity**: 特殊主题下内容模糊匹配的权重（高于默认值）

### 2.4 special_mappings

定义特殊关键词的映射关系，用于处理拼写错误或发音相似的搜索词。

```json
"special_mappings": {
    "露营能": "露营地"
}
```

- 当用户搜索"露营能"时，系统会将其映射为"露营地"进行搜索
- 用于提高用户输入不规范时的搜索体验

### 2.5 special_bonus

定义特殊关键词的额外加分规则，对特定关键词的匹配结果给予额外权重加成。

```json
"special_bonus": {
    "露营能": 80
}
```

- 当搜索内容包含"露营能"关键词时，匹配结果将获得80分的额外加分
- 用于突出显示特定内容或处理特殊业务需求

## 3. 配置修改指南

修改配置文件时，请遵循以下原则：

1. **保持格式正确**：确保JSON格式正确，避免语法错误
2. **权重调整**：调整权重值时，请考虑各权重间的相对关系
3. **阈值设置**：模糊匹配阈值过低会导致不相关结果增多，过高则可能导致相关结果被过滤
4. **测试验证**：修改配置后，请进行充分测试，确保搜索结果符合预期
5. **备份**：修改前请备份原配置文件，以便出现问题时恢复

## 4. 示例场景

### 4.1 提高标题匹配的重要性

如果需要让标题匹配在搜索结果中占更大比重，可以增加标题相关权重：

```json
"title_exact_match": 150,  // 从100提高到150
"title_contains": 80,      // 从50提高到80
```

### 4.2 调整模糊匹配的敏感度

如果发现模糊匹配结果不够准确，可以提高默认阈值：

```json
"default": 0.8  // 从0.7提高到0.8
```

### 4.3 添加新的关键词映射

如需添加新的关键词映射关系：

```json
"special_mappings": {
    "露营能": "露营地",
    "露菅": "露营"  // 新增映射
}
```
