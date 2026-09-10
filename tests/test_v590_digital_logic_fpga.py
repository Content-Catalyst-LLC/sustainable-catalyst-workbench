import pytest

from backend.app.v590 import (
    BooleanExpressionInput,
    FSMInput,
    FSMTransition,
    HDLScaffoldInput,
    KarnaughInput,
    PYNQOverlayInput,
    ResourceEstimateInput,
    TimingInput,
    TimingSignal,
    fsm_object,
    hdl_scaffold_object,
    karnaugh_object,
    minimize_object,
    parse_logic,
    pynq_overlay_object,
    resource_estimate_object,
    status_record,
    timing_object,
    truth_table_object,
)


def test_status_reports_digital_logic_capabilities_and_export_boundary():
    status = status_record()
    assert status['ok'] is True
    assert status['version'] == '5.9.0'
    for capability in [
        'restricted-boolean-expression-parser','truth-tables','boolean-minimization','karnaugh-maps',
        'finite-state-machine-validation','digital-timing-waveforms','logic-resource-estimates',
        'verilog-scaffolds','vhdl-scaffolds','pynq-overlay-scaffolds','canonical-digital-logic-objects',
    ]:
        assert capability in status['capabilities']
    assert status['synthesisExecutionAuthorized'] is False
    assert status['bitstreamGenerationAuthorized'] is False
    assert status['bitstreamProgrammingAuthorized'] is False
    assert status['jtagAccessAuthorized'] is False


def test_truth_table_xor_is_exact_and_hash_is_canonical():
    result = truth_table_object(BooleanExpressionInput(expression='A ^ B'))
    rows = result['result']['rows']
    assert [row['output'] for row in rows] == [0, 1, 1, 0]
    assert result['result']['minterms'] == [1, 2]
    assert len(result['digitalLogicObjectHash']) == 64


def test_boolean_minimization_reduces_absorption_identity():
    result = minimize_object(BooleanExpressionInput(expression='(A & B) | (A & !B)'))['result']
    assert result['sumOfProducts'] == 'A'
    assert result['minimizedLogic']['gates'] == 0


def test_parser_rejects_unsupported_python_or_function_syntax():
    for expression in ['A.__class__', 'eval(A)', 'A + B', 'A && B']:
        with pytest.raises(ValueError):
            parse_logic(expression)


def test_karnaugh_map_xor_has_gray_grid_and_minterms():
    result = karnaugh_object(KarnaughInput(expression='(!A & B) | (A & !B)'))['result']
    assert result['grid'] == [[0, 1], [1, 0]]
    assert result['minterms'] == [1, 2]
    assert result['rowGrayOrder'] == [0, 1]
    assert result['columnGrayOrder'] == [0, 1]


def test_karnaugh_map_rejects_more_than_four_variables():
    with pytest.raises(ValueError):
        karnaugh_object(KarnaughInput(expression='A & B & C & D & E'))


def test_fsm_validation_reports_reachability_and_binary_encoding():
    result = fsm_object(FSMInput(
        states=['IDLE','RUN','DONE','DEAD'], initialState='IDLE', encoding='binary',
        transitions=[
            FSMTransition(fromState='IDLE',input='start',toState='RUN'),
            FSMTransition(fromState='RUN',input='done',toState='DONE'),
            FSMTransition(fromState='DONE',input='reset',toState='IDLE'),
            FSMTransition(fromState='DEAD',input='0',toState='DEAD'),
        ]
    ))['result']
    assert result['deterministic'] is True
    assert result['unreachableStates'] == ['DEAD']
    assert set(result['stateEncoding']) == {'IDLE','RUN','DONE','DEAD'}
    assert all(len(code) == 2 for code in result['stateEncoding'].values())


def test_fsm_rejects_duplicate_state_input_transition():
    with pytest.raises(ValueError):
        FSMInput(states=['A','B'],initialState='A',transitions=[
            FSMTransition(fromState='A',input='1',toState='A'),
            FSMTransition(fromState='A',input='1',toState='B'),
        ])


def test_timing_waveform_evaluates_logic_without_propagation_delay_claim():
    result = timing_object(TimingInput(
        expression='A ^ B', samplePeriodNs=10,
        signals=[TimingSignal(name='A',values=[0,0,1,1]),TimingSignal(name='B',values=[0,1,0,1])]
    ))['result']
    assert result['output'] == [0,1,1,0]
    assert result['outputTransitionCount'] == 2
    assert result['propagationDelayModeled'] is False


def test_timing_input_requires_equal_signal_lengths():
    with pytest.raises(ValueError):
        TimingInput(expression='A & B',signals=[TimingSignal(name='A',values=[0,1]),TimingSignal(name='B',values=[0])])


@pytest.mark.parametrize('language,ext', [('verilog','.v'),('vhdl','.vhd')])
def test_hdl_scaffold_is_export_only_and_language_specific(language, ext):
    result = hdl_scaffold_object(HDLScaffoldInput(language=language,moduleName='logic_core',expression='A ^ B',outputName='Y',includeTestbench=True))
    r = result['result']
    assert r['exportOnly'] is True
    assert r['requiresHumanReviewBeforeSynthesis'] is True
    assert r['synthesisPerformed'] is False
    assert r['bitstreamGenerated'] is False
    assert r['files'][0]['path'].endswith(ext)
    assert any(f['path'].endswith('.xdc') for f in r['files'])
    assert len(result['digitalLogicObjectHash']) == 64


def test_resource_estimate_is_explicitly_pre_synthesis_heuristic():
    r = resource_estimate_object(ResourceEstimateInput(expression='(A & B) | (C & D)',targetFamily='zynq-7000',lutInputs=6))['result']
    assert r['estimateType'] == 'pre-synthesis-heuristic'
    assert r['estimatedLUTs'] >= 1
    assert r['placementRoutingModeled'] is False
    assert r['timingClosureModeled'] is False


def test_pynq_overlay_scaffold_does_not_resolve_pins_or_load_bitstream():
    r = pynq_overlay_object(PYNQOverlayInput(projectName='demo_overlay',moduleName='logic_core',expression='A ^ B',board='pynq-z2'))['result']
    paths = [f['path'] for f in r['files']]
    assert 'pynq_overlay.py' in paths
    assert 'README_PYNQ.md' in paths
    assert r['vivadoExecutionPerformed'] is False
    assert r['bitstreamGenerated'] is False
    assert r['overlayLoaded'] is False
    assert r['physicalPinsResolved'] is False
    assert r['requiresOfficialBoardConstraintReview'] is True
