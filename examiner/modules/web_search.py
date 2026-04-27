from typing import List, Dict


def search_interview_questions(
    company: str,
    position: str,
    limit: int = 10,
    config: Dict = None
) -> List[str]:
    web_search_config = config.get("web_search", {}) if config else {}

    if web_search_config.get("enabled"):
        return _search_with_api(company, position, limit, web_search_config)
    else:
        return []


def _search_with_api(company: str, position: str, limit: int, config: Dict) -> List[str]:
    raise NotImplementedError("WebSearch API not yet implemented")
