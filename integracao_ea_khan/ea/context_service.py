import re
import json
from pathlib import Path

CACHE_FILE = Path(__file__).resolve().parents[2] / "state" / "ea_context_cache.json"


def extract_selected_item(html, field_name):
    """
    Extrai o JSON de selectedItem baseado no name do searchBox
    """

    pattern = rf'name:\s*setVal\(\'{field_name}\'\).*?selectedItem:\s*eval\((\{{.*?\}})\)'
    
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        raise ValueError(f"{field_name} não encontrado no HTML")

    json_str = match.group(1)

    return json.loads(json_str)


def get_context_ids(session):
    url = "https://7edu-br.educadventista.org/teacherportal/"
    html = session.get(url).text

    term_data = extract_selected_item(html, "academicTermId")
    employee_data = extract_selected_item(html, "employeeId")

    academic_term_id = term_data["Identity"]
    employee_id = employee_data["Identity"]

    return employee_id, academic_term_id


def save_context(employee_id, term_id):
    data = {
        "employee_id": employee_id,
        "academic_term_id": term_id
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_context():
    if not CACHE_FILE.exists():
        return None

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_context_ids_cached(session, test_fn=None):
    cache = load_context()

    if cache and test_fn:
        try:
            if test_fn(cache["employee_id"], cache["academic_term_id"]):
                return cache["employee_id"], cache["academic_term_id"]
        except:
            pass

    # fallback
    employee_id, term_id = get_context_ids(session)
    save_context(employee_id, term_id)

    return employee_id, term_id
