import math

import pytest

from backend.app.v580 import (
    ADCDACInput,
    BusPlanInput,
    GPIOPlanInput,
    PinAssignment,
    PrototypeScaffoldInput,
    PWMTimerInput,
    RLCInput,
    ResistorNetworkInput,
    SamplingInput,
    SensorModelInput,
    adc_dac_object,
    bus_plan_object,
    gpio_plan_object,
    prototype_scaffold_object,
    pwm_timer_object,
    resistor_network_object,
    rlc_object,
    sampling_object,
    sensor_model_object,
    status_record,
)


def test_status_reports_electronics_embedded_capabilities_and_boundary():
    status = status_record()
    assert status['ok'] is True
    assert status['version'] == '5.8.0'
    for capability in [
        'resistor-network-analysis', 'rlc-impedance-analysis', 'adc-dac-quantization',
        'pwm-timer-planning', 'sampling-nyquist-analysis', 'i2c-spi-uart-planning',
        'sensor-transfer-models', 'gpio-allocation-planning',
        'export-only-embedded-scaffolds', 'canonical-electronics-embedded-objects',
    ]:
        assert capability in status['capabilities']
    assert status['deviceExecutionAuthorized'] is False
    assert status['automaticDeviceProgrammingAuthorized'] is False
    assert status['serialPortAccessAuthorized'] is False
    assert status['gpioAccessAuthorized'] is False
    assert status['jtagAccessAuthorized'] is False


def test_series_resistor_network_obeys_ohms_law_and_power_balance():
    r = resistor_network_object(ResistorNetworkInput(topology='series', resistancesOhm=[100, 200], sourceVoltageV=6))['result']
    assert r['equivalentResistanceOhm'] == pytest.approx(300)
    assert r['totalCurrentA'] == pytest.approx(0.02)
    assert r['totalPowerW'] == pytest.approx(0.12)
    assert r['components'][0]['voltageV'] == pytest.approx(2)
    assert r['components'][1]['voltageV'] == pytest.approx(4)
    assert sum(x['powerW'] for x in r['components']) == pytest.approx(r['totalPowerW'])


def test_parallel_resistor_network_reports_branch_currents():
    r = resistor_network_object(ResistorNetworkInput(topology='parallel', resistancesOhm=[100, 100], sourceVoltageV=5))['result']
    assert r['equivalentResistanceOhm'] == pytest.approx(50)
    assert r['totalCurrentA'] == pytest.approx(0.1)
    assert [x['currentA'] for x in r['components']] == pytest.approx([0.05, 0.05])


def test_rlc_series_reports_resonance_impedance_and_phase():
    L = 10e-3
    C = 1e-6
    f0 = 1 / (2 * math.pi * math.sqrt(L * C))
    r = rlc_object(RLCInput(topology='series', resistanceOhm=100, inductanceH=L, capacitanceF=C, frequencyHz=f0, sourceVoltageV=1))['result']
    assert r['resonantFrequencyHz'] == pytest.approx(f0, rel=1e-10)
    assert r['equivalentImpedance']['magnitude'] == pytest.approx(100, rel=1e-10)
    assert r['equivalentImpedance']['phaseDeg'] == pytest.approx(0, abs=1e-8)
    assert len(r['electronicsEmbeddedObjectHash']) == 64


def test_adc_dac_quantization_and_dac_reconstruction():
    r = adc_dac_object(ADCDACInput(bits=12, referenceVoltageV=3.3, inputVoltageV=1.65, dacCode=2048))['result']
    assert r['maxCode'] == 4095
    assert r['adc']['code'] in (2047, 2048)
    assert abs(r['adc']['quantizationErrorV']) <= r['adc']['idealQuantizationUncertaintyV'] + 1e-12
    assert r['dac']['outputVoltageV'] == pytest.approx(2048 * 3.3 / 4095)


def test_adc_flags_out_of_range_input_as_clipped():
    r = adc_dac_object(ADCDACInput(bits=10, referenceVoltageV=3.3, inputVoltageV=4.2))['result']
    assert r['adc']['clipped'] is True
    assert r['adc']['code'] == 1023


def test_pwm_timer_finds_low_error_configuration():
    r = pwm_timer_object(PWMTimerInput(clockHz=16_000_000, desiredFrequencyHz=1000, dutyCyclePercent=25, counterBits=16, availablePrescalers=[1,8,64,256,1024]))['result']
    s = r['selected']
    assert abs(s['frequencyErrorPpm']) < 1
    assert s['actualFrequencyHz'] == pytest.approx(1000)
    assert s['compareCount'] > 0


def test_pwm_timer_rejects_unrepresentable_frequency():
    with pytest.raises(ValueError):
        pwm_timer_object(PWMTimerInput(clockHz=1_000, desiredFrequencyHz=1e9, counterBits=8, availablePrescalers=[1]))


def test_sampling_plan_distinguishes_nyquist_safe_and_alias_risk():
    safe = sampling_object(SamplingInput(sampleRateHz=10_000, signalBandwidthHz=1000, adcBits=12, durationS=.5))['result']
    risky = sampling_object(SamplingInput(sampleRateHz=1500, signalBandwidthHz=1000, adcBits=12, durationS=.5))['result']
    assert safe['nyquistSatisfied'] is True
    assert safe['oversamplingRatio'] == pytest.approx(5)
    assert safe['sampleCount'] == 5000
    assert risky['nyquistSatisfied'] is False


def test_i2c_bus_plan_accounts_for_ack_overhead():
    r = bus_plan_object(BusPlanInput(protocol='i2c', clockOrBaudHz=400_000, payloadBytes=32, transactionCount=1))['result']
    assert r['wireCountMinimum'] == 2
    assert r['estimatedWireBits'] > 32 * 8
    assert 0 < r['payloadEfficiency'] < 1
    assert r['estimatedTransferTimeS'] > 0


def test_uart_bus_plan_uses_frame_bits():
    r = bus_plan_object(BusPlanInput(protocol='uart', clockOrBaudHz=115200, payloadBytes=10, uartDataBits=8, uartParity='none', uartStopBits=1))['result']
    assert r['estimatedWireBits'] == 100
    assert r['payloadEfficiency'] == pytest.approx(0.8)


def test_linear_and_voltage_divider_sensor_models():
    linear = sensor_model_object(SensorModelInput(model='linear', inputVoltageV=1.2, gainPerVolt=100, offset=-10, outputUnit='C'))['result']
    divider = sensor_model_object(SensorModelInput(model='voltage-divider', inputVoltageV=1.65, supplyVoltageV=3.3, knownResistanceOhm=10_000, sensorPosition='low'))['result']
    assert linear['result']['value'] == pytest.approx(110)
    assert divider['result']['inferredSensorResistanceOhm'] == pytest.approx(10_000)


def test_ntc_beta_model_returns_nominal_temperature_at_nominal_resistance():
    r = sensor_model_object(SensorModelInput(model='ntc-beta', measuredResistanceOhm=10_000, nominalResistanceOhm=10_000, nominalTemperatureC=25, betaK=3950))['result']
    assert r['result']['temperatureC'] == pytest.approx(25, abs=1e-8)


def test_gpio_plan_rejects_duplicate_physical_pin():
    with pytest.raises(ValueError):
        GPIOPlanInput(target='generic', assignments=[
            PinAssignment(signal='a', pin='D1', direction='output'),
            PinAssignment(signal='b', pin='D1', direction='input'),
        ])


def test_gpio_plan_marks_high_voltage_for_board_specific_review():
    r = gpio_plan_object(GPIOPlanInput(target='arduino', assignments=[PinAssignment(signal='sensor', pin='A0', direction='input', voltageV=12, interface='adc')]))['result']
    assert r['conflictFree'] is True
    assert r['boardPinoutValidated'] is False
    assert r['warnings']


@pytest.mark.parametrize('target,extension', [
    ('arduino', '.ino'), ('esp32', '.ino'), ('raspberry-pi', '.py'), ('pynq', '.py'), ('verilog', '.v'), ('vhdl', '.vhd')
])
def test_prototype_scaffolds_are_export_only_and_target_specific(target, extension):
    r = prototype_scaffold_object(PrototypeScaffoldInput(target=target, projectName='demo_project', interface='pwm', sampleRateHz=1000))['result']
    assert r['exportOnly'] is True
    assert r['requiresHumanReviewBeforeExecution'] is True
    assert r['deviceProgrammingPerformed'] is False
    assert r['files'][0]['path'].endswith(extension)
    assert len(r['electronicsEmbeddedObjectHash']) == 64
