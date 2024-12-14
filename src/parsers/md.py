"""
Module that handles parsing MD files and converting them to JSON
"""

import sys
import json
import re


def get_meta(question_dict: dict, key: str):
    """
    Get metadata from question_dict
    :param question_dict: dictionary that contains question metadata
    :param key: the key that will be searched in the dictionary
    :return: the value associated with key from question dict
    """
    if not key in question_dict["metadata"]:
        return ""
    if len(question_dict["metadata"][key]) == 1:
        return question_dict["metadata"][key][0]
    return question_dict["metadata"][key]

def set_meta(question_dict: dict, key: str, value: any):
    """
    Set metadata in question_dict
    :param question_dict: dictionary that contains question metadata
    :param key: the key that will be searched in the dictionary
    :param value: the value that will be set in the dictionary
    """
    if key not in question_dict["metadata"]:
        question_dict["metadata"][key] = []

    question_dict["metadata"][key].append(value)

def quiz_md_to_json(file_content: str):
    """
    Converts a MD quiz to JSON quiz
    :param file_content: a quiz stored in MD format
    :return: a quiz stored in JSON format
    """
    question_arr = file_content.split("\n\n\n")
    question_arr_json = list(map(md_to_json, question_arr))
    return '[' + ','.join(question_arr_json) + ']'

def quiz_json_to_md(json_arr: list):
    """
    Converts a JSON quiz to MD quiz
    :param file_content: a quiz stored in JSON format
    :return: a quiz stored in MD format
    """
    return list(map(json_to_md, json_arr))

def json_to_md(json_obj: dict) -> str:
    """
    Generates a question in MD format from JSON string
    :param json_obj: a question stored in JSON format
    :return: a string representing a question in MD format
    """

    json_q = json_obj
    md_q = ""

    md_q += "# " + json_q["name"] + "\n\n"
    md_q += "## Question Text\n\n"
    md_q += json_q["statement"] + "\n\n"

    md_q += "## Question Answers\n\n"
    for answer in json_q["answers"]:
        ans = answer["statement"]
        grade = "+" if answer["correct"] else "-"
        md_q += grade + " " + ans + "\n\n"

    if "feedback" in json_q and json_q["feedback"] is not None:
        md_q += "## Feedback\n\n"
        md_q += json_q["feedback"] + "\n\n"

    if "metadata" in json_q:
        md_q += "## Metadata\n\n"
        for json_tag in json_q["metadata"]:
            md_q += json_tag + "=" + str(get_meta(json_q, json_tag)) + "\n\n"

    return md_q + "\n"

def check_md_q(md_q: str) -> None:
    """
    Validates a question format in MD and exits with error if invalid
    :param md_q: a question stored in MD format
    :return: None
    """
    q_title = md_q.split('\n')[0]
    if not q_title.startswith('# '):
        sys.exit(f'Error: Question starting with \"{q_title}\" does not have a title.')

    q_title = q_title[2:]
    q_fields = md_q.split('## ')

    field_names = [f.split('\n')[0] for f in q_fields[1:]]
    if 'Question Text' not in field_names or \
        'Question Answers' not in field_names:
        sys.exit(f'Error: No question text or answer set for question \"{q_title}\".')

    q_ans = [s.rstrip('\n').split('\n')[1:] for s in q_fields if s.startswith('Question Answers')][0]
    correct_answers_no = len([ans for ans in q_ans if ans[0] == '+'])
    if correct_answers_no < 1:
        sys.exit(f'Error: No correct answer set for question \"{q_title}\".')

def md_to_json(md_q: str) -> str:
    """
    Generates a question in JSON format from MD string
    :param md_q: a question stored in MD format
    :return: a string representing a question in JSON format
    """
    md_copy = str(md_q).rstrip()
    md_copy = re.sub(r'\n+', '\n', md_copy).strip('\n')

    check_md_q(md_copy)

    question = {
        "name": "",
        "statement": "",
        "feedback": "",
        "metadata": {},
        "answers": [
            # {
            #     "statement": "",
            #     "correct": False,
            #     "grade": 0.0
            # }
        ],
        "correct_answers_no": 0,
    }

    q_title = md_copy.split('\n')[0][2:]
    q_body = md_copy.split('\n')[1:]
    question["name"] = q_title

    q_fiels = md_copy.split('## ')

    for field in q_fiels:
        field_name = field.split('\n')[0]

        if field_name == 'Question Text':
            question['statement'] = '\n'.join(field.split('\n')[1:])
        elif field_name == 'Question Answers':
            q_ans = field.rstrip('\n').split('\n')[1:]
            question['correct_answers_no'] = len([ans for ans in q_ans if ans[0] == '+'])
            grade = 1 / (question['correct_answers_no'] * 1.0)

            for ans in q_ans:
                if ans[0] == '+':
                    question['answers'].append(
                        {"statement": ans[2:], "correct": True, "grade": grade}
                    )
                elif ans[0] == '-':
                    if question['correct_answers_no'] > 1:
                        question['answers'].append(
                            {"statement": ans[2:], "correct": False, "grade": -grade}
                        )
                    else:
                        question['answers'].append(
                            {"statement": ans[2:], "correct": False, "grade": 0}
                        )
        elif field_name == 'Feedback':
            question['feedback'] = '\n'.join(field.split('\n')[1:])
        elif field_name == 'Metadata':
            metas = field.rstrip('\n').split('\n')[1:]
            for meta in metas:
                tag_pair = meta.split("=")
                set_meta(question, tag_pair[0], tag_pair[1])

    return json.dumps(question, indent=4)
