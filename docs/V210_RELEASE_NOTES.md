# Sustainable Catalyst Prototyping Workbench v2.1.0

## Raspberry Pi, TinyML, and Embedded Device Studio

Workbench v2.1.0 turns the v2.0.0 hardware foundation into a connected embedded-development workflow. The release keeps the existing calculators, Code Studio, Research Lab, notebook, documentation, Arduino, schematic, BOM, PCB, assembly, FPGA, storage keys, and local runner pairing model.

## New WordPress modules

- `[sc_workbench_embedded_device_studio project="default"]`
- `[sc_workbench_raspberry_pi project="default"]`
- `[sc_workbench_tinyml project="default"]`
- `[sc_workbench_sensor_calibration project="default"]`
- `[sc_workbench_device_logs project="default"]`
- `[sc_workbench_embedded_board_catalog project="default"]`

The v2.1.0 module launcher is also appended to the existing v2.0.0 Hardware Studio.

## Raspberry Pi Studio

- Raspberry Pi 5, Raspberry Pi 4, Raspberry Pi Zero 2 W, and Raspberry Pi 3 profiles
- GPIO, I²C, SPI, serial, network, and camera project planning
- Python acquisition-service generation
- Machine-readable project manifest
- Browser-local project persistence
- Exportable JSON project bundle and Python service
- Validation gates for power, permissions, calibration, storage, network, privacy, and failure behavior

## TinyML Studio

- CSV parser with schema and numerical-feature validation
- Classification and regression modes
- Deterministic train/test split for pipeline checks
- Nearest-centroid classification baseline
- Univariate linear-regression baseline
- Accuracy, RMSE, R², and feature-statistics records
- INT8 symmetric quantization preview and Float16 planning
- Model-card export
- C deployment scaffold export
- Complete browser-local TinyML project bundle

The browser baseline is intentionally transparent and reproducible. It is not a substitute for a reviewed production training pipeline.

## Sensor and device records

- Linear sensor calibration from reference/measured pairs
- Slope, intercept, residuals, RMSE, and R²
- Calibration record export
- Browser-local timestamped device observation log
- CSV log export
- Expanded embedded board catalog spanning Raspberry Pi, Arduino Nicla, Portenta, MKR, ESP32-compatible, Seeed, Adafruit, ST, and open FPGA profiles

## Go Runner v2.1.0

New paired endpoints:

- `GET /devices`
- `POST /device-task`

New command:

- `workbench-runner devices`

Device discovery reports interfaces visible to the current local user, including serial, I²C, GPIO, SPI, video, network, Raspberry Pi identity, and embedded toolchain availability. The device-task endpoint accepts only named allowlisted operations. It does not accept shell text or arbitrary commands.

The `arduino-board-list` task requires the runner to be started with `--enable-native-exec`. File-based discovery tasks do not execute a shell.

## FastAPI routes

- `GET /workbench/v2.1.0/status`
- `GET /workbench/v2.1.0/boards`
- `POST /workbench/v2.1.0/calibration/linear`
- `POST /workbench/v2.1.0/tinyml/prepare`
- `POST /workbench/v2.1.0/projects/raspberry-pi`
- `POST /workbench/v2.1.0/projects/tinyml`

## Compatibility

- v2.0.0 Research Lab and Hardware Studio remain active.
- Existing WordPress shortcodes remain unchanged.
- Existing browser-local project records are not deleted or migrated.
- The v2.0.0 runner pairing token is reused for the same project and browser origin.
- Native execution remains disabled by default.
