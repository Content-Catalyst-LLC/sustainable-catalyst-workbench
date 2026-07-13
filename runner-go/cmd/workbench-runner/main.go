package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/Content-Catalyst-LLC/sustainable-catalyst-workbench/runner-go/internal/runner"
)

const (
	listenAddress  = "127.0.0.1:8787"
	maxBodyBytes   = 256 * 1024
	maxOutputBytes = 256 * 1024
)

type server struct {
	pairingCode string
	nativeExec  bool
	timeout     time.Duration
	mu          sync.RWMutex
	tokens      map[string]string
}

type pairRequest struct {
	Code   string `json:"code"`
	Origin string `json:"origin"`
}

type executeRequest struct {
	Language string `json:"language"`
	Source   string `json:"source"`
	Filename string `json:"filename"`
	Consent  bool   `json:"consent"`
}

type deviceTaskRequest struct {
	Task    string `json:"task"`
	Consent bool   `json:"consent"`
}

type runtimeRecord struct {
	Language  string `json:"language"`
	Command   string `json:"command"`
	Path      string `json:"path,omitempty"`
	Version   string `json:"version,omitempty"`
	Available bool   `json:"available"`
}

func main() {
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "version":
			fmt.Println(runner.Version)
			return
		case "doctor":
			printJSON(map[string]any{"ok": true, "version": runner.Version, "platform": runtime.GOOS + "/" + runtime.GOARCH, "runtimes": discoverRuntimes()})
			return
		case "runtimes":
			printJSON(discoverRuntimes())
			return
		case "devices":
			printJSON(discoverDevices())
			return
		case "hardware-tools":
			printJSON(discoverHardwareTools())
			return
		case "robotics-tools":
			printJSON(discoverRoboticsTools())
			return
		case "instrumentation-tools":
			printJSON(discoverInstrumentationTools())
			return
		case "simulation-tools":
			printJSON(discoverSimulationTools())
			return
		case "multi-language-tools":
			printJSON(discoverMultiLanguageTools())
			return
		case "visualization-tools":
			printJSON(discoverVisualizationTools())
			return
		case "experiment-tools":
			printJSON(discoverExperimentTools())
			return
		case "serve":
			serve(os.Args[2:])
			return
		}
	}
	fmt.Println("Sustainable Catalyst Workbench Runner " + runner.Version)
	fmt.Println("Usage: workbench-runner serve [--enable-native-exec] [--timeout 8s]")
	fmt.Println("       workbench-runner version | doctor | runtimes | devices | hardware-tools | robotics-tools | instrumentation-tools | simulation-tools | multi-language-tools | visualization-tools | experiment-tools")
}

func serve(args []string) {
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	nativeExec := fs.Bool("enable-native-exec", false, "enable structured execution for allowlisted languages")
	timeout := fs.Duration("timeout", 8*time.Second, "maximum execution time")
	_ = fs.Parse(args)

	s := &server{
		pairingCode: sixDigitCode(),
		nativeExec:  *nativeExec,
		timeout:     *timeout,
		tokens:      make(map[string]string),
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.withCORS(s.health))
	mux.HandleFunc("/pair", s.withCORS(s.pair))
	mux.HandleFunc("/runtimes", s.withCORS(s.authorized(s.runtimes)))
	mux.HandleFunc("/devices", s.withCORS(s.authorized(s.devices)))
	mux.HandleFunc("/device-task", s.withCORS(s.authorized(s.deviceTask)))
	mux.HandleFunc("/hardware-tools", s.withCORS(s.authorized(s.hardwareTools)))
	mux.HandleFunc("/hardware-task", s.withCORS(s.authorized(s.hardwareTask)))
	mux.HandleFunc("/robotics-tools", s.withCORS(s.authorized(s.roboticsTools)))
	mux.HandleFunc("/robotics-task", s.withCORS(s.authorized(s.roboticsTask)))
	mux.HandleFunc("/instrumentation-tools", s.withCORS(s.authorized(s.instrumentationTools)))
	mux.HandleFunc("/instrumentation-task", s.withCORS(s.authorized(s.instrumentationTask)))
	mux.HandleFunc("/simulation-tools", s.withCORS(s.authorized(s.simulationTools)))
	mux.HandleFunc("/simulation-task", s.withCORS(s.authorized(s.simulationTask)))
	mux.HandleFunc("/multi-language-tools", s.withCORS(s.authorized(s.multiLanguageTools)))
	mux.HandleFunc("/multi-language-task", s.withCORS(s.authorized(s.multiLanguageTask)))
	mux.HandleFunc("/visualization-tools", s.withCORS(s.authorized(s.visualizationTools)))
	mux.HandleFunc("/visualization-task", s.withCORS(s.authorized(s.visualizationTask)))
	mux.HandleFunc("/experiment-tools", s.withCORS(s.authorized(s.experimentTools)))
	mux.HandleFunc("/experiment-task", s.withCORS(s.authorized(s.experimentTask)))
	mux.HandleFunc("/execute", s.withCORS(s.authorized(s.execute)))

	httpServer := &http.Server{
		Addr:              listenAddress,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       30 * time.Second,
	}

	fmt.Println("Sustainable Catalyst Workbench Runner v" + runner.Version)
	fmt.Println("Listening only on http://" + listenAddress)
	fmt.Println("Pairing code: " + s.pairingCode)
	if s.nativeExec {
		fmt.Println("Native execution: ENABLED (local user permissions; trusted code only)")
	} else {
		fmt.Println("Native execution: disabled (discovery-only mode)")
	}
	fmt.Println("Keep this terminal open while using the browser Workbench.")

	log.Fatal(httpServer.ListenAndServe())
}

func (s *server) withCORS(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin != "" && validBrowserOrigin(origin) {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Vary", "Origin")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		}
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next(w, r)
	}
}

func validBrowserOrigin(origin string) bool {
	parsed, err := url.Parse(origin)
	if err != nil || parsed.Host == "" {
		return false
	}
	return parsed.Scheme == "https" || parsed.Scheme == "http"
}

func (s *server) health(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":                         true,
		"version":                    runner.Version,
		"service":                    "sustainable-catalyst-workbench-runner",
		"listen":                     listenAddress,
		"loopbackOnly":               true,
		"nativeExecutionEnabled":     s.nativeExec,
		"arbitraryShellEndpoint":     false,
		"pairingRequired":            true,
		"platform":                   runtime.GOOS + "/" + runtime.GOARCH,
		"embeddedDeviceStudio":       true,
		"deviceDiscovery":            true,
		"structuredDeviceTasks":      true,
		"fpgaStudio":                 true,
		"electronicsDesign":          true,
		"hardwareValidation":         true,
		"hardwareToolDiscovery":      true,
		"roboticsStudio":             true,
		"controlSimulation":          true,
		"mechatronicsValidation":     true,
		"roboticsToolDiscovery":      true,
		"instrumentationStudio":      true,
		"dataAcquisitionPlanning":    true,
		"signalAnalysis":             true,
		"instrumentToolDiscovery":    true,
		"simulationStudio":           true,
		"digitalTwinStudio":          true,
		"systemsModeling":            true,
		"simulationToolDiscovery":    true,
		"multiLanguageRuntime":       true,
		"languageEquivalence":        true,
		"reproducibilityValidation":  true,
		"multiLanguageToolDiscovery": true,
		"scientificVisualization":    true,
		"engineeringDashboards":      true,
		"validationOverlays":         true,
		"visualizationToolDiscovery": true,
		"experimentAutomation":       true,
		"protocolValidation":         true,
		"workflowReproducibility":    true,
		"experimentToolDiscovery":    true,
	})
}

func (s *server) pair(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	var req pairRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	headerOrigin := r.Header.Get("Origin")
	if req.Code != s.pairingCode {
		writeError(w, http.StatusUnauthorized, "invalid pairing code")
		return
	}
	if !validBrowserOrigin(req.Origin) || headerOrigin == "" || req.Origin != headerOrigin {
		writeError(w, http.StatusBadRequest, "origin mismatch")
		return
	}
	token := randomToken(32)
	s.mu.Lock()
	s.tokens[token] = req.Origin
	s.mu.Unlock()
	s.pairingCode = sixDigitCode()
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":                     true,
		"token":                  token,
		"origin":                 req.Origin,
		"nativeExecutionEnabled": s.nativeExec,
		"message":                "Paired. The terminal now shows a new one-time pairing code.",
	})
	fmt.Println("Browser paired for origin: " + req.Origin)
	fmt.Println("New pairing code: " + s.pairingCode)
}

func (s *server) authorized(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		auth := strings.TrimSpace(strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer "))
		if auth == "" {
			writeError(w, http.StatusUnauthorized, "pairing token required")
			return
		}
		s.mu.RLock()
		origin, ok := s.tokens[auth]
		s.mu.RUnlock()
		if !ok || origin != r.Header.Get("Origin") {
			writeError(w, http.StatusUnauthorized, "invalid or origin-mismatched pairing token")
			return
		}
		next(w, r)
	}
}

func (s *server) runtimes(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":                     true,
		"version":                runner.Version,
		"nativeExecutionEnabled": s.nativeExec,
		"runtimes":               discoverRuntimes(),
	})
}

func (s *server) devices(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":       true,
		"version":  runner.Version,
		"platform": runtime.GOOS + "/" + runtime.GOARCH,
		"devices":  discoverDevices(),
	})
}

func (s *server) hardwareTools(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":      true,
		"version": runner.Version,
		"tools":   discoverHardwareTools(),
		"notes": []string{
			"Availability only confirms that a command is visible to the local user.",
			"Tool versions, target-device support, constraints, licenses, and generated results require project-specific review.",
		},
	})
}

func (s *server) hardwareTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "hardware tasks are disabled; restart with --enable-native-exec")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local hardware task")
		return
	}
	result, err := runHardwareTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func (s *server) deviceTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local device task")
		return
	}
	result, requiresExec, err := runDeviceTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if requiresExec && !s.nativeExec {
		writeError(w, http.StatusForbidden, "this allowlisted device task requires --enable-native-exec")
		return
	}
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func (s *server) execute(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "native execution is disabled; restart with --enable-native-exec")
		return
	}
	var req executeRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit local-execution consent is required")
		return
	}
	if len(req.Source) == 0 || len(req.Source) > 200*1024 {
		writeError(w, http.StatusBadRequest, "source must be between 1 byte and 200 KiB")
		return
	}
	result, err := runSource(r.Context(), s.timeout, strings.ToLower(req.Language), req.Filename, req.Source)
	if err != nil {
		result["ok"] = false
		result["error"] = err.Error()
		writeJSON(w, http.StatusBadRequest, result)
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	writeJSON(w, http.StatusOK, result)
}

func (s *server) roboticsTools(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "version": runner.Version, "tools": discoverRoboticsTools(), "notes": []string{"Discovery only confirms that a command is visible to the local user.", "Robot motion, actuator power, control stability, physical interfaces, and safety functions require hardware-specific validation."}})
}

func (s *server) roboticsTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "robotics tasks are disabled; restart with --enable-native-exec")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local robotics task")
		return
	}
	result, err := runRoboticsTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func discoverRoboticsTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"robotics-ros2", "ros2"}, {"robotics-platformio", "pio"}, {"robotics-arduino-cli", "arduino-cli"},
		{"robotics-openocd", "openocd"}, {"robotics-pigpio", "pigs"}, {"robotics-gpio", "gpiodetect"},
		{"robotics-serial-minicom", "minicom"}, {"robotics-serial-picocom", "picocom"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func runRoboticsTask(parent context.Context, timeout time.Duration, task string) (map[string]any, error) {
	specs := map[string][]string{
		"ros2-version": {"ros2", "--help"}, "platformio-version": {"pio", "--version"}, "arduino-cli-version": {"arduino-cli", "version"},
		"openocd-version": {"openocd", "--version"}, "minicom-version": {"minicom", "--version"}, "picocom-version": {"picocom", "--help"},
	}
	parts, ok := specs[task]
	if !ok {
		return map[string]any{"task": task}, errors.New("robotics task is not allowlisted")
	}
	path, err := exec.LookPath(parts[0])
	if err != nil {
		return map[string]any{"task": task, "command": parts[0]}, fmt.Errorf("tool is not available: %s", parts[0])
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	command := exec.CommandContext(ctx, path, parts[1:]...)
	command.Env = minimalEnvironment(os.TempDir())
	output, commandErr := command.CombinedOutput()
	limited := appendLimited(nil, output, maxOutputBytes)
	if ctx.Err() == context.DeadlineExceeded {
		return map[string]any{"task": task, "output": string(limited)}, errors.New("robotics task timed out")
	}
	if commandErr != nil && len(limited) == 0 {
		return map[string]any{"task": task, "output": string(limited)}, fmt.Errorf("robotics task failed: %w", commandErr)
	}
	return map[string]any{"task": task, "command": parts[0], "path": path, "output": string(limited)}, nil
}

func (s *server) instrumentationTools(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":      true,
		"version": runner.Version,
		"tools":   discoverInstrumentationTools(),
		"notes": []string{
			"Discovery only confirms that a command is visible to the local user.",
			"Instrument voltage, isolation, grounding, probes, sample clocks, calibration, and uncertainty require equipment-specific review.",
		},
	})
}

func (s *server) instrumentationTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "instrumentation tasks are disabled; restart with --enable-native-exec")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local instrumentation task")
		return
	}
	result, err := runInstrumentationTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func discoverInstrumentationTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"instrument-sigrok", "sigrok-cli"},
		{"instrument-pulseview", "pulseview"},
		{"instrument-sox", "sox"},
		{"instrument-ffmpeg", "ffmpeg"},
		{"instrument-rtl-test", "rtl_test"},
		{"instrument-rtl-power", "rtl_power"},
		{"instrument-alsa-record", "arecord"},
		{"instrument-libiio", "iio_info"},
		{"instrument-serial-minicom", "minicom"},
		{"instrument-serial-picocom", "picocom"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func runInstrumentationTask(parent context.Context, timeout time.Duration, task string) (map[string]any, error) {
	specs := map[string][]string{
		"sigrok-version":  {"sigrok-cli", "--version"},
		"sox-version":     {"sox", "--version"},
		"ffmpeg-version":  {"ffmpeg", "-version"},
		"arecord-devices": {"arecord", "-l"},
		"iio-info":        {"iio_info"},
		"minicom-version": {"minicom", "--version"},
		"picocom-version": {"picocom", "--help"},
	}
	parts, ok := specs[task]
	if !ok {
		return map[string]any{"task": task}, errors.New("instrumentation task is not allowlisted")
	}
	path, err := exec.LookPath(parts[0])
	if err != nil {
		return map[string]any{"task": task, "command": parts[0]}, fmt.Errorf("tool is not available: %s", parts[0])
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	command := exec.CommandContext(ctx, path, parts[1:]...)
	command.Env = minimalEnvironment(os.TempDir())
	output, commandErr := command.CombinedOutput()
	limited := appendLimited(nil, output, maxOutputBytes)
	if ctx.Err() == context.DeadlineExceeded {
		return map[string]any{"task": task, "output": string(limited)}, errors.New("instrumentation task timed out")
	}
	if commandErr != nil && len(limited) == 0 {
		return map[string]any{"task": task, "output": string(limited)}, fmt.Errorf("instrumentation task failed: %w", commandErr)
	}
	return map[string]any{"task": task, "command": parts[0], "path": path, "output": string(limited)}, nil
}

func (s *server) simulationTools(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":      true,
		"version": runner.Version,
		"tools":   discoverSimulationTools(),
		"notes": []string{
			"Discovery only confirms that a command is visible to the local user.",
			"Models, solvers, units, parameters, calibration, and boundary conditions require independent validation.",
		},
	})
}

func (s *server) simulationTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "simulation tasks are disabled; restart with --enable-native-exec")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local simulation task")
		return
	}
	result, err := runSimulationTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func (s *server) multiLanguageTools(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":      true,
		"version": runner.Version,
		"tools":   discoverMultiLanguageTools(),
		"executionBoundary": map[string]any{
			"loopbackOnly": true, "pairingRequired": true, "originBoundTokens": true,
			"arbitraryShellEndpoint": false, "maximumSourceBytes": 200 * 1024,
			"maximumOutputBytes": maxOutputBytes, "temporaryWorkingDirectory": true,
		},
		"notes": []string{
			"Availability only confirms that a command is visible to the local user.",
			"Compiler, interpreter, package, ABI, numeric, and platform behavior require project-specific validation.",
		},
	})
}

func (s *server) multiLanguageTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "multi-language tasks are disabled; restart with --enable-native-exec")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local runtime task")
		return
	}
	result, err := runMultiLanguageTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func discoverMultiLanguageTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"python", "python3"}, {"javascript", "node"}, {"r", "Rscript"}, {"sql", "sqlite3"},
		{"go", "go"}, {"c", "cc"}, {"cpp", "c++"}, {"rust", "rustc"}, {"rust-cargo", "cargo"},
		{"haskell", "runhaskell"}, {"haskell-ghc", "ghc"}, {"assembly-nasm", "nasm"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func runMultiLanguageTask(parent context.Context, timeout time.Duration, task string) (map[string]any, error) {
	specs := map[string][]string{
		"python-version": {"python3", "--version"}, "javascript-version": {"node", "--version"},
		"r-version": {"Rscript", "--version"}, "sql-version": {"sqlite3", "--version"},
		"go-version": {"go", "version"}, "c-version": {"cc", "--version"}, "cpp-version": {"c++", "--version"},
		"rust-version": {"rustc", "--version"}, "cargo-version": {"cargo", "--version"},
		"haskell-version": {"runhaskell", "--version"}, "ghc-version": {"ghc", "--version"},
		"nasm-version": {"nasm", "-v"},
	}
	parts, ok := specs[task]
	if !ok {
		return map[string]any{"task": task}, errors.New("runtime task is not allowlisted")
	}
	path, err := exec.LookPath(parts[0])
	if err != nil {
		return map[string]any{"task": task, "command": parts[0]}, fmt.Errorf("runtime is not available: %s", parts[0])
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	command := exec.CommandContext(ctx, path, parts[1:]...)
	command.Env = minimalEnvironment(os.TempDir())
	output, commandErr := command.CombinedOutput()
	limited := appendLimited(nil, output, maxOutputBytes)
	if ctx.Err() == context.DeadlineExceeded {
		return map[string]any{"task": task, "output": string(limited)}, errors.New("runtime task timed out")
	}
	if commandErr != nil && len(limited) == 0 {
		return map[string]any{"task": task, "output": string(limited)}, fmt.Errorf("runtime task failed: %w", commandErr)
	}
	return map[string]any{"task": task, "command": parts[0], "path": path, "output": string(limited)}, nil
}

func (s *server) visualizationTools(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok": true, "version": runner.Version, "tools": discoverVisualizationTools(),
		"executionBoundary": map[string]any{
			"loopbackOnly": true, "pairingRequired": true, "originBoundTokens": true,
			"arbitraryShellEndpoint": false, "allowlistedDiagnosticsOnly": true,
		},
		"notes": []string{
			"Availability only confirms that a visualization command is visible to the current local user.",
			"Chart accuracy, fonts, color profiles, export formats, accessibility, and rendering behavior require project-specific review.",
		},
	})
}

func (s *server) visualizationTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "visualization tasks are disabled; restart with --enable-native-exec")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local visualization task")
		return
	}
	result, err := runVisualizationTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func discoverVisualizationTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"visualization-gnuplot", "gnuplot"}, {"visualization-graphviz", "dot"},
		{"visualization-imagemagick", "magick"}, {"visualization-convert", "convert"},
		{"visualization-inkscape", "inkscape"}, {"visualization-ffmpeg", "ffmpeg"},
		{"visualization-chromium", "chromium"}, {"visualization-chromium-browser", "chromium-browser"},
		{"visualization-python", "python3"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func runVisualizationTask(parent context.Context, timeout time.Duration, task string) (map[string]any, error) {
	specs := map[string][]string{
		"gnuplot-version": {"gnuplot", "--version"}, "graphviz-version": {"dot", "-V"},
		"imagemagick-version": {"magick", "--version"}, "convert-version": {"convert", "--version"},
		"inkscape-version": {"inkscape", "--version"}, "ffmpeg-version": {"ffmpeg", "-version"},
		"chromium-version": {"chromium", "--version"}, "chromium-browser-version": {"chromium-browser", "--version"},
		"python-version": {"python3", "--version"},
	}
	parts, ok := specs[task]
	if !ok {
		return map[string]any{"task": task}, errors.New("visualization task is not allowlisted")
	}
	path, err := exec.LookPath(parts[0])
	if err != nil {
		return map[string]any{"task": task, "command": parts[0]}, fmt.Errorf("visualization tool is not available: %s", parts[0])
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	command := exec.CommandContext(ctx, path, parts[1:]...)
	command.Env = minimalEnvironment(os.TempDir())
	output, commandErr := command.CombinedOutput()
	limited := appendLimited(nil, output, maxOutputBytes)
	if ctx.Err() == context.DeadlineExceeded {
		return map[string]any{"task": task, "output": string(limited)}, errors.New("visualization task timed out")
	}
	if commandErr != nil && len(limited) == 0 {
		return map[string]any{"task": task, "output": string(limited)}, fmt.Errorf("visualization task failed: %w", commandErr)
	}
	return map[string]any{"task": task, "command": parts[0], "path": path, "output": string(limited)}, nil
}

func (s *server) experimentTools(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET required")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok": true, "version": runner.Version, "tools": discoverExperimentTools(),
		"executionBoundary": map[string]any{
			"loopbackOnly": true, "pairingRequired": true, "originBoundTokens": true,
			"arbitraryShellEndpoint": false, "allowlistedDiagnosticsOnly": true,
		},
		"notes": []string{
			"Availability confirms only that a workflow or experiment command is visible to the current local user.",
			"The runner does not install an unattended scheduler, bypass equipment interlocks, or approve an experiment protocol.",
		},
	})
}

func (s *server) experimentTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	if !s.nativeExec {
		writeError(w, http.StatusForbidden, "experiment tasks are disabled; restart with --enable-native-exec")
		return
	}
	var req deviceTaskRequest
	if err := readJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	if !req.Consent {
		writeError(w, http.StatusBadRequest, "explicit consent is required for a local experiment task")
		return
	}
	result, err := runExperimentTask(r.Context(), s.timeout, strings.ToLower(req.Task))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result["ok"] = true
	result["version"] = runner.Version
	result["arbitraryShellEndpoint"] = false
	writeJSON(w, http.StatusOK, result)
}

func discoverExperimentTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"experiment-python", "python3"}, {"experiment-pytest", "pytest"},
		{"experiment-git", "git"}, {"experiment-make", "make"},
		{"experiment-jupyter", "jupyter"}, {"experiment-papermill", "papermill"},
		{"experiment-snakemake", "snakemake"}, {"experiment-nextflow", "nextflow"},
		{"experiment-dvc", "dvc"}, {"experiment-sqlite", "sqlite3"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func runExperimentTask(parent context.Context, timeout time.Duration, task string) (map[string]any, error) {
	specs := map[string][]string{
		"python-version": {"python3", "--version"}, "pytest-version": {"pytest", "--version"},
		"git-version": {"git", "--version"}, "make-version": {"make", "--version"},
		"jupyter-version": {"jupyter", "--version"}, "papermill-version": {"papermill", "--version"},
		"snakemake-version": {"snakemake", "--version"}, "nextflow-version": {"nextflow", "-version"},
		"dvc-version": {"dvc", "--version"}, "sqlite-version": {"sqlite3", "--version"},
	}
	parts, ok := specs[task]
	if !ok {
		return map[string]any{"task": task}, errors.New("experiment task is not allowlisted")
	}
	path, err := exec.LookPath(parts[0])
	if err != nil {
		return map[string]any{"task": task, "command": parts[0]}, fmt.Errorf("experiment tool is not available: %s", parts[0])
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	command := exec.CommandContext(ctx, path, parts[1:]...)
	command.Env = minimalEnvironment(os.TempDir())
	output, commandErr := command.CombinedOutput()
	limited := appendLimited(nil, output, maxOutputBytes)
	if ctx.Err() == context.DeadlineExceeded {
		return map[string]any{"task": task, "output": string(limited)}, errors.New("experiment task timed out")
	}
	if commandErr != nil && len(limited) == 0 {
		return map[string]any{"task": task, "output": string(limited)}, fmt.Errorf("experiment task failed: %w", commandErr)
	}
	return map[string]any{"task": task, "command": parts[0], "path": path, "output": string(limited)}, nil
}

func discoverSimulationTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"simulation-python", "python3"},
		{"simulation-jupyter", "jupyter"},
		{"simulation-ipython", "ipython"},
		{"simulation-r", "Rscript"},
		{"simulation-julia", "julia"},
		{"simulation-octave", "octave"},
		{"simulation-openmodelica", "omc"},
		{"simulation-gnuplot", "gnuplot"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func runSimulationTask(parent context.Context, timeout time.Duration, task string) (map[string]any, error) {
	specs := map[string][]string{
		"python-version":       {"python3", "--version"},
		"jupyter-version":      {"jupyter", "--version"},
		"ipython-version":      {"ipython", "--version"},
		"r-version":            {"Rscript", "--version"},
		"julia-version":        {"julia", "--version"},
		"octave-version":       {"octave", "--version"},
		"openmodelica-version": {"omc", "--version"},
		"gnuplot-version":      {"gnuplot", "--version"},
	}
	parts, ok := specs[task]
	if !ok {
		return map[string]any{"task": task}, errors.New("simulation task is not allowlisted")
	}
	path, err := exec.LookPath(parts[0])
	if err != nil {
		return map[string]any{"task": task, "command": parts[0]}, fmt.Errorf("tool is not available: %s", parts[0])
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	command := exec.CommandContext(ctx, path, parts[1:]...)
	command.Env = minimalEnvironment(os.TempDir())
	output, commandErr := command.CombinedOutput()
	limited := appendLimited(nil, output, maxOutputBytes)
	if ctx.Err() == context.DeadlineExceeded {
		return map[string]any{"task": task, "output": string(limited)}, errors.New("simulation task timed out")
	}
	if commandErr != nil && len(limited) == 0 {
		return map[string]any{"task": task, "output": string(limited)}, fmt.Errorf("simulation task failed: %w", commandErr)
	}
	return map[string]any{"task": task, "command": parts[0], "path": path, "output": string(limited)}, nil
}

func discoverRuntimes() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"python", "python3"}, {"javascript", "node"}, {"r", "Rscript"}, {"sql", "sqlite3"}, {"go", "go"},
		{"c", "cc"}, {"cpp", "c++"}, {"rust", "rustc"}, {"haskell", "runhaskell"},
		{"arduino", "arduino-cli"}, {"fpga-yosys", "yosys"},
		{"fpga-nextpnr", "nextpnr-ice40"}, {"assembly", "nasm"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		rec := runtimeRecord{Language: spec.language, Command: spec.command}
		path, err := exec.LookPath(spec.command)
		if err == nil {
			rec.Available = true
			rec.Path = path
			ctx, cancel := context.WithTimeout(context.Background(), 1200*time.Millisecond)
			versionArgs := []string{"--version"}
			if spec.command == "go" {
				versionArgs = []string{"version"}
			}
			if spec.command == "arduino-cli" {
				versionArgs = []string{"version"}
			}
			b, _ := exec.CommandContext(ctx, spec.command, versionArgs...).CombinedOutput()
			cancel()
			line := strings.Split(strings.TrimSpace(string(b)), "\n")[0]
			if len(line) > 180 {
				line = line[:180]
			}
			rec.Version = line
		}
		out = append(out, rec)
	}
	return out
}

func discoverDevices() map[string]any {
	serialPatterns := []string{"/dev/ttyUSB*", "/dev/ttyACM*", "/dev/serial/by-id/*"}
	if runtime.GOOS == "darwin" {
		serialPatterns = []string{"/dev/cu.*", "/dev/tty.*"}
	}
	interfaces := make([]map[string]any, 0)
	if records, err := net.Interfaces(); err == nil {
		for _, record := range records {
			addresses, _ := record.Addrs()
			values := make([]string, 0, len(addresses))
			for _, address := range addresses {
				values = append(values, address.String())
			}
			interfaces = append(interfaces, map[string]any{
				"name":      record.Name,
				"flags":     record.Flags.String(),
				"addresses": values,
			})
		}
	}
	model := strings.TrimSpace(readSmallFile("/proc/device-tree/model", 512))
	if model == "" {
		model = strings.TrimSpace(readSmallFile("/sys/firmware/devicetree/base/model", 512))
	}
	return map[string]any{
		"raspberryPiModel": model,
		"serial":           globExisting(serialPatterns...),
		"i2c":              globExisting("/dev/i2c-*"),
		"gpio":             globExisting("/dev/gpiochip*"),
		"spi":              globExisting("/dev/spidev*"),
		"video":            globExisting("/dev/video*"),
		"network":          interfaces,
		"toolchains":       discoverEmbeddedTools(),
		"notes": []string{
			"Discovery reports interfaces visible to the current local user.",
			"A listed interface does not establish electrical compatibility, permissions, calibration, or safe operation.",
		},
	}
}

func discoverEmbeddedTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"arduino-cli", "arduino-cli"},
		{"python-smbus", "python3"},
		{"gpio-tools", "gpiodetect"},
		{"i2c-tools", "i2cdetect"},
		{"picotool", "picotool"},
		{"openocd", "openocd"},
		{"esptool", "esptool.py"},
		{"yosys", "yosys"},
		{"nextpnr", "nextpnr-ice40"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func discoverHardwareTools() []runtimeRecord {
	specs := []struct{ language, command string }{
		{"fpga-yosys", "yosys"},
		{"fpga-nextpnr-ice40", "nextpnr-ice40"},
		{"fpga-nextpnr-ecp5", "nextpnr-ecp5"},
		{"fpga-iverilog", "iverilog"},
		{"fpga-verilator", "verilator"},
		{"fpga-ghdl", "ghdl"},
		{"fpga-openfpgaloader", "openFPGALoader"},
		{"fpga-icepack", "icepack"},
		{"hardware-openocd", "openocd"},
		{"hardware-arduino-cli", "arduino-cli"},
		{"hardware-kicad-cli", "kicad-cli"},
	}
	out := make([]runtimeRecord, 0, len(specs))
	for _, spec := range specs {
		record := runtimeRecord{Language: spec.language, Command: spec.command}
		if path, err := exec.LookPath(spec.command); err == nil {
			record.Available = true
			record.Path = path
		}
		out = append(out, record)
	}
	return out
}

func globExisting(patterns ...string) []string {
	seen := make(map[string]bool)
	out := make([]string, 0)
	for _, pattern := range patterns {
		matches, _ := filepath.Glob(pattern)
		for _, match := range matches {
			if seen[match] {
				continue
			}
			if _, err := os.Stat(match); err == nil {
				seen[match] = true
				out = append(out, match)
			}
		}
	}
	sort.Strings(out)
	return out
}

func readSmallFile(path string, limit int64) string {
	file, err := os.Open(path)
	if err != nil {
		return ""
	}
	defer file.Close()
	contents, err := io.ReadAll(io.LimitReader(file, limit))
	if err != nil {
		return ""
	}
	return strings.TrimRight(string(contents), "\x00\r\n ")
}

func runHardwareTask(parent context.Context, timeout time.Duration, task string) (map[string]any, error) {
	specs := map[string][]string{
		"yosys-version":          {"yosys", "-V"},
		"nextpnr-ice40-version":  {"nextpnr-ice40", "--version"},
		"nextpnr-ecp5-version":   {"nextpnr-ecp5", "--version"},
		"iverilog-version":       {"iverilog", "-V"},
		"verilator-version":      {"verilator", "--version"},
		"ghdl-version":           {"ghdl", "--version"},
		"openfpgaloader-version": {"openFPGALoader", "--version"},
		"openocd-version":        {"openocd", "--version"},
		"kicad-cli-version":      {"kicad-cli", "version"},
	}
	parts, ok := specs[task]
	if !ok {
		return map[string]any{"task": task}, errors.New("hardware task is not allowlisted")
	}
	path, err := exec.LookPath(parts[0])
	if err != nil {
		return map[string]any{"task": task, "command": parts[0]}, fmt.Errorf("tool is not available: %s", parts[0])
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	command := exec.CommandContext(ctx, path, parts[1:]...)
	command.Env = minimalEnvironment(os.TempDir())
	output, commandErr := command.CombinedOutput()
	limited := appendLimited(nil, output, maxOutputBytes)
	if ctx.Err() == context.DeadlineExceeded {
		return map[string]any{"task": task, "command": parts[0], "output": string(limited)}, errors.New("hardware task timed out")
	}
	if commandErr != nil {
		return map[string]any{"task": task, "command": parts[0], "output": string(limited)}, fmt.Errorf("hardware task failed: %w", commandErr)
	}
	return map[string]any{"task": task, "command": parts[0], "path": path, "output": string(limited)}, nil
}

func runDeviceTask(parent context.Context, timeout time.Duration, task string) (map[string]any, bool, error) {
	switch task {
	case "raspberry-pi-info":
		return map[string]any{
			"task":           task,
			"model":          strings.TrimSpace(readSmallFile("/proc/device-tree/model", 512)),
			"cpuInfoPreview": readSmallFile("/proc/cpuinfo", 16*1024),
		}, false, nil
	case "serial-list":
		patterns := []string{"/dev/ttyUSB*", "/dev/ttyACM*", "/dev/serial/by-id/*"}
		if runtime.GOOS == "darwin" {
			patterns = []string{"/dev/cu.*", "/dev/tty.*"}
		}
		return map[string]any{"task": task, "interfaces": globExisting(patterns...)}, false, nil
	case "i2c-list":
		return map[string]any{"task": task, "interfaces": globExisting("/dev/i2c-*")}, false, nil
	case "gpio-list":
		return map[string]any{"task": task, "interfaces": globExisting("/dev/gpiochip*")}, false, nil
	case "arduino-board-list":
		path, err := exec.LookPath("arduino-cli")
		if err != nil {
			return map[string]any{"task": task}, true, errors.New("arduino-cli is not available")
		}
		ctx, cancel := context.WithTimeout(parent, timeout)
		defer cancel()
		command := exec.CommandContext(ctx, path, "board", "list", "--format", "json")
		command.Env = minimalEnvironment(os.TempDir())
		output, commandErr := command.CombinedOutput()
		if ctx.Err() == context.DeadlineExceeded {
			return map[string]any{"task": task}, true, errors.New("Arduino board discovery timed out")
		}
		if commandErr != nil {
			return map[string]any{"task": task, "output": string(appendLimited(nil, output, maxOutputBytes))}, true, fmt.Errorf("arduino-cli board list failed: %w", commandErr)
		}
		return map[string]any{"task": task, "output": string(appendLimited(nil, output, maxOutputBytes))}, true, nil
	default:
		return map[string]any{"task": task}, false, errors.New("device task is not allowlisted")
	}
}

func runSource(parent context.Context, timeout time.Duration, language, filename, source string) (map[string]any, error) {
	dir, err := os.MkdirTemp("", "scwb-run-*")
	if err != nil {
		return map[string]any{}, err
	}
	defer os.RemoveAll(dir)

	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()

	ext := map[string]string{"python": ".py", "javascript": ".js", "r": ".R", "sql": ".sql", "go": ".go", "c": ".c", "cpp": ".cpp", "rust": ".rs", "haskell": ".hs"}[language]
	if ext == "" {
		return map[string]any{"language": language}, errors.New("language is not allowlisted")
	}
	if filename == "" || filepath.Ext(filename) != ext {
		filename = "main" + ext
	}
	filename = filepath.Base(filename)
	sourcePath := filepath.Join(dir, filename)
	if err := os.WriteFile(sourcePath, []byte(source), 0600); err != nil {
		return map[string]any{}, err
	}

	var commands [][]string
	switch language {
	case "python":
		commands = [][]string{{"python3", sourcePath}}
	case "javascript":
		commands = [][]string{{"node", sourcePath}}
	case "r":
		commands = [][]string{{"Rscript", sourcePath}}
	case "sql":
		commands = [][]string{{"sqlite3", ":memory:", ".read " + sourcePath}}
	case "haskell":
		commands = [][]string{{"runhaskell", sourcePath}}
	case "go":
		commands = [][]string{{"go", "run", sourcePath}}
	case "c":
		bin := filepath.Join(dir, "program")
		commands = [][]string{{"cc", "-O0", "-std=c11", sourcePath, "-o", bin}, {bin}}
	case "cpp":
		bin := filepath.Join(dir, "program")
		commands = [][]string{{"c++", "-O0", "-std=c++17", sourcePath, "-o", bin}, {bin}}
	case "rust":
		bin := filepath.Join(dir, "program")
		commands = [][]string{{"rustc", sourcePath, "-o", bin}, {bin}}
	}

	started := time.Now()
	combined := make([]byte, 0, 4096)
	for _, parts := range commands {
		if _, err := exec.LookPath(parts[0]); err != nil {
			return map[string]any{"language": language}, fmt.Errorf("runtime not available: %s", parts[0])
		}
		cmd := exec.CommandContext(ctx, parts[0], parts[1:]...)
		cmd.Dir = dir
		cmd.Env = minimalEnvironment(dir)
		output, runErr := cmd.CombinedOutput()
		combined = appendLimited(combined, output, maxOutputBytes)
		if ctx.Err() == context.DeadlineExceeded {
			return map[string]any{"language": language, "output": string(combined), "durationMs": time.Since(started).Milliseconds()}, errors.New("execution timed out")
		}
		if runErr != nil {
			return map[string]any{"language": language, "output": string(combined), "durationMs": time.Since(started).Milliseconds()}, fmt.Errorf("command failed: %w", runErr)
		}
	}
	return map[string]any{"language": language, "output": string(combined), "durationMs": time.Since(started).Milliseconds(), "truncated": len(combined) >= maxOutputBytes}, nil
}

func minimalEnvironment(workdir string) []string {
	allowed := []string{"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "WINDIR"}
	env := []string{"SC_WORKBENCH_RUNNER=1", "PWD=" + workdir}
	for _, key := range allowed {
		if value, ok := os.LookupEnv(key); ok {
			env = append(env, key+"="+value)
		}
	}
	return env
}

func appendLimited(dst, src []byte, limit int) []byte {
	remaining := limit - len(dst)
	if remaining <= 0 {
		return dst
	}
	if len(src) > remaining {
		src = src[:remaining]
	}
	return append(dst, src...)
}

func readJSON(r *http.Request, target any) error {
	if !strings.HasPrefix(r.Header.Get("Content-Type"), "application/json") {
		return errors.New("Content-Type application/json required")
	}
	limited := io.LimitReader(r.Body, maxBodyBytes+1)
	dec := json.NewDecoder(limited)
	dec.DisallowUnknownFields()
	if err := dec.Decode(target); err != nil {
		return fmt.Errorf("invalid JSON: %w", err)
	}
	var extra any
	if err := dec.Decode(&extra); err != io.EOF {
		return errors.New("request must contain one JSON object")
	}
	return nil
}

func sixDigitCode() string {
	var b [4]byte
	if _, err := rand.Read(b[:]); err != nil {
		return fmt.Sprintf("%06d", time.Now().UnixNano()%1000000)
	}
	n := int(b[0])<<24 | int(b[1])<<16 | int(b[2])<<8 | int(b[3])
	if n < 0 {
		n = -n
	}
	return fmt.Sprintf("%06d", n%1000000)
}

func randomToken(bytes int) string {
	b := make([]byte, bytes)
	if _, err := rand.Read(b); err != nil {
		return strconv.FormatInt(time.Now().UnixNano(), 16)
	}
	return hex.EncodeToString(b)
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]any{"ok": false, "error": message})
}
func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}
func printJSON(value any) { b, _ := json.MarshalIndent(value, "", "  "); fmt.Println(string(b)) }
