import math

import pytest

from backend.app.v570 import (
    ConvolutionInput,
    FilterDesignInput,
    PIDInput,
    RootLocusInput,
    SpectrumInput,
    StateSpaceInput,
    TransferFunctionInput,
    convolution_object,
    filter_design_object,
    pid_object,
    root_locus_object,
    spectrum_object,
    state_space_object,
    status_record,
    transfer_function_object,
)


def test_status_reports_signals_systems_control_capabilities_and_boundary():
    status = status_record()
    assert status['ok'] is True
    assert status['version'] == '5.7.0'
    for capability in [
        'fft-spectrum-analysis', 'digital-filter-design', 'continuous-transfer-functions',
        'root-locus', 'state-space-analysis', 'pid-closed-loop-simulation',
        'canonical-signals-control-objects',
    ]:
        assert capability in status['capabilities']
    assert status['arbitraryCodeExecutionAuthorized'] is False
    assert status['pythonEvalAuthorized'] is False
    assert status['remoteShellAuthorized'] is False
    assert status['deviceExecutionAuthorized'] is False


def test_fft_spectrum_detects_fundamental_and_harmonic_ratio():
    sample_rate = 1024
    values = [
        math.sin(2 * math.pi * 64 * n / sample_rate)
        + 0.2 * math.sin(2 * math.pi * 128 * n / sample_rate)
        for n in range(sample_rate)
    ]
    result = spectrum_object(SpectrumInput(values=values, sampleRateHz=sample_rate, window='hann'))['result']
    assert result['fundamentalHz'] == pytest.approx(64.0, abs=1e-10)
    assert result['totalHarmonicDistortionRatio'] == pytest.approx(0.2, rel=0.02)
    assert result['peaks'][0]['frequencyHz'] == pytest.approx(64.0)
    assert len(result['signalsControlObjectHash']) == 64


def test_convolution_supports_normalized_same_mode():
    result = convolution_object(ConvolutionInput(signal=[1, 2, 3, 2, 1], kernel=[1, 2, 1], mode='same', normalizeKernel=True))['result']
    assert result['normalizedKernel'] is True
    assert result['kernelUsed'] == pytest.approx([0.25, 0.5, 0.25])
    assert len(result['output']) == 5
    assert result['output'][2] == pytest.approx(2.5)


def test_butterworth_lowpass_is_stable_and_attenuates_high_frequency():
    result = filter_design_object(FilterDesignInput(
        family='butterworth', response='lowpass', order=4, sampleRateHz=1000, cutoffHz=[100], responsePoints=401
    ))['result']
    assert result['stable'] is True
    assert len(result['secondOrderSections']) == 2
    low = min(result['frequencyResponse'], key=lambda p: abs(p['frequencyHz'] - 20))
    high = min(result['frequencyResponse'], key=lambda p: abs(p['frequencyHz'] - 400))
    assert low['magnitudeDb'] > -1.0
    assert high['magnitudeDb'] < -20.0


def test_filter_rejects_cutoff_at_or_above_nyquist():
    with pytest.raises(ValueError):
        FilterDesignInput(sampleRateHz=1000, cutoffHz=[500])


def test_first_order_transfer_function_reports_stability_bode_and_step():
    result = transfer_function_object(TransferFunctionInput(
        numerator=[1], denominator=[1, 1], frequencyMinHz=0.01, frequencyMaxHz=10, timeDurationS=8, timeSamples=401
    ))['result']
    assert result['stable'] is True
    assert result['dcGain'] == pytest.approx(1.0)
    assert len(result['bode']) == 401
    assert result['step'][-1]['value'] == pytest.approx(1.0, rel=5e-4)
    assert result['poles'][0]['real'] == pytest.approx(-1.0)


def test_unstable_transfer_function_is_flagged():
    result = transfer_function_object(TransferFunctionInput(numerator=[1], denominator=[1, -1], timeDurationS=1, timeSamples=64))['result']
    assert result['stable'] is False
    assert result['poles'][0]['real'] > 0


def test_state_space_reports_controllability_observability_and_step():
    result = state_space_object(StateSpaceInput(A=[[0, 1], [-2, -3]], B=[0, 1], C=[1, 0], D=0, durationS=8, samples=401))['result']
    assert result['stable'] is True
    assert result['fullyControllable'] is True
    assert result['fullyObservable'] is True
    assert result['controllabilityRank'] == 2
    assert result['observabilityRank'] == 2
    assert len(result['step']) == 401


def test_state_space_can_report_rank_deficiency_without_claiming_full_control():
    result = state_space_object(StateSpaceInput(A=[[-1, 0], [0, -2]], B=[1, 0], C=[1, 0], D=0, durationS=2, samples=64))['result']
    assert result['fullyControllable'] is False
    assert result['fullyObservable'] is False


def test_pid_closed_loop_produces_stable_response_and_metrics():
    result = pid_object(PIDInput(
        plantNumerator=[1], plantDenominator=[1, 1], kp=2, ki=1, kd=0.1, setpoint=1, durationS=12, samples=601
    ))['result']
    assert result['stable'] is True
    assert result['metrics']['steadyStateError'] == pytest.approx(0, abs=0.01)
    assert result['metrics']['integralAbsoluteError'] > 0
    assert len(result['step']) == 601
    assert len(result['signalsControlObjectHash']) == 64


def test_pid_rejects_all_zero_gains():
    with pytest.raises(ValueError):
        PIDInput(plantNumerator=[1], plantDenominator=[1, 1], kp=0, ki=0, kd=0)


def test_root_locus_samples_closed_loop_poles_over_gain_range():
    result = root_locus_object(RootLocusInput(numerator=[1], denominator=[1, 3, 2, 0], gainMin=0, gainMax=60, gainPoints=31))['result']
    assert len(result['locus']) == 31
    assert result['locus'][0]['gain'] == pytest.approx(0)
    assert result['locus'][-1]['gain'] == pytest.approx(60)
    assert all('poles' in item and item['poles'] for item in result['locus'])
    assert len(result['signalsControlObjectHash']) == 64
