"""Unit tests for DAG engine validation, cycle detection, and topological sorting."""

import pytest
from app.engine.dag import DAG, DAGValidationError


def test_valid_linear_dag():
    nodes = [
        {"id": "n1", "type": "manualTrigger", "label": "Start"},
        {"id": "n2", "type": "aiAgent", "label": "Process"},
        {"id": "n3", "type": "output", "label": "End"},
    ]
    edges = [
        {"id": "e1", "source": "n1", "target": "n2"},
        {"id": "e2", "source": "n2", "target": "n3"},
    ]
    dag = DAG(nodes, edges)
    is_valid, errors, warnings = dag.validate()
    assert is_valid is True
    assert len(errors) == 0

    order = dag.detect_cycles_and_sort()
    assert order == ["n1", "n2", "n3"]


def test_dag_cycle_detection():
    # n1 -> n2 -> n3 -> n1 (cycle)
    nodes = [
        {"id": "n1", "type": "manualTrigger", "label": "Start"},
        {"id": "n2", "type": "aiAgent", "label": "Process"},
        {"id": "n3", "type": "output", "label": "End"},
    ]
    edges = [
        {"id": "e1", "source": "n1", "target": "n2"},
        {"id": "e2", "source": "n2", "target": "n3"},
        {"id": "e3", "source": "n3", "target": "n1"},  # Creates cycle!
    ]
    dag = DAG(nodes, edges)
    is_valid, errors, warnings = dag.validate()
    assert is_valid is False
    assert any("Cycle detected" in err for err in errors)

    with pytest.raises(DAGValidationError):
        dag.detect_cycles_and_sort()


def test_dag_missing_trigger():
    nodes = [
        {"id": "n1", "type": "transform", "label": "Transform"},
        {"id": "n2", "type": "output", "label": "End"},
    ]
    edges = [
        {"id": "e1", "source": "n1", "target": "n2"},
    ]
    dag = DAG(nodes, edges)
    is_valid, errors, warnings = dag.validate()
    assert is_valid is False
    assert any("at least one trigger node" in err for err in errors)
