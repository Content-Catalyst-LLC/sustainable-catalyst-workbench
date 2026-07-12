# Sustainable Catalyst Prototyping Workbench v2.4.0

## Instrumentation, Data Acquisition, and Signal Analysis Studio

Version 2.4.0 extends the Workbench from robotics and hardware validation into measurement engineering, instrument planning, acquisition design, signal analysis, calibration, uncertainty, and traceable measurement review.

## New WordPress modules

- `[sc_workbench_instrumentation_studio project="default"]`
- `[sc_workbench_data_acquisition project="default"]`
- `[sc_workbench_signal_analysis project="default"]`
- `[sc_workbench_frequency_analysis project="default"]`
- `[sc_workbench_calibration_uncertainty project="default"]`
- `[sc_workbench_measurement_validation project="default"]`

## Browser-local capabilities

- Instrument span, accuracy, ADC resolution, quantization-step, bandwidth, interface, and isolation review
- Sample-rate, Nyquist, throughput, buffer, storage, timestamp, channel-skew, and anti-alias planning
- Time-domain mean, RMS, standard deviation, peak-to-peak, crest factor, drift, noise, and SNR estimates
- Moving-average filtering and compact signal previews
- Hann, Hamming, and rectangular-window spectrum analysis with dominant-frequency and top-peak records
- Linear calibration regression, residuals, R², RMSE, standard uncertainty, combined uncertainty, and expanded uncertainty
- Timestamp monotonicity, sample-rate accuracy, jitter, missing-data, channel-statistics, and provenance checks
- Local JSON project and result exports

## FastAPI routes

- `GET /api/v2.4/status`
- `POST /api/v2.4/instrumentation/review`
- `POST /api/v2.4/acquisition/plan`
- `POST /api/v2.4/signals/analyze`
- `POST /api/v2.4/frequency/analyze`
- `POST /api/v2.4/calibration/fit`
- `POST /api/v2.4/measurements/validate`

## Local runner additions

- `workbench-runner instrumentation-tools`
- `GET /instrumentation-tools`
- `POST /instrumentation-task`

The runner discovers supported local tools such as sigrok-cli, PulseView, SoX, FFmpeg, RTL-SDR utilities, ALSA capture, libiio, minicom, and picocom. Discovery does not grant browser shell access. Local tasks remain paired, consent-gated, allowlisted, loopback-only, and disabled unless the runner is launched with `--enable-native-exec`.

## Compatibility

Version 2.4.0 preserves existing calculator, Code Studio, research notebook, hardware, Raspberry Pi, TinyML, FPGA, electronics, robotics, controls, local storage, REST, and shortcode interfaces from v1.9.1 through v2.3.0.

## Responsible-use boundary

Workbench measurement outputs are analytical aids, not calibration certificates or safety approvals. Validate instrument ratings, electrical isolation, grounding, probes, sample clocks, anti-alias filters, traceability, uncertainty models, environmental conditions, and safety-critical measurements against actual equipment and applicable standards.
