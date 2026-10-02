import importlib
import pytest
from fastapi import HTTPException

def _module(tmp_path, monkeypatch):
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path))
    import app.v1090 as v1090
    return importlib.reload(v1090)

def _request(v):
    return v.GraphRequest(
        projectKey="p1",
        graphKey="research-agent-graph",
        title="Research agent graph",
        agents=[
            {
                "agentKey":"researcher",
                "role":"research orchestration",
                "allowedToolKeys":["lookup"],
                "maxSteps":20,
            }
        ],
        tools=[
            {
                "toolKey":"lookup",
                "action":"read source",
                "risk":"read-only",
                "idempotent":True,
            }
        ],
        nodes=[
            {"nodeKey":"start","kind":"agent","title":"Research","agentKey":"researcher"},
            {"nodeKey":"lookup","kind":"tool","title":"Lookup","toolKey":"lookup"},
            {"nodeKey":"checkpoint","kind":"checkpoint","title":"Checkpoint","checkpoint":True},
            {"nodeKey":"handoff","kind":"handoff","title":"Handoff"},
        ],
        edges=[
            {"fromNode":"start","toNode":"lookup"},
            {"fromNode":"lookup","toNode":"checkpoint"},
            {"fromNode":"checkpoint","toNode":"handoff"},
        ],
        requireExplicitRunApproval=True,
    )

def test_manifest():
    import app.v1090 as v
    m=v.manifest()
    assert m["version"]=="10.9.0"
    assert m["capabilities"]["directedAcyclicGraphValidation"] is True
    assert m["boundaries"]["automaticExternalSideEffects"] is False

def test_compose_deterministic(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch)
    req=_request(v)
    a=v.compose_graph(req)
    b=v.compose_graph(req)
    assert a["graphHash"]==b["graphHash"]
    assert a["graph"]["topologicalOrder"]==["start","lookup","checkpoint","handoff"]
    assert a["graphReady"] is True

def test_save_run_and_replay(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch)
    saved=v.save_graph(_request(v))
    assert saved["idempotent"] is False
    assert v.save_graph(_request(v))["idempotent"] is True

    with pytest.raises(HTTPException) as e:
        v.record_run(v.RunRequest(
            projectKey="p1",
            graphHash=saved["graphHash"],
            approved=False,
            dryRun=True,
        ))
    assert e.value.status_code==409

    run=v.record_run(v.RunRequest(
        projectKey="p1",
        graphHash=saved["graphHash"],
        approved=True,
        dryRun=True,
        executionRuntime="test-runtime",
        nodeStates=[
            {"nodeKey":"start","state":"succeeded"},
            {"nodeKey":"lookup","state":"succeeded"},
            {"nodeKey":"checkpoint","state":"succeeded"},
        ],
    ))
    assert run["run"]["externalSideEffectsExecuted"] is False

    replay=v.replay_plan(v.ReplayRequest(
        projectKey="p1",
        graphHash=saved["graphHash"],
        runHash=run["runHash"],
        fromCheckpointNode="checkpoint",
    ))
    assert replay["replayPlan"]["explicitApprovalRequired"] is True
    assert replay["replayPlan"]["automaticExecution"] is False

def test_cycle_rejected():
    import app.v1090 as v
    with pytest.raises(Exception):
        v.GraphRequest(
            projectKey="p",graphKey="g",title="cycle",
            nodes=[
                {"nodeKey":"a","kind":"compute","title":"A"},
                {"nodeKey":"b","kind":"compute","title":"B"},
            ],
            edges=[
                {"fromNode":"a","toNode":"b"},
                {"fromNode":"b","toNode":"a"},
            ],
        )

def test_undefined_edge_node_rejected():
    import app.v1090 as v
    with pytest.raises(Exception):
        v.GraphRequest(
            projectKey="p",graphKey="g",title="bad edge",
            nodes=[{"nodeKey":"a","kind":"compute","title":"A"}],
            edges=[{"fromNode":"a","toNode":"missing"}],
        )

def test_risky_tool_requires_contract_approval():
    import app.v1090 as v
    with pytest.raises(Exception):
        v.ToolContract(
            toolKey="write",
            action="write external system",
            risk="external-side-effect",
            requiresHumanApproval=False,
        )

def test_risky_tool_node_requires_upstream_approval():
    import app.v1090 as v
    with pytest.raises(Exception):
        v.GraphRequest(
            projectKey="p",graphKey="g",title="unsafe",
            tools=[
                {
                    "toolKey":"write",
                    "action":"external write",
                    "risk":"external-side-effect",
                    "requiresHumanApproval":True,
                }
            ],
            nodes=[
                {"nodeKey":"start","kind":"compute","title":"Start"},
                {"nodeKey":"write","kind":"tool","title":"Write","toolKey":"write"},
            ],
            edges=[{"fromNode":"start","toNode":"write"}],
            allowExternalSideEffects=True,
        )

def test_risky_tool_with_approval_is_valid():
    import app.v1090 as v
    req=v.GraphRequest(
        projectKey="p",graphKey="g",title="approved",
        tools=[
            {
                "toolKey":"write",
                "action":"external write",
                "risk":"external-side-effect",
                "requiresHumanApproval":True,
            }
        ],
        nodes=[
            {"nodeKey":"approval","kind":"human-approval","title":"Approve"},
            {"nodeKey":"write","kind":"tool","title":"Write","toolKey":"write"},
        ],
        edges=[{"fromNode":"approval","toNode":"write"}],
        allowExternalSideEffects=True,
    )
    assert req.nodes[0].approvalRequired is True
