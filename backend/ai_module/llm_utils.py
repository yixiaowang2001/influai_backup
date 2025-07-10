import json
import re


def parse_json_response(response, default_output):
    try:
        result = json.loads(response)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    cleaned = response.strip()

    # ```json ```
    if cleaned.startswith('```json') and cleaned.endswith('```'):
        try:
            content = cleaned[7:-3].strip()
            return json.loads(content)
        except:
            pass

    # <json></json>
    xml_match = re.search(r'<json>(.*?)</json>', cleaned, re.DOTALL)
    if xml_match:
        try:
            return json.loads(xml_match.group(1).strip())
        except:
            pass

    # {JSON}
    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass

    return default_output


if __name__ == "__main__":
    response = """```json
    {
      "极差": 0.23,
      "不友善": 0.22,
      "中立": 0.31,
      "友善": 0.18,
      "极好": 0.04,
      "狂热": 0.02
    }
    ```"""

    default_response = {
        "极差": 0.0,
        "不友善": 0.0,
        "中立": 0.0,
        "友善": 0.0,
        "极好": 0.0,
        "狂热": 0.0
    }

    parsed = parse_json_response(response, default_response)
    print(parsed)
