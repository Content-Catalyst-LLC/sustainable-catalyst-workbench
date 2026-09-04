import math
import pytest
from fastapi import HTTPException

from backend.app.v530 import (
    BlackboardInput,
    MusicInput,
    FormInput,
    PrototypeInput,
    status_record,
    translate_blackboard,
    music_math,
    creative_form,
    prototype,
)


def test_v530_status_and_execution_boundary():
    s = status_record()
    assert s['version'] == '5.3.0'
    for cap in ['computational-blackboard', 'music-acoustics-mathematics', 'creative-mathematics', 'pynq', 'verilog', 'vhdl']:
        assert cap in s['capabilities']
    assert s['arbitraryCodeExecutionAuthorized'] is False
    assert s['remoteShellAuthorized'] is False
    assert s['deviceExecutionAuthorized'] is False
    assert s['automaticDeviceProgrammingAuthorized'] is False


def test_blackboard_definite_integral_translation_is_exact():
    r = translate_blackboard(BlackboardInput(input='integrate x^2 from 0 to 3'))['result']
    assert r['operation'] == 'definite-integral'
    assert r['exactText'] == '9'
    assert 'Integral' in r['translatedExpression']
    assert '⌠' in r['translatedPretty'] or 'Integral' in r['translatedPretty']
    assert len(r['objectHash']) == 64


def test_blackboard_derivative_and_equation_solve():
    d = translate_blackboard(BlackboardInput(input='d/dx sin(x)*exp(x)'))['result']
    assert d['operation'] == 'differentiate'
    assert d['exactText'] == 'exp(x)*sin(x) + exp(x)*cos(x)'
    s = translate_blackboard(BlackboardInput(input='solve x^2+4*x-12=0 for x'))['result']
    assert s['solutionCount'] == 2
    assert [item['exact'] for item in s['solutions']] == ['-6', '2']


def test_blackboard_rejects_python_constructs():
    with pytest.raises(HTTPException):
        translate_blackboard(BlackboardInput(input="__import__('os').system('id')"))


def test_music_note_frequency_wavelength_and_harmonics():
    r = music_math(MusicInput(mode='note', note='A4', harmonics=8))['result']
    assert abs(r['frequencyHz'] - 440.0) < 1e-9
    assert r['nearestNote'] == 'A4'
    assert abs(r['wavelengthMeters'] - 343 / 440) < 1e-9
    assert len(r['harmonics']) == 8
    assert r['harmonics'][1]['frequencyHz'] == 880.0
    assert len(r['waveformSamples']) == 181


def test_music_interval_cents():
    r = music_math(MusicInput(mode='interval', frequencyHz=440, secondFrequencyHz=660))['result']
    assert abs(r['interval']['ratio'] - 1.5) < 1e-12
    assert 701 < r['interval']['cents'] < 703


def test_creative_form_is_bounded_and_hashed():
    r = creative_form(FormInput(family='lissajous', a=3, b=2, phase=.5, points=401))['result']
    assert r['pointCount'] == 401
    assert r['extent'] <= 1.000000001
    assert len(r['objectHash']) == 64
    assert all(math.isfinite(p['x']) and math.isfinite(p['y']) for p in r['points'])


def test_pynq_and_hdl_scaffolds_are_export_only():
    pynq = prototype(PrototypeInput(target='pynq', projectName='tone_overlay', signalFrequencyHz=440))['result']
    assert pynq['filename'] == 'pynq_overlay.py'
    assert 'from pynq import Overlay' in pynq['code']
    assert pynq['execution'] == 'export-only'
    assert pynq['programmingAuthorized'] is False
    verilog = prototype(PrototypeInput(target='verilog', projectName='tone', signalFrequencyHz=1000, clockMHz=100))['result']
    assert verilog['filename'] == 'tone.v'
    assert 'module tone' in verilog['code']
    assert 'HALF_CYCLES' in verilog['code']


def test_prototype_target_is_allowlisted_by_schema():
    with pytest.raises(Exception):
        PrototypeInput(target='shell')
