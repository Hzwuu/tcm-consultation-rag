#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define MAX_ILLNESS 15
#define MAX_SYMPTOM 200
#define MAX_ADVICE 200
#define MAX_PRESCRIPTION 100

// 中医病症结构体
typedef struct {
    char name[50];               // 病症名称
    char symptoms[MAX_SYMPTOM];  // 症状描述
    char advice[MAX_ADVICE];     // 调理建议
    char prescription[MAX_PRESCRIPTION]; // 参考方剂
} TCM_Illness;

// 初始化病症数据库
void initTCMDATABASE(TCM_Illness database[]) {
    // 1. 风热感冒
    strcpy_s(database[0].name, sizeof(database[0].name), "风热感冒");
    strcpy_s(database[0].symptoms, sizeof(database[0].symptoms), "发烧明显，怕风，喉咙红痛，流黄浓鼻涕，口渴想喝凉水");
    strcpy_s(database[0].advice, sizeof(database[0].advice), "多喝菊花茶、金银花露；饮食清淡，忌辛辣、羊肉");
    strcpy_s(database[0].prescription, sizeof(database[0].prescription), "银翘散");

    // 2. 风寒感冒
    strcpy_s(database[1].name, sizeof(database[1].name), "风寒感冒");
    strcpy_s(database[1].symptoms, sizeof(database[1].symptoms), "怕冷，发热轻，无汗，流清鼻涕，咳白稀痰，不想喝水");
    strcpy_s(database[1].advice, sizeof(database[1].advice), "喝热姜汤、葱白水发汗；注意保暖，忌生冷食物");
    strcpy_s(database[1].prescription, sizeof(database[1].prescription), "荆防败毒散");

    // 3. 胃火旺盛
    strcpy_s(database[2].name, sizeof(database[2].name), "胃火旺盛");
    strcpy_s(database[2].symptoms, sizeof(database[2].symptoms), "胃有烧灼感，口臭严重，牙龈肿痛，爱喝冷饮，大便干结");
    strcpy_s(database[2].advice, sizeof(database[2].advice), "立即停食辛辣油炸；多吃苦瓜、黄瓜、梨；严禁熬夜");
    strcpy_s(database[2].prescription, sizeof(database[2].prescription), "清胃散");

    // 4. 肝气郁结
    strcpy_s(database[3].name, sizeof(database[3].name), "肝气郁结");
    strcpy_s(database[3].symptoms, sizeof(database[3].symptoms), "情绪低落或烦躁，爱叹气，两胁或乳房胀痛，感觉喉咙有异物");
    strcpy_s(database[3].advice, sizeof(database[3].advice), "喝玫瑰花茶疏解情绪；适度运动；按摩膻中穴（两乳连线中点）");
    strcpy_s(database[3].prescription, sizeof(database[3].prescription), "柴胡疏肝散");

    // 5. 气血两虚
    strcpy_s(database[4].name, sizeof(database[4].name), "气血两虚");
    strcpy_s(database[4].symptoms, sizeof(database[4].symptoms), "面色苍白或萎黄，头晕心慌，浑身乏力，手脚发麻，记性差");
    strcpy_s(database[4].advice, sizeof(database[4].advice), "适当多吃红枣、桂圆、瘦肉；避免过度劳累；保证睡眠");
    strcpy_s(database[4].prescription, sizeof(database[4].prescription), "八珍汤");

    // 6. 湿热泄泻
    strcpy_s(database[5].name, sizeof(database[5].name), "湿热泄泻");
    strcpy_s(database[5].symptoms, sizeof(database[5].symptoms), "腹痛即泻，大便急迫、黄褐臭秽，肛门灼热，小便黄");
    strcpy_s(database[5].advice, sizeof(database[5].advice), "饮食清淡，喝薏米赤小豆水；忌肥甘厚味、酒和甜食");
    strcpy_s(database[5].prescription, sizeof(database[5].prescription), "葛根芩连汤");

    // 7. 心脾两虚
    strcpy_s(database[6].name, sizeof(database[6].name), "心脾两虚");
    strcpy_s(database[6].symptoms, sizeof(database[6].symptoms), "心慌失眠、多梦易醒，食欲不振，饭后腹胀，面色萎黄");
    strcpy_s(database[6].advice, sizeof(database[6].advice), "规律三餐，细嚼慢咽；睡前热水泡脚；避免思虑过度");
    strcpy_s(database[6].prescription, sizeof(database[6].prescription), "归脾汤");

    // 8. 肾阴亏虚
    strcpy_s(database[7].name, sizeof(database[7].name), "肾阴亏虚");
    strcpy_s(database[7].symptoms, sizeof(database[7].symptoms), "腰膝酸软，头晕耳鸣，手脚心发热，夜间盗汗，口干咽燥");
    strcpy_s(database[7].advice, sizeof(database[7].advice), "严禁熬夜；多吃黑芝麻、桑葚、山药；忌辛辣温燥食物");
    strcpy_s(database[7].prescription, sizeof(database[7].prescription), "六味地黄丸");

    // 9. 痰湿咳嗽
    strcpy_s(database[8].name, sizeof(database[8].name), "痰湿咳嗽");
    strcpy_s(database[8].symptoms, sizeof(database[8].symptoms), "咳嗽反复，痰多色白质黏，早晨或饭后加重，胸闷身重");
    strcpy_s(database[8].advice, sizeof(database[8].advice), "严格忌口甜食、冷饮、油腻食物；多吃白萝卜、冬瓜");
    strcpy_s(database[8].prescription, sizeof(database[8].prescription), "二陈汤");

    // 10. 脾胃虚寒
    strcpy_s(database[9].name, sizeof(database[9].name), "脾胃虚寒");
    strcpy_s(database[9].symptoms, sizeof(database[9].symptoms), "胃部怕冷，喜温喜按，吃凉的就不舒服，大便稀溏");
    strcpy_s(database[9].advice, sizeof(database[9].advice), "食物以温热为主（如生姜、小米粥）；绝对禁止生冷；注意腹部保暖");
    strcpy_s(database[9].prescription, sizeof(database[9].prescription), "理中丸");

    // 11. 肝火上炎
    strcpy_s(database[10].name, sizeof(database[10].name), "肝火上炎");
    strcpy_s(database[10].symptoms, sizeof(database[10].symptoms), "头痛头晕，面红目赤，口苦易怒，耳鸣如潮，失眠多梦");
    strcpy_s(database[10].advice, sizeof(database[10].advice), "管理情绪，忌酒和辛辣；喝菊花茶；保证晚上11点前睡觉");
    strcpy_s(database[10].prescription, sizeof(database[10].prescription), "龙胆泻肝汤");

    // 12. 心火亢盛
    strcpy_s(database[11].name, sizeof(database[11].name), "心火亢盛");
    strcpy_s(database[11].symptoms, sizeof(database[11].symptoms), "舌尖长疮溃疡，心烦失眠，小便黄赤甚至有灼热感");
    strcpy_s(database[11].advice, sizeof(database[11].advice), "吃苦瓜、莲子心；多喝淡竹叶水；保持心态平和");
    strcpy_s(database[11].prescription, sizeof(database[11].prescription), "导赤散");

    // 13. 风寒湿痹（关节痛）
    strcpy_s(database[12].name, sizeof(database[12].name), "风寒湿痹（关节痛）");
    strcpy_s(database[12].symptoms, sizeof(database[12].symptoms), "关节（膝、肩）酸楚疼痛，遇冷或阴雨天加重，热敷则缓");
    strcpy_s(database[12].advice, sizeof(database[12].advice), "疼痛部位注意保暖防潮；用艾叶、生姜煮水热敷；避空调冷风直吹");
    strcpy_s(database[12].prescription, sizeof(database[12].prescription), "蠲痹汤");

    // 14. 肺肾阴虚
    strcpy_s(database[13].name, sizeof(database[13].name), "肺肾阴虚");
    strcpy_s(database[13].symptoms, sizeof(database[13].symptoms), "干咳少痰或带血丝，声音嘶哑，腰酸腿软，手足心热，盗汗");
    strcpy_s(database[13].advice, sizeof(database[13].advice), "戒烟，避免油烟；多吃银耳、百合、梨；避免熬夜伤阴");
    strcpy_s(database[13].prescription, sizeof(database[13].prescription), "百合固金汤");

    // 15. 食积停滞
    strcpy_s(database[14].name, sizeof(database[14].name), "食积停滞");
    strcpy_s(database[14].symptoms, sizeof(database[14].symptoms), "暴饮暴食后胃胀痛，打嗝有酸腐味，不想吃饭，大便酸臭");
    strcpy_s(database[14].advice, sizeof(database[14].advice), "下一顿喝白粥让肠胃休息；喝山楂麦芽水助消化；饭后散步");
    strcpy_s(database[14].prescription, sizeof(database[14].prescription), "保和丸");
}

// 显示所有病症列表
void showIllnessList(TCM_Illness database[]) {
    printf("\n========== 中医常见病症列表 ==========\n");
    for (int i = 0; i < MAX_ILLNESS; i++) {
        printf("%2d. %s\n", i + 1, database[i].name);
    }
    printf("====================================\n");
}

// 根据症状关键词搜索
void searchBySymptom(TCM_Illness database[], char* keyword) {
    int found = 0;
    printf("\n搜索症状关键词: \"%s\"\n", keyword);
    printf("========================================\n");

    for (int i = 0; i < MAX_ILLNESS; i++) {
        // 在症状描述中搜索关键词
        if (strstr(database[i].symptoms, keyword) != NULL) {
            printf("\n匹配病症：%s\n", database[i].name);
            printf("典型症状：%s\n", database[i].symptoms);
            printf("调理建议：%s\n", database[i].advice);
            printf("参考方剂：%s\n", database[i].prescription);
            printf("----------------------------------------\n");
            found = 1;
        }
    }

    if (!found) {
        printf("未找到包含该关键词的病症。\n");
        printf("请尝试其他描述，如：发烧、胃痛、咳嗽等。\n");
    }
}

// 根据病症名称查询
void searchByName(TCM_Illness database[], char* name) {
    int found = 0;

    for (int i = 0; i < MAX_ILLNESS; i++) {
        if (strstr(database[i].name, name) != NULL) {
            printf("\n========== 病症信息详情 ==========\n");
            printf("病症名称：%s\n", database[i].name);
            printf("典型症状：%s\n", database[i].symptoms);
            printf("调理建议：%s\n", database[i].advice);
            printf("参考方剂：%s\n", database[i].prescription);
            printf("===================================\n");
            found = 1;
            break;
        }
    }

    if (!found) {
        printf("未找到病症：%s\n", name);
        printf("请查看病症列表确认正确的名称。\n");
    }
}

// 显示免责声明
void showDisclaimer() {
    printf("\n**************************************************\n");
    printf("*                重要声明                        *\n");
    printf("* 本程序仅供学习和参考使用，不能替代专业医疗诊断 *\n");
    printf("* 如有不适，请及时就医咨询专业中医师           *\n");
    printf("* 请勿自行用药，所有方剂需在医师指导下使用     *\n");
    printf("**************************************************\n\n");
}

// 主函数
int main() {
    TCM_Illness illnessDatabase[MAX_ILLNESS];
    char input[100];
    int choice;

    // 初始化数据库
    initTCMDATABASE(illnessDatabase);

    printf("欢迎使用中医简易查询系统 (VS2022版)\n");
    showDisclaimer();

    while (1) {
        printf("\n========== 主菜单 ==========\n");
        printf("1. 查看所有病症列表\n");
        printf("2. 根据症状关键词查询\n");
        printf("3. 根据病症名称查询\n");
        printf("4. 退出系统\n");
        printf("请选择操作 (1-4): ");

        // 主菜单输入校验：只允许输1-4的数字，输错重新来
        while (1) {
            printf("请选择操作 (1-4): ");
            // 判断是否是数字，且在1-4之间
            if (scanf_s("%d", &choice) == 1 && choice >= 1 && choice <= 4) {
                (void)getchar(); // 清除输入后的换行符，避免后续输入出错
                break; // 输入正确，退出循环，执行后续操作
            }
            else {
                // 输入错误（字母/符号/超范围数字），提示并清空缓冲区
                printf("❌ 输入错误！请输入1-4之间的数字\n");
                while (getchar() != '\n'); // 清空缓冲区，避免死循环
            }
        }
        switch (choice) {
        case 1:
            showIllnessList(illnessDatabase);
            break;

        case 2:
            printf("\n请输入症状关键词（如：发烧、胃痛、咳嗽等）: ");
            fgets(input, sizeof(input), stdin);
            input[strcspn(input, "\n")] = 0; // 移除换行符
            searchBySymptom(illnessDatabase, input);
            break;

        case 3:
            printf("\n请输入病症名称（如：风热感冒、胃火旺盛等）: ");
            fgets(input, sizeof(input), stdin);
            input[strcspn(input, "\n")] = 0; // 移除换行符
            searchByName(illnessDatabase, input);
            break;

        case 4:
            printf("\n感谢使用中医简易查询系统！\n");
            printf("祝您健康！\n");
            return 0;

        default:
            printf("无效选择，请输入1-4之间的数字！\n");
        }
    }

    return 0;
}