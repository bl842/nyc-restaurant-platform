# 明天会议怎么使用这份材料

先读两页英文简报，再打开 HTML 原型跑一次演示。你需要能解释项目解决的问题、每个数字代表什么，以及哪些问题还没有数据支持。暂时不用背完整代码。

## 开场可以这样说

I have narrowed the project to a restaurant market exploration platform for both prospective owners and existing operators in New York City. Users can start with a cuisine, a location, or no fixed idea. I have prepared six public sources and a first Python and SQL pipeline, together with a small interactive prototype. The first version focuses on restaurant supply, retail asking-rent context and delivery economics. I would like to use this meeting to confirm the scope, choose the BI tool and agree on the next demand-side dataset.

## 三分钟演示顺序

打开原型，先展示 “I am still exploring”，解释全市概览中的数字是行政记录里的餐饮场所供给。点击 “I have a cuisine”，示例选择 Chinese，然后选 Queens：数量应为 757。点击 “I have a location”，展示 Manhattan 的菜系构成。这样三个不同输入都进入了同一套比较流程。

进入 Delivery trends，保持 Q4 2024 和 Q4 2025，指出配送量增长 18.3%，但平均订单金额扣掉商家平台费后的金额只增加约 0.8%。需要明确，这个金额还没有扣食材、人工、包装和租金，不能称为利润。统计还包括部分非餐饮配送。

进入 Rent comparisons，把面积从 1000 改成 2000 平方英尺，展示成本如何随假设变化。Times Square 与 Financial District 的中位挂牌租金差约 6.6 倍，但这是零售商铺挂牌参考，不代表某一家可用餐馆铺位的实际报价。

## 需要在会议上确认的事

确认第一版是否接受“帮助比较和缩小研究范围”的定位，以及导师希望先看到 Tableau 还是 Power BI。确认网站最终应是公开网页、嵌入 BI 的仪表盘，还是可运行的本地演示。建议下周只新增一种需求侧指标，例如居民人口或交通活动，并先验证与现有地理单元能否对应。还需要确认实习项目最终按分析质量、商业可解释性、网站功能，还是其中某种组合来验收。

## 对方可能问到的问题

如果问为什么不用检查记录的行数数餐馆：同一家店的一次检查可能有多条违规记录。原始来源有 296,270 行，按 CAMIS 归并后是 31,469 个场所。现在的快照只包含活跃状态及部分申请者，所以不能用它重建历年的开关店趋势。

如果问菜系数量能否代表市场份额：目前代表供给数量的占比，不能代表营业收入份额。缺少菜系的信息有 3,860 条，图表保留这一点。更少的同类餐馆也可能意味着需求更少，因此尚未制作“最适合开店”的评分。

如果问为什么没有盈利预测：现有数据缺少单店营收、毛利、具体铺位条款和人工成本。第一版已经有可解释的比较模块，后续可以在取得这些输入后增加经营测算。

如果问你用什么工具：Python 读取 XLSX、HTML、PDF 和 API 数据，完成清洗；SQL 计算汇总、分母和同比；现在用本地 HTML 展示交互。清洗表可以导入 Tableau 或 Power BI，但这两个软件的原生工作簿尚未完成。

## 下周的可执行安排

第一天按会议反馈确定问题和指标，复核原始数据及菜系缺失。第二天在选定的一个 BI 工具中制作餐馆数量与菜系构成视图。第三天加入外卖或租金视图并核对 SQL 总数。第四天测试三类用户入口，补齐来源、时间范围和指标定义。第五天整理反馈和一页书面进度。若需求侧数据当天无法匹配，记录缺口，不延误已验证的供给视图。
