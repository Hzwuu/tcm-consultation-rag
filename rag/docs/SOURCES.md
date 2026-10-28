# 知识库来源登记

本项目第二阶段开始执行“来源优先”的知识库策略：没有可追溯来源的内容，不写入正式知识库；开放来源未给出完整临床表现的证候，只记录证名、证素和来源，不补写未经核实的症状。

## 已使用来源

### S003：中医世家《中医诊断学》

- 类型：在线中医理论资料
- URL：https://www.zysj.com.cn/lilunshuji/zhenduanxue/2735.html
- URL：https://www.zysj.com.cn/lilunshuji/zhenduanxue/92-4-3_group.html
- URL：https://www.zysj.com.cn/lilunshuji/zhenduanxue/2734.html
- 本项目使用范围：
  - 心气虚证、心阳虚证、心阳暴脱证的临床表现和鉴别。
  - 心脾两虚证、心肺气虚证等部分脏腑辨证内容。
  - 心阴虚证、脾阳虚证、肝阴虚证、肝阳上亢证等条目的交叉核验。
- 数据结构：
  - 记录来源标题、来源定位与审核字段，便于与教材版本和标准术语逐项对照。

### S006：中医世家《中医内科学》

- 类型：在线中医理论资料
- URL：https://www.zysj.com.cn/lilunshuji/neikexue/76-8-6.html
- URL：https://www.zysj.com.cn/lilunshuji/neikexue/76-3-0.html
- 本项目使用范围：
  - 肾气虚证、肺阴虚证等虚劳/肺系相关表现的来源核验。
- 数据组织：
  - 用于临床表现、舌脉和辨证点的结构化整理；处方和治疗建议不进入默认问诊输出。

### S004：济康堂中医研究院学习资料《中医诊断学》

- 类型：中医诊断学学习资料
- URL：https://www.jikangtang.com.cn/index.php/index/show?catname=xuexiziliao&id=183
- URL：https://www.jikangtang.com.cn/index.php/index/show?catname=xuexiziliao&id=184
- 本项目使用范围：
  - 气虚证、气陷证、血虚证等基础证候。
  - 心气虚、心血虚等心病辨证条目。
- 数据组织：
  - 学习资料用于原型知识库，并与教材、标准和审核字段共同展示。

### S005：中国医药信息查询平台

- 类型：医学信息平台词条
- URL：https://m.dayi.org.cn/symptom/600359
- URL：https://m.dayi.org.cn/disease/1155918
- URL：https://m.dayi.org.cn/disease/1155691
- URL：https://m.dayi.org.cn/disease/1157788
- URL：https://m.dayi.org.cn/disease/1159754
- URL：https://m.dayi.org.cn/qa/347893.html
- URL：https://m.dayi.org.cn/qa/359881.html
- 本项目使用范围：
  - 心肺气虚证词条。
  - 虚劳词条中的肺气虚、心气虚、脾气虚、肾气虚、肝血虚、心血虚等表现。
  - 心阴虚证、肾阳虚证、肾阴虚证、脾阳虚证、肝阳上亢证等常见证候的症状、舌脉和鉴别线索。
- 数据组织：
  - 平台词条作为二级来源，与典籍、教材和中医药标准共同组成来源信息。

### S001：主次症辨证法与证素辨证法辨别58个中医临床常见证结果的比较

- 类型：论文
- 期刊：《福建中医药》
- 年份：2025
- URL：https://cjournal.hep.com.cn/1000-338X/CN/PDF/10.13260/j.cnki.jfjtcm.2025.09006
- 本项目使用范围：
  - 表 2：58 个中医临床常见证的证名、主次症辨证法证素、证素辨证法证素、Jaccard 相似度。
  - 表 1：心气虚证、心阳虚证示例中的部分主症、次症、舌脉信息。
- 数据限制：
  - 表 2 提供证名、证素和相似度信息。
  - `tcm_syndrome_index_v2_source_backed.csv` 按该论文的字段范围保存证名、证素和来源定位。
  - 症状详情由来源详情库单独保存，两个数据层分别承担索引与详情功能。

## 论文引用的规范来源索引

论文正文提到其证名标准参考：

- GB/T 16751.2-2021《中医临床诊疗术语 第 2 部分：证候》
- 朱文锋《中医诊断学》
- 朱文锋《中医常见证候的辨病论治》

这些来源作为论文背景记录保存。知识库条目使用 `source_title`、`source_url` 和 `source_locator` 登记来源位置。

## 数据质量规则

1. 证名、证素、相似度必须能追溯到具体来源。
2. 症状、舌脉、方剂和调理建议不得凭经验扩写。
3. 没有来源支持的字段不进入结构化默认输出。
4. 每条记录必须包含 `review_status`，用于展示来源支撑与审核信息。
5. 医疗建议类字段必须带有来源字段和审核提示，并在界面中与候选依据分开显示。
