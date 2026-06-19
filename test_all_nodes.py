import requests
import json
import os
import time
import sys

BASE = "http://localhost:8000/api/v1"
PASSED = 0
FAILED = 0
RESULTS = []

def create_and_run(name, nodes, edges, inputs=None):
    global PASSED, FAILED
    if inputs is None:
        inputs = {"input": "test_data"}
    wf = {"name": name, "description": f"test {name}", "nodes": nodes, "edges": edges, "status": "active"}
    try:
        r = requests.post(f"{BASE}/workflows", json=wf, timeout=10)
        if r.status_code != 200:
            msg = f"[FAIL] {name}: create HTTP {r.status_code}"
            print(msg); RESULTS.append(msg); FAILED += 1; return None
        wf_id = r.json().get("id") or r.json().get("_id")
        if not wf_id:
            msg = f"[FAIL] {name}: no id"
            print(msg); RESULTS.append(msg); FAILED += 1; return None
    except Exception as e:
        msg = f"[FAIL] {name}: create {e}"
        print(msg); RESULTS.append(msg); FAILED += 1; return None
    try:
        r = requests.post(f"{BASE}/workflows/{wf_id}/run", json={"inputs": inputs}, timeout=60)
        if r.status_code != 200:
            msg = f"[FAIL] {name}: run HTTP {r.status_code} {r.text[:300]}"
            print(msg); RESULTS.append(msg); FAILED += 1; return wf_id
        result = r.json()
        node_results = result.get("node_results", {})
        outputs = result.get("outputs", {})
        has_error = any(isinstance(nr, dict) and "error" in nr for nr in node_results.values())
        has_fail = any(isinstance(nr, dict) and nr.get("status") == "failed" for nr in node_results.values())
        if has_error or has_fail:
            details = json.dumps(node_results, ensure_ascii=False, default=str)[:500]
            msg = f"[FAIL] {name}: {details}"
            print(msg); RESULTS.append(msg); FAILED += 1
        else:
            brief = json.dumps(node_results, ensure_ascii=False, default=str)[:200]
            msg = f"[PASS] {name}: {brief}"
            print(msg); RESULTS.append(msg); PASSED += 1
    except Exception as e:
        msg = f"[FAIL] {name}: run {e}"
        print(msg); RESULTS.append(msg); FAILED += 1
    return wf_id

def S(t, l, c={}):
    return {"id": t, "type": t.split("_")[0], "label": l, "config": c}

def N(id, tp, label, c={}):
    return {"id": id, "type": tp, "label": label, "config": c}

def E(s, t):
    return {"id": f"e_{s}_{t}", "source": s, "target": t}

# ==================== 数据处理类 ====================

def test_math_calc():
    return create_and_run("math_calc", [
        N("start_1","start","input",{}), N("n1","math_calc","calc",{"expression":"2 + 3 * 4"}), N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_datetime():
    return create_and_run("datetime_now", [
        N("start_1","start","input",{}), N("n1","datetime","dt",{"action":"now","format":"%Y-%m-%d %H:%M:%S"}), N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_datetime_timestamp():
    return create_and_run("datetime_timestamp", [
        N("start_1","start","input",{}), N("n1","datetime","dt",{"action":"timestamp","format":""}), N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_type_convert():
    return create_and_run("type_convert_int", [
        N("start_1","start","input",{"default_input":"42"}), N("n1","type_convert","tc",{"target_type":"int","input_template":"{{input}}"}), N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_type_convert_list():
    return create_and_run("type_convert_list", [
        N("start_1","start","input",{"default_input":"a,b,c"}), N("n1","type_convert","tc",{"target_type":"list","delimiter":",","input_template":"{{input}}"}), N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_csv_parse():
    return create_and_run("csv_parse", [
        N("start_1","start","input",{"default_input":"name,age\nAlice,30\nBob,25"}),
        N("n1","csv_parse","csv",{"delimiter":",","has_header":True,"input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_regex_replace():
    return create_and_run("regex_replace", [
        N("start_1","start","input",{"default_input":"hello world 123"}),
        N("n1","regex_replace","rr",{"pattern":"\\d+","replacement":"NUM","input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_hash_md5():
    return create_and_run("hash_md5", [
        N("start_1","start","input",{"default_input":"hello"}),
        N("n1","hash_encode","h",{"algorithm":"md5","input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_hash_base64():
    return create_and_run("hash_base64_encode", [
        N("start_1","start","input",{"default_input":"hello"}),
        N("n1","hash_encode","h",{"algorithm":"base64_encode","input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_uuid():
    return create_and_run("uuid_generate", [
        N("start_1","start","input",{}), N("n1","uuid_generate","uuid",{"version":"4","count":3}), N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

# ==================== AI 扩展类 ====================

def test_markdown_html():
    return create_and_run("markdown_html", [
        N("start_1","start","input",{"default_input":"# Title\n\n**bold** text"}),
        N("n1","markdown_html","md",{"input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

# ==================== 网络通信类 ====================

def test_network_ping():
    return create_and_run("network_ping", [
        N("start_1","start","input",{"default_input":"127.0.0.1"}),
        N("n1","network_ping","ping",{"count":2,"timeout":5,"input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_http_stream():
    return create_and_run("http_stream", [
        N("start_1","start","input",{}),
        N("n1","http_stream","hs",{"method":"GET","url":"http://httpbin.org/get","timeout":10}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

# ==================== 实用工具类 ====================

def test_qrcode_gen():
    return create_and_run("qrcode_gen", [
        N("start_1","start","input",{"default_input":"https://github.com"}),
        N("n1","qrcode_gen","qr",{"size":256,"input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_json_diff():
    return create_and_run("json_diff", [
        N("start_1","start","input",{"default_input":"{\"name\":\"Alice\",\"age\":30}"}),
        N("n1","json_diff","jd",{"input_template":"{{input}}","compare_value":"{\"name\":\"Bob\",\"age\":25}"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

# ==================== 原有节点 ====================

def test_transform():
    return create_and_run("transform", [
        N("start_1","start","input",{"default_input":"Hello"}),
        N("n1","transform","t",{"template":"{{input}} World!"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_condition_true():
    return create_and_run("condition_true", [
        N("start_1","start","input",{"default_input":"yes"}),
        N("n1","condition","cond",{"condition":"input == 'yes'"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_delay():
    return create_and_run("delay", [
        N("start_1","start","input",{}), N("n1","delay","d",{"seconds":1}), N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_loop():
    return create_and_run("loop", [
        N("start_1","start","input",{"default_input":"[\"a\",\"b\",\"c\"]"}),
        N("n1","loop","loop",{"list_var":"input"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_code_exec():
    return create_and_run("code_exec", [
        N("start_1","start","input",{"default_input":"3.14"}),
        N("n1","code_exec","code",{"language":"python","code":"import math\nresult = math.sqrt(float('3.14'))"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_error_handler():
    return create_and_run("error_handler", [
        N("start_1","start","input",{}),
        N("n1","error_handler","eh",{"fallback_output":"default"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_switch():
    return create_and_run("switch", [
        N("start_1","start","input",{"default_input":"B"}),
        N("n1","switch","sw",{"switch_var":"input","cases":"A:branchA\nB:branchB","default_case":"default"}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_retry():
    return create_and_run("retry", [
        N("start_1","start","input",{}),
        N("n1","retry","r",{"max_retries":2,"retry_delay":0}),
        N("out_1","output","output",{})
    ], [E("start_1","n1"), E("n1","out_1")])

def test_tool_http():
    return create_and_run("tool_http", [
        N("start_1","start","input",{}),
        N("tool_1","tool","http",{"tool_name":"http","method":"GET","input_template":"http://httpbin.org/get","timeout":10}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

def test_tool_run_command():
    return create_and_run("tool_run_command", [
        N("start_1","start","input",{}),
        N("tool_1","tool","cmd",{"tool_name":"run_command","input_template":"echo hello","timeout":10}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

def test_tool_text_extract():
    return create_and_run("tool_text_extract", [
        N("start_1","start","input",{"default_input":"Hello World! This is a test."}),
        N("tool_1","tool","te",{"tool_name":"text_extract","max_length":10,"input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

def test_tool_regex():
    return create_and_run("tool_regex", [
        N("start_1","start","input",{"default_input":"abc 123 def 456"}),
        N("tool_1","tool","re",{"tool_name":"regex","pattern":"\\d+","input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

def test_tool_json_parse():
    return create_and_run("tool_json_parse", [
        N("start_1","start","input",{"default_input":"{\"a\":{\"b\":42}}"}),
        N("tool_1","tool","jp",{"tool_name":"json_parse","path":"a.b","input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

def test_tool_file_read():
    return create_and_run("tool_file_read", [
        N("start_1","start","input",{}),
        N("tool_1","tool","fr",{"tool_name":"file_read","input_template":"requirements.txt","encoding":"utf-8","max_size":500}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

def test_tool_file_write():
    return create_and_run("tool_file_write", [
        N("start_1","start","input",{"default_input":"workflow test content"}),
        N("tool_1","tool","fw",{"tool_name":"file_write","file_path":"test_output.txt","write_mode":"overwrite","input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

def test_tool_knowledge_search():
    return create_and_run("tool_knowledge_search", [
        N("start_1","start","input",{"default_input":"what is AI"}),
        N("tool_1","tool","ks",{"tool_name":"knowledge_search","top_k":3,"input_template":"{{input}}"}),
        N("out_1","output","output",{})
    ], [E("start_1","tool_1"), E("tool_1","out_1")])

# ==================== 运行 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("WORKFLOW NODE FUNCTIONAL TEST")
    print("=" * 60)

    tests = [
        ("Data Processing", [
            test_math_calc, test_datetime, test_datetime_timestamp,
            test_type_convert, test_type_convert_list, test_csv_parse,
            test_regex_replace, test_hash_md5, test_hash_base64, test_uuid,
        ]),
        ("AI Extension", [test_markdown_html]),
        ("Network", [test_network_ping, test_http_stream]),
        ("Utility", [test_qrcode_gen, test_json_diff]),
        ("Original Nodes", [
            test_transform, test_condition_true, test_delay, test_loop,
            test_code_exec, test_error_handler, test_switch, test_retry,
        ]),
        ("Tool Nodes", [
            test_tool_http, test_tool_run_command, test_tool_text_extract,
            test_tool_regex, test_tool_json_parse, test_tool_file_read,
            test_tool_file_write, test_tool_knowledge_search,
        ]),
    ]

    for cat, fn_list in tests:
        print(f"\n--- {cat} ---")
        for fn in fn_list:
            fn()
            time.sleep(0.3)

    print(f"\n{'=' * 60}")
    print(f"RESULT: PASS {PASSED} / FAIL {FAILED} / TOTAL {PASSED+FAILED}")
    print(f"{'=' * 60}")
    if FAILED > 0:
        print("\nFailed:")
        for r in RESULTS:
            if "[FAIL]" in r:
                print(f"  {r}")
    sys.exit(0 if FAILED == 0 else 1)
