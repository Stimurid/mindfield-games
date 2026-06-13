"""Live smoke for chimera_weaver against a running backend."""
import json, os, urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8000/api")
MODEL = os.environ.get("SMOKE_MODEL")


def _req(method, path, body=None, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=180) as resp:
        return json.loads(resp.read().decode())


def main():
    chimeras = _req("GET", "/library/entries?kind=chimera")
    cell = chimeras[0]
    print(f"chimera cell: {cell['code']} · {cell['title']}")

    body = _req("POST", f"/library/entries/{cell['id']}/generate-chimera-draft",
                {"model": MODEL} if MODEL else {}, {"X-Player-Token": "smoke-b4"})
    print(f"\n[generated draft]")
    print(f"  name             : {body['name']!r}")
    print(f"  function         : {body['function']!r}")
    print(f"  verb             : {body['verb']!r}")
    print(f"  maturity_stage   : {body['maturity_stage']}")
    print(f"  critique         : {body['critique']!r}")

    print(f"\n[selected organ ids per bank]")
    for bank, ids in body["selected_organs"].items():
        print(f"  {bank:12} {len(ids)} organ(s)")

    # Validate via GameWeaver
    v = _req("POST", f"/configurator/drafts/{body['draft_id']}/weaver", {})
    verdict = v["verdict"]
    print(f"\n[playability_critic verdict]")
    print(f"  verb_status      : {verdict['verb_status']}")
    print(f"  crisis_status    : {verdict['crisis_status']}")
    print(f"  trace_status     : {verdict['trace_status']}")
    print(f"  playable_verdict : {verdict['playable_verdict']}")
    print(f"  critique         : {verdict['critique']}")


if __name__ == "__main__":
    main()
