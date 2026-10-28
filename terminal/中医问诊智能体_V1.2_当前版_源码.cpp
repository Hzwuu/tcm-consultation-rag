#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif

#pragma execution_character_set("utf-8")

struct TCMIllness {
    std::string name;
    std::string symptoms;
    std::string advice;
    std::string prescription;
};

static const std::vector<std::pair<std::string, std::vector<std::string>>> SYNONYM_GROUPS = {
    {"发热", {"发热", "发烧", "身热", "高热", "低热", "体温高"}},
    {"怕冷", {"怕冷", "畏寒", "恶寒", "发冷", "怕风", "手脚发凉", "手脚冰凉"}},
    {"咽痛", {"咽痛", "喉咙痛", "嗓子疼", "喉咙疼", "喉咙红痛", "咽喉痛", "咽干痛"}},
    {"咳嗽", {"咳嗽", "干咳", "咳痰", "咳白稀痰"}},
    {"痰多", {"痰多", "痰多色白", "黄痰", "白痰"}},
    {"流鼻涕", {"流鼻涕", "流涕", "鼻涕", "鼻塞", "流清鼻涕", "流黄浓鼻涕"}},
    {"口渴", {"口渴", "口干", "想喝水", "咽干", "口干咽燥"}},
    {"喜冷饮", {"想喝冷水", "喜冷饮", "喝凉水", "爱喝冷饮", "口渴想喝凉水"}},
    {"不渴", {"不渴", "不想喝水", "口不渴"}},
    {"便秘", {"便秘", "大便干", "大便干结", "干结", "排便困难"}},
    {"腹泻", {"腹泻", "拉稀", "便溏", "大便稀", "大便稀溏", "泄泻"}},
    {"大便酸臭", {"大便酸臭", "酸臭", "大便臭", "臭秽"}},
    {"失眠", {"失眠", "睡不着", "入睡难", "多梦易醒", "心烦失眠", "睡眠不好", "睡眠不太好", "睡不好"}},
    {"多梦", {"多梦", "梦多"}},
    {"心烦", {"心烦", "烦躁", "易怒", "急躁", "爱发火"}},
    {"乏力", {"乏力", "没力气", "浑身乏力", "疲倦", "疲劳", "神疲乏力", "少气懒言", "容易累", "白天容易累"}},
    {"头晕", {"头晕", "眩晕", "头晕眼花", "头重脚轻", "头晕目眩"}},
    {"头痛", {"头痛", "头疼", "头目胀痛"}},
    {"胃胀", {"胃胀", "腹胀", "肚子胀", "饭后腹胀", "腹胀恶心"}},
    {"胃痛", {"胃痛", "胃脘痛", "胃部灼痛", "胃部隐痛"}},
    {"反酸", {"反酸", "泛酸", "烧心", "嗳腐吞酸", "打嗝有酸腐味", "打嗝酸腐"}},
    {"食欲不振", {"不想吃饭", "食欲不振", "纳差", "食欲差", "食欲不佳"}},
    {"腰膝酸软", {"腰酸", "腰膝酸软", "腰膝酸痛", "膝软", "腰疼", "腰痛", "腰膝冷痛"}},
    {"盗汗", {"盗汗", "夜间出汗", "睡着出汗"}},
    {"自汗", {"自汗", "白天出汗", "动一动就出汗", "容易出汗"}},
    {"无汗", {"无汗", "不出汗", "没汗"}},
    {"畏寒肢冷", {"畏寒肢冷", "四肢不温", "肢体不温", "手脚发冷", "手足不温"}},
    {"夜尿多", {"夜尿多", "夜尿频", "小便清长", "尿清长"}},
    {"尿黄", {"尿黄", "小便黄", "尿色黄", "小便短黄"}},
    {"口苦", {"口苦"}},
    {"口臭", {"口臭"}},
    {"心慌", {"心慌", "心悸"}},
    {"胸闷", {"胸闷", "胸痛", "胸口痛", "胸胁胀", "胁痛", "两胁痛", "胸闷胁痛"}},
    {"关节痛", {"关节痛", "关节疼痛", "关节酸楚", "遇冷加重", "阴雨天加重"}},
    {"潮热", {"潮热", "五心烦热", "手足心热", "手脚心发热"}},
    {"气短", {"气短", "气促", "喘不过气", "活动后加重", "咳嗽无力"}},
    {"健忘", {"健忘", "记性差", "记忆力差"}},
    {"面色苍白", {"面色苍白", "面色萎黄", "面色暗沉", "口唇紫暗"}},
    {"大便黏腻", {"大便黏腻", "大便黏", "大便粘"}},
};

static const std::map<std::string, std::string> TYPO_MAP = {
    {"咽通", "咽痛"},
    {"怕泠", "怕冷"},
    {"咳嗖", "咳嗽"},
    {"头通", "头痛"},
    {"腹涨", "腹胀"},
    {"腹泄", "腹泻"},
    {"失眠多梦易醒", "失眠"},
};

static const std::vector<std::string> PROTECTED_WORDS = {
    "没有", "不是", "不想", "不要", "不清楚", "正常", "太多", "烧烤",
    "胃口", "睡眠", "白天", "晚上", "昨天", "今天", "最近", "开始",
    "以后", "时候", "现在", "感觉", "有点", "比较", "特别", "一直",
    "然后", "还是", "就是", "可能", "可以", "已经", "不好", "不太",
};

std::string trim(const std::string& value) {
    const std::string spaces = " \t\r\n";
    const size_t start = value.find_first_not_of(spaces);
    if (start == std::string::npos) {
        return "";
    }
    const size_t end = value.find_last_not_of(spaces);
    return value.substr(start, end - start + 1);
}

std::vector<std::string> splitCsvLine(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    bool inQuotes = false;
    for (size_t i = 0; i < line.size(); ++i) {
        const char ch = line[i];
        if (ch == '"') {
            if (inQuotes && i + 1 < line.size() && line[i + 1] == '"') {
                field += '"';
                ++i;
            } else {
                inQuotes = !inQuotes;
            }
        } else if (ch == ',' && !inQuotes) {
            fields.push_back(trim(field));
            field.clear();
        } else {
            field += ch;
        }
    }
    fields.push_back(trim(field));
    return fields;
}

std::vector<TCMIllness> loadDatabase(const std::string& filePath) {
    std::vector<TCMIllness> database;
    std::ifstream file(filePath);
    if (!file.is_open()) {
        std::cerr << "无法打开数据文件：" << filePath << "\n";
        return database;
    }
    std::string line;
    bool isHeader = true;
    while (std::getline(file, line)) {
        line = trim(line);
        if (line.empty()) {
            continue;
        }
        if (isHeader) {
            isHeader = false;
            continue;
        }
        const std::vector<std::string> fields = splitCsvLine(line);
        if (fields.size() < 4) {
            std::cerr << "跳过格式不完整的数据行：" << line << "\n";
            continue;
        }
        database.push_back({fields[0], fields[1], fields[2], fields[3]});
    }
    return database;
}

const std::map<std::string, std::string>& synonymLookup() {
    static const std::map<std::string, std::string> lookup = [] {
        std::map<std::string, std::string> result;
        for (const auto& group : SYNONYM_GROUPS) {
            result[group.first] = group.first;
            for (const auto& variant : group.second) {
                result[variant] = group.first;
            }
        }
        return result;
    }();
    return lookup;
}

const std::vector<std::string>& vocabulary() {
    static const std::vector<std::string> vocab = [] {
        std::vector<std::string> result;
        for (const auto& item : synonymLookup()) {
            result.push_back(item.first);
        }
        std::sort(result.begin(), result.end(), [](const std::string& a, const std::string& b) {
            return a.size() > b.size();
        });
        return result;
    }();
    return vocab;
}

std::vector<std::string> variantsOf(const std::string& canonical) {
    for (const auto& group : SYNONYM_GROUPS) {
        if (group.first == canonical) {
            return group.second;
        }
    }
    return {canonical};
}

std::vector<std::string> utf8Chars(const std::string& text) {
    std::vector<std::string> chars;
    for (size_t i = 0; i < text.size();) {
        const unsigned char ch = static_cast<unsigned char>(text[i]);
        size_t length = 1;
        if ((ch & 0x80) == 0) {
            length = 1;
        } else if ((ch & 0xE0) == 0xC0) {
            length = 2;
        } else if ((ch & 0xF0) == 0xE0) {
            length = 3;
        } else if ((ch & 0xF8) == 0xF0) {
            length = 4;
        }
        chars.push_back(text.substr(i, length));
        i += length;
    }
    return chars;
}

int levenshteinChars(const std::vector<std::string>& left, const std::vector<std::string>& right) {
    std::vector<int> previous(right.size() + 1);
    for (size_t j = 0; j <= right.size(); ++j) {
        previous[j] = static_cast<int>(j);
    }
    for (size_t i = 1; i <= left.size(); ++i) {
        std::vector<int> current(right.size() + 1, 0);
        current[0] = static_cast<int>(i);
        for (size_t j = 1; j <= right.size(); ++j) {
            const int cost = (left[i - 1] == right[j - 1]) ? 0 : 1;
            current[j] = std::min({previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost});
        }
        previous = current;
    }
    return previous.back();
}

std::string nearestTerm(const std::string& window) {
    const std::vector<std::string> windowChars = utf8Chars(window);
    std::string sameLength;
    std::string otherLength;
    for (const auto& term : vocabulary()) {
        const std::vector<std::string> termChars = utf8Chars(term);
        if (termChars.size() != windowChars.size() &&
            (termChars.size() > windowChars.size() ? termChars.size() - windowChars.size()
                                                   : windowChars.size() - termChars.size()) != 1) {
            continue;
        }
        bool share = false;
        for (const auto& ch : windowChars) {
            if (term.find(ch) != std::string::npos) {
                share = true;
                break;
            }
        }
        if (!share) {
            continue;
        }
        if (levenshteinChars(windowChars, termChars) != 1) {
            continue;
        }
        if (termChars.size() == windowChars.size()) {
            if (sameLength.empty()) {
                sameLength = term;
            }
        } else if (term.find(window) == std::string::npos && window.find(term) == std::string::npos) {
            if (otherLength.empty()) {
                otherLength = term;
            }
        }
    }
    if (!sameLength.empty()) {
        return sameLength;
    }
    return otherLength;
}

bool containsKnown(const std::string& text) {
    for (const auto& item : synonymLookup()) {
        if (text.find(item.first) != std::string::npos) {
            return true;
        }
    }
    return false;
}

bool containsProtected(const std::string& text) {
    for (const auto& word : PROTECTED_WORDS) {
        if (text.find(word) != std::string::npos) {
            return true;
        }
    }
    return false;
}

std::vector<std::string> splitTokens(const std::string& text) {
    const std::vector<std::string> separators = {
        " ", "\t", "，", "、", "；", ";", ",", "。", ".", "！", "？", "!", "?", "\n",
    };
    std::vector<std::string> tokens;
    std::string current;
    const std::vector<std::string> chars = utf8Chars(text);
    for (const auto& ch : chars) {
        if (std::find(separators.begin(), separators.end(), ch) != separators.end()) {
            if (!current.empty()) {
                tokens.push_back(current);
                current.clear();
            }
        } else {
            current += ch;
        }
    }
    if (!current.empty()) {
        tokens.push_back(current);
    }
    return tokens;
}

std::string correctTypos(const std::string& input, std::vector<std::string>& notes) {
    std::string result = input;
    for (const auto& item : TYPO_MAP) {
        size_t position = 0;
        while ((position = result.find(item.first, position)) != std::string::npos) {
            result.replace(position, item.first.size(), item.second);
            notes.push_back(item.first + "→" + item.second);
            position += item.second.size();
        }
    }
    for (int pass = 0; pass < 2; ++pass) {
        bool changed = false;
        for (const auto& token : splitTokens(result)) {
            if (containsKnown(token) || containsProtected(token)) {
                continue;
            }
            const std::vector<std::string> chars = utf8Chars(token);
            for (size_t length = 2; length <= 4 && !changed; ++length) {
                if (chars.size() < length) {
                    break;
                }
                for (size_t i = 0; i + length <= chars.size(); ++i) {
                    std::string window;
                    for (size_t k = i; k < i + length; ++k) {
                        window += chars[k];
                    }
                    if (synonymLookup().count(window)) {
                        continue;
                    }
                    const std::string candidate = nearestTerm(window);
                    if (candidate.empty()) {
                        continue;
                    }
                    const size_t position = result.find(window);
                    if (position != std::string::npos) {
                        result.replace(position, window.size(), candidate);
                        notes.push_back(window + "→" + candidate);
                        changed = true;
                        break;
                    }
                }
            }
            if (changed) {
                break;
            }
        }
        if (!changed) {
            break;
        }
    }
    return result;
}

std::vector<std::string> extractTerms(const std::string& text) {
    std::vector<std::string> terms;
    for (const auto& group : SYNONYM_GROUPS) {
        for (const auto& variant : group.second) {
            if (text.find(variant) != std::string::npos) {
                if (std::find(terms.begin(), terms.end(), group.first) == terms.end()) {
                    terms.push_back(group.first);
                }
                break;
            }
        }
    }
    return terms;
}

std::pair<int, std::vector<std::string>> scoreIllness(
    const TCMIllness& illness,
    const std::vector<std::string>& terms) {
    const std::string text =
        illness.name + "；" + illness.symptoms + "；" + illness.advice + "；" + illness.prescription;
    std::vector<std::string> hits;
    int score = 0;
    for (const auto& term : terms) {
        for (const auto& variant : variantsOf(term)) {
            if (text.find(variant) != std::string::npos) {
                hits.push_back(term);
                score += 3;
                if (illness.name.find(variant) != std::string::npos) {
                    score += 2;
                }
                break;
            }
        }
    }
    return {score, hits};
}

void printIllness(const TCMIllness& illness, int score, const std::vector<std::string>& hits) {
    std::cout << "\n匹配病症：" << illness.name << "（匹配分 " << score << "）\n";
    std::cout << "命中症状：" << (hits.empty() ? "无" : "");
    for (size_t i = 0; i < hits.size(); ++i) {
        std::cout << hits[i] << (i + 1 == hits.size() ? "" : "、");
    }
    std::cout << "\n";
    std::cout << "典型症状：" << illness.symptoms << "\n";
    std::cout << "调理建议：" << illness.advice << "\n";
    std::cout << "参考方剂：" << illness.prescription << "\n";
    std::cout << "----------------------------------------\n";
}

void searchBySymptoms(const std::vector<TCMIllness>& database, const std::string& input) {
    std::vector<std::string> corrections;
    const std::string corrected = correctTypos(trim(input), corrections);
    const std::vector<std::string> terms = extractTerms(corrected);

    if (terms.empty()) {
        std::cout << "未识别到明确症状，请尝试：发烧、怕冷、咽痛、胃胀、失眠等。\n";
        return;
    }

    std::cout << "\n识别到的症状：";
    for (size_t i = 0; i < terms.size(); ++i) {
        std::cout << terms[i] << (i + 1 == terms.size() ? "" : "、");
    }
    std::cout << "\n";
    if (!corrections.empty()) {
        std::cout << "术语纠正：";
        for (size_t i = 0; i < corrections.size(); ++i) {
            std::cout << corrections[i] << (i + 1 == corrections.size() ? "" : "、");
        }
        std::cout << "\n";
    }

    std::vector<std::pair<int, size_t>> ranked;
    std::vector<std::vector<std::string>> hitMap;
    for (size_t i = 0; i < database.size(); ++i) {
        const auto result = scoreIllness(database[i], terms);
        ranked.push_back({result.first, i});
        hitMap.push_back(result.second);
    }
    std::sort(ranked.begin(), ranked.end(), [](const auto& a, const auto& b) {
        return a.first > b.first;
    });

    int shown = 0;
    for (const auto& item : ranked) {
        if (item.first <= 0 || shown >= 5) {
            break;
        }
        printIllness(database[item.second], item.first, hitMap[item.second]);
        ++shown;
    }
    if (shown == 0) {
        std::cout << "未找到匹配的病症，请尝试其他描述。\n";
    }
}

void showIllnessList(const std::vector<TCMIllness>& database) {
    std::cout << "\n========== 中医常见病症列表 ==========\n";
    for (size_t i = 0; i < database.size(); ++i) {
        std::cout << i + 1 << ". " << database[i].name << "\n";
    }
    std::cout << "====================================\n";
}

void searchByName(const std::vector<TCMIllness>& database, const std::string& name) {
    const std::string cleaned = trim(name);
    if (cleaned.empty()) {
        std::cout << "请输入有效病症名称，不能为空。\n";
        return;
    }
    for (const auto& illness : database) {
        if (illness.name.find(cleaned) != std::string::npos) {
            std::cout << "\n========== 病症信息详情 ==========\n";
            std::cout << "病症名称：" << illness.name << "\n";
            std::cout << "典型症状：" << illness.symptoms << "\n";
            std::cout << "调理建议：" << illness.advice << "\n";
            std::cout << "参考方剂：" << illness.prescription << "\n";
            std::cout << "===================================\n";
            return;
        }
    }
    std::cout << "未找到病症：" << cleaned << "\n";
}

void showDisclaimer() {
    std::cout << "\n**************************************************\n";
    std::cout << "*                重要声明                        *\n";
    std::cout << "* 本程序仅供学习和参考使用，不能替代专业医疗诊断 *\n";
    std::cout << "* 如有不适，请及时就医咨询专业中医师           *\n";
    std::cout << "* 请勿自行用药，所有方剂需在医师指导下使用     *\n";
    std::cout << "**************************************************\n\n";
}

int readMenuChoice() {
    int choice = 0;
    while (true) {
        std::cout << "请选择操作 (1-4): ";
        if (std::cin >> choice && choice >= 1 && choice <= 4) {
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            return choice;
        }
        std::cout << "输入错误，请输入1-4之间的数字。\n";
        std::cin.clear();
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    }
}

int main() {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
#endif

    const std::string dataFile = "tcm_data.csv";
    const std::vector<TCMIllness> database = loadDatabase(dataFile);
    if (database.empty()) {
        std::cerr << "病症数据库为空，请确认 " << dataFile << " 与程序位于同一目录。\n";
        return 1;
    }

    std::cout << "欢迎使用中医简易查询系统 V1.2（多症状 + 同义词/错别字容错）\n";
    std::cout << "已加载 " << database.size() << " 条病症数据。\n";
    showDisclaimer();

    while (true) {
        std::cout << "\n========== 主菜单 ==========\n";
        std::cout << "1. 查看所有病症列表\n";
        std::cout << "2. 多症状组合查询（推荐）\n";
        std::cout << "3. 根据病症名称查询\n";
        std::cout << "4. 退出系统\n";

        switch (readMenuChoice()) {
        case 1:
            showIllnessList(database);
            break;
        case 2: {
            std::cout << "\n请输入一个或多个症状（空格或逗号分隔，例如：咽通 发烧 怕冷）: ";
            std::string input;
            std::getline(std::cin, input);
            searchBySymptoms(database, input);
            break;
        }
        case 3: {
            std::cout << "\n请输入病症名称（如：风热感冒、胃火旺盛等）: ";
            std::string input;
            std::getline(std::cin, input);
            searchByName(database, input);
            break;
        }
        case 4:
            std::cout << "\n感谢使用中医简易查询系统！\n祝您健康！\n";
            return 0;
        }
    }
}
