import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class Option:
    id: str
    content: str
    pts: float

@dataclass
class Question:
    isChoice: bool
    type: str
    id: str
    options: list

def fill_form(form_info: Dict[str, Any], method: str = 'good') -> Dict[str, Any]:
    """中文: 根据评教数据生成提交表单。

    English: Create submission payload from questionnaire information.

    Args:
        form_info (Dict[str, Any]): 问卷和题目信息 / Raw form data.
        method (str): 评教策略，默认为 'good' / Strategy for answering.

    Returns:
        Dict[str, Any]: 用于提交的表单数据 / Final payload for submission.
    """
    basic_info = form_info['pjxtPjjgPjjgckb'][1]
    question_list = get_question_list(form_info)
    choice_list = [q for q in question_list if q.isChoice]
    other_list = [q for q in question_list if not q.isChoice]
    if method == 'good':
        choice_answer = gen_good_answer(choice_list)
    elif method == 'random':
        choice_answer = gen_random_answer(choice_list)
    elif method == 'worst_passing':
        choice_answer = gen_worst_passing_answer(choice_list)
    else:
        raise ValueError(f"未知的方法 {method}")
    enforce_rules(choice_answer, choice_list)
    total_score = int(sum(q.pts for q in choice_answer if q))
    answer_list = []
    for i in range(len(choice_list)):
        if choice_answer[i]:
            selected_id = choice_answer[i].id
        else:
            selected_id = ""
        answer_list.append({
            'sjly': '1',
            'stlx': choice_list[i].type,
            'wjid': basic_info['wjid'],
            'wjssrwid': basic_info['wjssrwid'],
            'wjstctid': "",
            'wjstid': choice_list[i].id,
            'xxdalist': [
                selected_id
            ]
        })
    for q in other_list:
        answer_list.append({
            'sjly': '1',
            'stlx': q.type,
            'wjid': basic_info['wjid'],
            'wjssrwid': basic_info['wjssrwid'],
            'wjstctid': q.options[0].id if q.options else "",
            'wjstid': q.id,
            'xxdalist': [
                ""
            ]
        })
    ret = {
        'pjidlist': [],
        'pjjglist': [
            {
                'bprdm': basic_info['bprdm'],
                'bprmc': basic_info['bprmc'],
                'kcdm': basic_info['kcdm'],
                'kcmc': basic_info['kcmc'],
                'pjdf': total_score,
                'pjfs': basic_info['pjfs'],
                'pjid': basic_info['pjid'],
                'pjlx': basic_info['pjlx'],
                'pjmap': form_info['pjmap'],
                'pjrdm': basic_info['pjrdm'],
                'pjrjsdm': basic_info['pjrjsdm'],
                'pjrxm': basic_info['pjrxm'],
                'pjsx': 1,
                'rwh': basic_info['rwh'],
                'stzjid': basic_info['stzjid'],
                'wjid': basic_info['wjid'],
                'wjssrwid': basic_info['wjssrwid'],
                'wtjjy': '',
                'xhgs': basic_info['xhgs'],
                'xnxq': basic_info['xnxq'],
                'sfxxpj': '1',
                'sqzt': basic_info['sqzt'],
                'yxfz': basic_info['yxfz'],
                'sdrs': basic_info['sdrs'],
                "zsxz": basic_info['pjrjsdm'],
                'sfnm': '1',
                'pjxxlist': answer_list
            }
        ],
        'pjzt': '1'
    }
    return ret

def get_question_list(form_info: Dict[str, Any]) -> List[Question]:
    """中文: 从原始数据中解析出所有题目。

    English: Parse question list from raw form information.

    Args:
        form_info (Dict[str, Any]): 问卷数据 / Raw form data.

    Returns:
        List[Question]: 解析后的题目列表 / Parsed questions.
    """
    ret = []
    for entry in form_info['pjxtWjWjbReturnEntity']['wjzblist'][0]['tklist']:
        q = Question(
            isChoice=entry['tmlx'] == '1',
            type=entry['tmlx'],
            id=entry['tmid'],
            options=[]
        )
        for option in entry.get('tmxxlist', []):
            q.options.append(Option(
                id=option['tmxxid'],
                content=option['xxmc'],
                pts=float(option['xxfz'])
            ))
        q.options.sort(key=lambda x: x.pts, reverse=True)
        ret.append(q)
    return ret

def gen_good_answer(choice_list: List[Question]) -> List[Optional[Option]]:
    """中文: 为每个选择题生成最高分答案。

    English: Generate the best-scoring answer for each choice question.

    Args:
        choice_list (List[Question]): 选择题列表 / Choice questions.

    Returns:
        List[Optional[Option]]: 每题选择的选项 / Selected options.
    """
    ret = []
    for q in choice_list:
        ret.append(q.options[0] if q.options else None)
    return ret

def gen_random_answer(choice_list: List[Question]) -> List[Optional[Option]]:
    """中文: 随机生成选择题答案。

    English: Randomly select an answer for each choice question.

    Args:
        choice_list (List[Question]): 选择题列表 / Choice questions.

    Returns:
        List[Optional[Option]]: 随机选择的选项 / Randomly chosen options.
    """
    ret = []
    for q in choice_list:
        if q.options:
            selected_option = random.choice(q.options[:3]) if len(q.options) >=3 else random.choice(q.options)
            ret.append(selected_option)
        else:
            ret.append(None)
    return ret

def gen_worst_passing_answer(choice_list: List[Question]) -> List[Optional[Option]]:
    """中文: 生成仍保证及格的最低分答案。

    English: Generate the lowest passing answers for each choice question.

    Args:
        choice_list (List[Question]): 选择题列表 / Choice questions.

    Returns:
        List[Optional[Option]]: 选择的选项 / Selected options ensuring pass.
    """
    ret = []
    for q in choice_list:
        if q.options:
            ret.append(q.options[2] if len(q.options) >=3 else q.options[-1])
        else:
            ret.append(None)
    return ret

def enforce_rules(choice_answer: List[Optional[Option]], choice_list: List[Question]) -> None:
    """中文: 对生成的答案应用限制规则。

    English: Enforce rules to adjust generated answers.

    Args:
        choice_answer (List[Optional[Option]]): 已选择的答案列表 / Generated answers.
        choice_list (List[Question]): 所有选择题 / Choice questions.
    """
    # 规则1：不能全选同一个选项
    selected_contents = [option.content for option in choice_answer if option]
    if len(set(selected_contents)) == 1:
        for i, option in enumerate(choice_answer):
            if option.content != '中等':
                for opt in choice_list[i].options:
                    if opt.content != option.content:
                        choice_answer[i] = opt
                        break
                break
    # 规则2：前五道题中至少有一道选择“合格以上”（中等、良好、优秀）
    count_passing = sum(1 for option in choice_answer[:5] if option and option.content in ['中等', '良好', '优秀'])
    if count_passing == 0:
        for i in range(5):
            if choice_answer[i]:
                for opt in choice_list[i].options:
                    if opt.content == '中等':
                        choice_answer[i] = opt
                        break
                break
