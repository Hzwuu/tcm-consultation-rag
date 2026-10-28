from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DETAILS_PATH = PROJECT_ROOT / "data" / "tcm_syndrome_details_v2_source_backed.csv"


NEW_ROWS = [
    {
        "id": "TCMD013",
        "name": "心阴虚证",
        "category": "心系证候",
        "core_symptoms": "心悸；失眠多梦；五心烦热；潮热；盗汗；两颧发红；咽干",
        "tongue_pulse": "舌红少津或少苔；脉细数",
        "differentiation_points": "以心悸、失眠多梦等心系表现与阴虚内热表现并见为要点；需与心血虚的面色淡白、唇舌色淡、脉细弱鉴别",
        "common_triggers": "久病耗伤阴血；失血；阴血生成不足；情志不遂、气火内郁",
        "follow_up_questions": "是否心悸？是否失眠多梦？是否五心烦热或潮热盗汗？是否咽干口燥？舌苔是否偏少？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "避免熬夜和过度劳心；若心悸明显、胸痛、晕厥需及时就医",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行用药；心悸胸闷需排除心血管急症",
        "red_flags": "胸痛；晕厥；呼吸困难；心悸持续加重",
        "retrieval_keywords": "心阴虚；心悸；失眠；五心烦热；潮热；盗汗；舌红少津；脉细数",
        "source_note": "基于中国医药信息查询平台心阴虚词条和《中医诊断学》心与小肠病辨证整理；处方和调理建议待审核",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "中国医药信息查询平台《心阴虚》；《中医诊断学》心与小肠病辨证",
        "source_url": "https://m.dayi.org.cn/disease/1155691；https://www.zysj.com.cn/lilunshuji/zhenduanxue/2735.html",
        "source_locator": "中国医药信息查询平台“心阴虚”诊断/鉴别诊断；中医世家“心血虚与心阴虚证”",
        "evidence_note": "来源列出心悸、失眠多梦、潮热、盗汗、五心烦热、颧红、咽干、舌红少苔/少津、脉细数等表现",
    },
    {
        "id": "TCMD014",
        "name": "肾气虚证",
        "category": "肾系证候",
        "core_symptoms": "神疲乏力；腰膝酸软；小便频数而清；白带清稀",
        "tongue_pulse": "舌质淡；脉弱",
        "differentiation_points": "以肾虚相关腰膝酸软、小便频数清长或固摄减退表现与气虚表现并见为要点；一般不突出畏寒肢冷等阳虚寒象",
        "common_triggers": "久病体虚；年高肾亏；劳倦；先天不足",
        "follow_up_questions": "是否腰膝酸软？是否小便频数且清长？是否神疲乏力？女性是否白带清稀？是否明显畏寒肢冷以帮助鉴别肾阳虚？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "症状持续或伴尿痛、血尿、发热时应线下就医评估",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行补肾用药；尿路症状需排除感染、肾脏或泌尿系统疾病",
        "red_flags": "血尿；发热腰痛；尿量明显减少；水肿；意识异常",
        "retrieval_keywords": "肾气虚；神疲乏力；腰膝酸软；小便频数；白带清稀；舌淡；脉弱",
        "source_note": "基于中医世家《中医内科学》虚劳分证论治中“肾气虚”症状整理；处方信息未写入默认建议",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "《中医内科学》虚劳 - 中医世家",
        "source_url": "https://www.zysj.com.cn/lilunshuji/neikexue/76-8-6.html",
        "source_locator": "虚劳“气虚·肾气虚”条",
        "evidence_note": "来源列出神疲乏力、腰膝酸软、小便频数而清、白带清稀、舌质淡、脉弱等表现",
    },
    {
        "id": "TCMD015",
        "name": "肾阳虚证",
        "category": "肾系证候",
        "core_symptoms": "腰膝酸软冷痛；畏寒肢冷；下肢尤甚；神疲乏力；小便清长或夜尿多；性欲减退或生殖功能减退相关表现",
        "tongue_pulse": "舌淡胖；苔白或白腻有齿痕水滑；脉沉细无力",
        "differentiation_points": "以腰膝酸软冷痛、畏寒肢冷、小便清长或夜尿多等肾虚寒象为要点；与肾气虚相比寒象更明显",
        "common_triggers": "年高体衰；久病；房劳过度；阳虚体质",
        "follow_up_questions": "是否腰膝冷痛？是否怕冷、手脚冷且下肢更明显？是否夜尿多或小便清长？是否长期疲乏？是否有水肿或呼吸困难？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "若出现明显水肿、尿量减少、气喘或胸闷，应及时就医",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行服用温补类药物；合并高血压、肾病、心血管病时尤其需要医生评估",
        "red_flags": "水肿明显；尿量明显减少；呼吸困难；胸痛；晕厥",
        "retrieval_keywords": "肾阳虚；腰膝酸软冷痛；畏寒肢冷；夜尿多；小便清长；舌淡胖；脉沉细",
        "source_note": "基于中国医药信息查询平台肾阳虚词条和肾阴虚/肾阳虚鉴别问答整理；处方信息未写入默认建议",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "中国医药信息查询平台《肾阳虚》；《肾阴虚和肾阳虚怎么判断》",
        "source_url": "https://m.dayi.org.cn/disease/1157788；https://m.dayi.org.cn/qa/347893.html",
        "source_locator": "“肾阳虚”诊断依据；“肾阴虚和肾阳虚怎么判断”症状/脉诊/舌诊",
        "evidence_note": "来源列出腰膝酸软冷痛、畏寒肢冷、小便清长或夜尿多、舌淡胖、苔白、脉沉细无力等",
    },
    {
        "id": "TCMD016",
        "name": "肾阴虚证",
        "category": "肾系证候",
        "core_symptoms": "腰膝酸痛或酸软；眩晕耳鸣；失眠多梦；五心烦热；潮热盗汗；咽干颧红；小便短黄或便干",
        "tongue_pulse": "舌红少津；少苔或无苔；脉细数",
        "differentiation_points": "以肾系腰膝、耳鸣眩晕等表现与阴虚内热表现并见为要点；与肾阳虚的畏寒肢冷、小便清长相鉴别",
        "common_triggers": "久病伤肾；禀赋不足；房劳过度；温燥耗阴",
        "follow_up_questions": "是否腰膝酸软或酸痛？是否耳鸣眩晕？是否五心烦热、潮热或盗汗？是否咽干颧红？大便是否偏干？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "若伴持续发热、消瘦明显、咯血、血尿或严重失眠，应就医评估",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行长期服用滋补类药物；需排除内分泌、感染、肾脏等相关问题",
        "red_flags": "咯血；血尿；体重明显下降；持续发热；严重失眠伴情绪危机",
        "retrieval_keywords": "肾阴虚；腰膝酸软；眩晕耳鸣；五心烦热；潮热盗汗；咽干颧红；舌红少津；脉细数",
        "source_note": "基于中国医药信息查询平台肾阴虚/肾阳虚鉴别问答和虚劳词条整理；处方信息未写入默认建议",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "中国医药信息查询平台《肾阴虚和肾阳虚怎么判断》；《虚劳》",
        "source_url": "https://m.dayi.org.cn/qa/347893.html；https://m.dayi.org.cn/disease/1155918",
        "source_locator": "“肾阴虚和肾阳虚怎么判断”症状/脉诊/舌诊；虚劳“肾阴虚证”",
        "evidence_note": "来源列出五心烦热、耳鸣、眩晕、盗汗、咽干颧红、舌红少津、少苔或无苔、脉细数等",
    },
    {
        "id": "TCMD017",
        "name": "脾阳虚证",
        "category": "脾系证候",
        "core_symptoms": "腹痛隐隐；喜温喜按；大便溏稀；腹胀有冷感；口淡不渴；食欲不佳；肢体不温或怕冷",
        "tongue_pulse": "舌淡胖；苔白腻水滑；脉沉细",
        "differentiation_points": "以脾运失健与寒象并见为要点；与脾气虚相比，腹痛喜温、畏寒肢冷、便溏清稀等寒象更突出",
        "common_triggers": "脾气虚渐进；过食生冷；寒邪直中；肾阳不足影响脾阳",
        "follow_up_questions": "是否腹痛喜温喜按？大便是否溏稀或夹未消化食物？是否怕冷肢冷？食欲如何？是否小便清长或浮肿？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "腹痛明显、持续腹泻、便血、发热或脱水表现需及时就医",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行长期温补；腹泻腹痛需排除感染、炎症或消化系统疾病",
        "red_flags": "便血；黑便；持续高热；脱水；剧烈腹痛；体重明显下降",
        "retrieval_keywords": "脾阳虚；腹痛喜温喜按；大便溏稀；腹胀；畏寒肢冷；舌淡胖；苔白腻；脉沉细",
        "source_note": "基于中国医药信息查询平台脾阳虚词条和《中医诊断学》脾病辨证整理；处方信息未写入默认建议",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "中国医药信息查询平台《脾阳虚》；《中医诊断学》脾病辨证",
        "source_url": "https://m.dayi.org.cn/disease/1159754；https://www.zysj.com.cn/lilunshuji/zhenduanxue/92-4-3_group.html",
        "source_locator": "中国医药信息查询平台“脾阳虚”诊断依据；中医世家“脾阳虚证”",
        "evidence_note": "来源列出腹痛隐隐、喜温喜按、大便溏稀、腹胀冷感、肢体不温、舌淡胖、苔白腻水滑、脉沉细等",
    },
    {
        "id": "TCMD018",
        "name": "肺阴虚证",
        "category": "肺系证候",
        "core_symptoms": "干咳少痰；咽燥；声音嘶哑或失音；痰中带血或咯血；潮热；盗汗；面色潮红；形体消瘦",
        "tongue_pulse": "舌红少津；苔少；脉细数",
        "differentiation_points": "以肺失清润的干咳少痰、咽燥声嘶与阴虚内热表现并见为要点；需与燥邪犯肺的外感表证鉴别",
        "common_triggers": "久咳伤肺；热病耗阴；虚劳；阴津亏耗",
        "follow_up_questions": "是否干咳少痰？是否咽干或声音嘶哑？是否痰中带血？是否潮热盗汗？是否近期有外感发热？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "咯血、呼吸困难、胸痛、持续发热或消瘦明显需及时就医",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行止咳或滋补用药；咯血和长期咳嗽需排除肺部疾病",
        "red_flags": "咯血；呼吸困难；胸痛；持续发热；体重明显下降",
        "retrieval_keywords": "肺阴虚；干咳少痰；咽燥；声音嘶哑；痰中带血；潮热盗汗；舌红少津；脉细数",
        "source_note": "基于中国医药信息查询平台虚劳词条和中医世家《中医内科学》肺病证整理；处方信息未写入默认建议",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "中国医药信息查询平台《虚劳》；《中医内科学》肺病证 - 中医世家",
        "source_url": "https://m.dayi.org.cn/disease/1155918；https://www.zysj.com.cn/lilunshuji/neikexue/76-3-0.html",
        "source_locator": "虚劳“肺阴虚证”；中医世家“肺阴亏耗”",
        "evidence_note": "来源列出干咳少痰、咽燥、失音/声嘶、咯血、潮热盗汗、舌红少津、脉细数等",
    },
    {
        "id": "TCMD019",
        "name": "肝阴虚证",
        "category": "肝系证候",
        "core_symptoms": "头痛或头晕；眩晕耳鸣；两目干涩；目干畏光或视物不明；面部潮红或烘热；胁肋不适；急躁易怒；肢体麻木或筋脉拘急",
        "tongue_pulse": "舌干红或舌红少津；脉弦细数",
        "differentiation_points": "以肝系头目、目干、胁肋和筋脉失养表现与阴虚表现并见为要点；可发展或兼见肝阳上亢",
        "common_triggers": "慢性疾病耗伤肝阴；热病伤阴；情志不遂气郁化火；血虚不能养肝",
        "follow_up_questions": "是否眩晕耳鸣？眼睛是否干涩畏光？是否胁肋不适？是否五心烦热或潮热盗汗？是否急躁易怒或肢体麻木？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "若出现剧烈头痛、肢体无力麻木、言语不清、视物异常，应及时就医",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行用药；头痛眩晕或神经系统症状需排除急症",
        "red_flags": "突发剧烈头痛；言语不清；单侧肢体无力；意识异常；视力突然改变",
        "retrieval_keywords": "肝阴虚；头晕；眩晕耳鸣；目干；视物不明；胁肋；急躁易怒；舌红少津；脉弦细数",
        "source_note": "基于中国医药信息查询平台虚劳词条和中医世家《中医诊断学》肝与胆病辨证整理；处方信息未写入默认建议",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "中国医药信息查询平台《虚劳》；《中医诊断学》肝与胆病辨证",
        "source_url": "https://m.dayi.org.cn/disease/1155918；https://www.zysj.com.cn/lilunshuji/zhenduanxue/2734.html",
        "source_locator": "虚劳“肝阴虚证”；中医世家“肝阴虚证”",
        "evidence_note": "来源列出头痛、眩晕耳鸣、目干畏光/视物不明、急躁易怒、舌干红或舌红少津、脉弦细数等",
    },
    {
        "id": "TCMD020",
        "name": "肝阳上亢证",
        "category": "肝系证候",
        "core_symptoms": "头目胀痛；眩晕耳鸣；面红目赤；急躁易怒；失眠多梦；心悸健忘；腰膝酸软；头重脚轻",
        "tongue_pulse": "舌质红；苔薄黄、少苔或无苔；脉弦或弦细数",
        "differentiation_points": "以肝阳亢于上与肝肾阴亏于下并见为要点；头目胀痛、面红目赤、急躁易怒较突出",
        "common_triggers": "长期精神紧张；焦虑抑郁；强烈情绪刺激；长期劳累或熬夜；肝肾阴虚",
        "follow_up_questions": "是否头目胀痛或眩晕耳鸣？是否面红目赤、急躁易怒？是否失眠多梦？是否腰膝酸软、头重脚轻？近期是否长期熬夜或情绪压力大？",
        "care_advice": "生活建议需专业审核后补充",
        "diet_advice": "待专业审核",
        "lifestyle_advice": "突发剧烈头痛、胸痛、言语不清、肢体无力、血压极高等需立即就医",
        "prescription_reference": "待专业审核",
        "contraindications": "不建议自行降压或中药调理替代正规诊疗；头痛眩晕需关注血压和神经系统急症",
        "red_flags": "突发剧烈头痛；视物异常；言语不清；单侧肢体无力；胸痛；意识异常",
        "retrieval_keywords": "肝阳上亢；头目胀痛；眩晕耳鸣；面红目赤；急躁易怒；失眠多梦；腰膝酸软；舌红；脉弦",
        "source_note": "基于中国医药信息查询平台肝阳上亢问答和《中医诊断学》肝与胆病辨证整理；处方信息未写入默认建议",
        "review_status": "来源支撑临床表现；待中医专业审核",
        "last_updated": "2026-08-07",
        "source_title": "中国医药信息查询平台《如何判断是肝阳上亢》；《中医诊断学》肝与胆病辨证",
        "source_url": "https://m.dayi.org.cn/qa/359881.html；https://www.zysj.com.cn/lilunshuji/zhenduanxue/2734.html",
        "source_locator": "中国医药信息查询平台“如何判断是肝阳上亢”症状/舌脉；中医世家“肝阳上亢证”",
        "evidence_note": "来源列出头目胀痛、眩晕耳鸣、面红目赤、急躁易怒、失眠多梦、腰膝酸软、舌红、脉弦或弦细数等",
    },
]


def main() -> int:
    with DETAILS_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    fieldnames = list(rows[0].keys())
    existing_names = {row["name"] for row in rows}
    existing_ids = {row["id"] for row in rows}

    to_add = []
    for row in NEW_ROWS:
        if row["name"] in existing_names or row["id"] in existing_ids:
            continue
        to_add.append(row)

    with DETAILS_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows + to_add)

    print(f"added {len(to_add)} rows; total {len(rows) + len(to_add)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
