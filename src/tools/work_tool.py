from langchain_core.tools import tool
from typing import List, Dict, Any, Optional

@tool(parse_docstring=True)
def work_tool(
    overall_policy: Optional[str] = None,
    worker_role: Optional[str] = None,
    work_rules: Optional[str] = None,
    work_plan: Optional[str] = None,
    work_content: Optional[str] = None,
    work_purpose: Optional[str] = None,
    work_results: Optional[str] = None,
    current_issues: Optional[str] = None,
    issue_countermeasures: Optional[str] = None,
    next_steps: Optional[str] = None,
    memos: Optional[str] = None,
    todo_list: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """エージェントの作業状態、計画、課題などを管理するためのツール。

    このツールは、エージェントの現在の作業に関する様々な情報を更新するために使用されます。
    各パラメータは独立して更新可能で、指定された値がAgentStateに反映されます。

    Args:
        overall_policy (str, optional): 全体の方針。
        worker_role (str, optional): 作業者の役割。
        work_rules (str, optional): 作業ルール。
        work_plan (str, optional): 作業計画。
        work_content (str, optional): 作業内容。
        work_purpose (str, optional): 作業目的。
        work_results (str, optional): 作業結果。
        current_issues (str, optional): 現在の課題。
        issue_countermeasures (str, optional): 課題対応方針。
        next_steps (str, optional): 次の作業。
        memos (str, optional): その他備忘用メモ書き。
        todo_list (list[dict], optional): TODOリスト。各項目は {"task": "タスク内容", "completed": False} の形式の辞書リスト。

    Returns:
        更新された作業状態の辞書。AgentStateにマージされます。
    """
    updated_state = {}
    if overall_policy is not None: updated_state["overall_policy"] = overall_policy
    if worker_role is not None: updated_state["worker_role"] = worker_role
    if work_rules is not None: updated_state["work_rules"] = work_rules
    if work_plan is not None: updated_state["work_plan"] = work_plan
    if work_content is not None: updated_state["work_content"] = work_content
    if work_purpose is not None: updated_state["work_purpose"] = work_purpose
    if work_results is not None: updated_state["work_results"] = work_results
    if current_issues is not None: updated_state["current_issues"] = current_issues
    if issue_countermeasures is not None: updated_state["issue_countermeasures"] = issue_countermeasures
    if next_steps is not None: updated_state["next_steps"] = next_steps
    if memos is not None: updated_state["memos"] = memos
    if todo_list is not None: updated_state["todo_list"] = todo_list
    
    return updated_state
