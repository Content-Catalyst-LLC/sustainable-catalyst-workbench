(() => {
'use strict';
const CFG = window.SCWBV240 || {version:'2.4.0',storagePrefix:'scwb-v240:'};
const q = (root, selector) => root.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
const round = (value, digits = 4) => Number.isFinite(value) ? Number(value.toFixed(digits)) : 'N/A';
const field = (root, name) => q(root, `[data-scwb-v240-field="${name}"]`);
const text = (root, name) => (field(root, name)?.value || '').trim();
const number = (root, name, fallback = 0) => {
  const value = Number(field(root, name)?.value);
  return Number.isFinite(value) ? value : fallback;
};
const allFields = root => Object.fromEntries([...root.querySelectorAll('[data-scwb-v240-field]')].map(el => [el.dataset.scwbV240Field, el.value]));
const storageKey = root => `${CFG.storagePrefix}${root.dataset.scwbV240Project}:${root.dataset.scwbV240Panel}`;
const setStatus = (root, message) => { const el = q(root, '[data-scwb-v240-status]'); if (el) el.textContent = message; };
const save = root => {
  localStorage.setItem(storageKey(root), JSON.stringify({version:CFG.version,savedAt:new Date().toISOString(),fields:allFields(root)}));
  setStatus(root, 'Saved locally');
};
const load = root => {
  try {
    const payload = JSON.parse(localStorage.getItem(storageKey(root)) || 'null');
    if (!payload) return;
    Object.entries(payload.fields || {}).forEach(([name, value]) => { const el = field(root, name); if (el) el.value = value; });
  } catch (error) { /* Ignore malformed local drafts. */ }
};
const download = (name, payload) => {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'});
  const anchor = document.createElement('a');
  anchor.href = URL.createObjectURL(blob);
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
};
const finding = (level, message, code = '') => ({level, message, code});
const mean = values => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : NaN;
const variance = values => {
  if (values.length < 2) return 0;
  const m = mean(values);
  return values.reduce((sum, value) => sum + (value - m) ** 2, 0) / (values.length - 1);
};
const stddev = values => Math.sqrt(variance(values));
const rms = values => values.length ? Math.sqrt(values.reduce((sum, value) => sum + value * value, 0) / values.length) : NaN;
const linearFit = (x, y) => {
  const n = Math.min(x.length, y.length);
  if (n < 2) return {slope:NaN,intercept:NaN,r2:NaN,rmse:NaN,residuals:[]};
  const mx = mean(x), my = mean(y);
  let sxx = 0, sxy = 0, syy = 0;
  for (let i = 0; i < n; i += 1) { const dx = x[i] - mx, dy = y[i] - my; sxx += dx * dx; sxy += dx * dy; syy += dy * dy; }
  const slope = sxx > 0 ? sxy / sxx : NaN;
  const intercept = my - slope * mx;
  const residuals = y.map((value, index) => value - (slope * x[index] + intercept));
  const sse = residuals.reduce((sum, value) => sum + value * value, 0);
  return {slope,intercept,r2:syy > 0 ? 1 - sse / syy : 1,rmse:Math.sqrt(sse / n),residuals};
};
const parseLines = source => source.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
const parseNumericSeries = source => {
  const lines = parseLines(source);
  const values = [];
  let invalid = 0;
  lines.forEach((line, index) => {
    const cells = line.split(',').map(cell => cell.trim());
    const candidates = cells.map(Number).filter(Number.isFinite);
    if (!candidates.length) { if (index > 0 || !/[a-z]/i.test(line)) invalid += 1; return; }
    values.push(candidates[candidates.length - 1]);
  });
  return {values,invalid};
};
const parseTimeValue = (source, sampleRate) => {
  const lines = parseLines(source);
  const time = [], values = [];
  let invalid = 0;
  lines.forEach((line, index) => {
    const cells = line.split(',').map(cell => cell.trim());
    if (index === 0 && cells.some(cell => /[a-z]/i.test(cell))) return;
    if (cells.length >= 2 && Number.isFinite(Number(cells[0])) && Number.isFinite(Number(cells[1]))) {
      time.push(Number(cells[0])); values.push(Number(cells[1]));
    } else if (Number.isFinite(Number(cells[0]))) {
      time.push(values.length / Math.max(sampleRate, 1e-12)); values.push(Number(cells[0]));
    } else invalid += 1;
  });
  return {time,values,invalid};
};
const parseTable = source => {
  const lines = parseLines(source);
  if (!lines.length) return {headers:[],rows:[],invalid:0};
  const first = lines[0].split(',').map(cell => cell.trim());
  const hasHeader = first.some(cell => !Number.isFinite(Number(cell)));
  const headers = hasHeader ? first : first.map((_, index) => `column_${index + 1}`);
  const dataLines = hasHeader ? lines.slice(1) : lines;
  let invalid = 0;
  const rows = dataLines.map(line => {
    const cells = line.split(',').map(cell => cell.trim());
    const row = {};
    headers.forEach((header, index) => {
      const value = Number(cells[index]);
      row[header] = Number.isFinite(value) ? value : null;
      if (!Number.isFinite(value)) invalid += 1;
    });
    return row;
  });
  return {headers,rows,invalid};
};
const movingAverage = (values, width) => {
  const window = Math.max(1, Math.floor(width));
  const out = [];
  let sum = 0;
  for (let i = 0; i < values.length; i += 1) {
    sum += values[i];
    if (i >= window) sum -= values[i - window];
    out.push(sum / Math.min(window, i + 1));
  }
  return out;
};
const detrend = (time, values, mode) => {
  if (mode === 'none') return [...values];
  if (mode === 'linear') {
    const fit = linearFit(time, values);
    return values.map((value, index) => value - (fit.slope * time[index] + fit.intercept));
  }
  const m = mean(values);
  return values.map(value => value - m);
};
const chartLine = values => {
  if (!values || values.length < 2) return '';
  const width = 760, height = 170, pad = 10;
  const min = Math.min(...values), max = Math.max(...values), span = max - min || 1;
  const points = values.map((value, index) => {
    const x = pad + index * (width - 2 * pad) / Math.max(1, values.length - 1);
    const y = height - pad - (value - min) * (height - 2 * pad) / span;
    return `${round(x,2)},${round(y,2)}`;
  }).join(' ');
  return `<svg class="scwb-v240__chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Signal preview"><line class="scwb-v240__chart-grid" x1="10" y1="85" x2="750" y2="85"></line><polyline class="scwb-v240__chart-line" points="${points}"></polyline></svg>`;
};
const chartBars = spectrum => {
  if (!spectrum || !spectrum.length) return '';
  const width = 760, height = 170, pad = 10;
  const slice = spectrum.slice(0, 96);
  const max = Math.max(...slice.map(item => item.amplitude), 1e-12);
  const barWidth = (width - 2 * pad) / slice.length;
  const bars = slice.map((item, index) => {
    const h = item.amplitude / max * (height - 2 * pad);
    return `<rect class="scwb-v240__chart-bar" x="${round(pad + index * barWidth,2)}" y="${round(height - pad - h,2)}" width="${Math.max(.8,barWidth - .6)}" height="${round(h,2)}"></rect>`;
  }).join('');
  return `<svg class="scwb-v240__chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Frequency spectrum preview">${bars}</svg>`;
};
const render = (root, title, metrics, findings = [], extra = '') => {
  const results = q(root, '[data-scwb-v240-results]');
  const metricHtml = Object.entries(metrics).map(([label, value]) => `<div class="scwb-v240__metric"><strong>${esc(label)}</strong>${esc(value)}</div>`).join('');
  const findingHtml = findings.length ? `<ul>${findings.map(item => `<li class="${item.level === 'fail' ? 'fail' : item.level === 'warn' ? 'warn' : 'pass'}">${esc(item.message)}</li>`).join('')}</ul>` : '<p class="pass">No blocking review findings were generated.</p>';
  results.innerHTML = `<h3>${esc(title)}</h3><div class="scwb-v240__metric-grid">${metricHtml}</div>${extra}${findingHtml}`;
  setStatus(root, findings.some(item => item.level === 'fail') ? 'Review required' : 'Ready');
};

function instrumentation(root) {
  const min = number(root,'range_min'), max = number(root,'range_max'), expectedMin = number(root,'expected_min'), expectedMax = number(root,'expected_max');
  const bits = Math.floor(number(root,'resolution_bits',12)), accuracy = Math.abs(number(root,'accuracy_percent',0)), bandwidth = number(root,'bandwidth_hz',0);
  const range = max - min, codes = bits > 0 && bits <= 32 ? 2 ** bits : NaN, lsb = range > 0 ? range / Math.max(1,codes - 1) : NaN;
  const accuracyAbs = Math.abs(range) * accuracy / 100, expectedSpan = expectedMax - expectedMin, utilization = range > 0 ? expectedSpan / range * 100 : NaN;
  const findings = [];
  if (!(range > 0)) findings.push(finding('fail','Instrument range maximum must exceed range minimum.','invalid-range'));
  if (!(bits >= 4 && bits <= 32)) findings.push(finding('fail','ADC resolution must be between 4 and 32 bits.','invalid-resolution'));
  if (expectedMin < min || expectedMax > max) findings.push(finding('fail','Expected signal limits extend outside the stated instrument range.','range-exceeded'));
  if (expectedSpan <= 0) findings.push(finding('fail','Expected signal maximum must exceed expected signal minimum.','invalid-expected-span'));
  if (utilization < 10) findings.push(finding('warn','Expected signal uses less than 10% of the instrument span; effective resolution may be poor.','low-range-utilization'));
  if (bandwidth <= 0) findings.push(finding('fail','Instrument bandwidth must be positive.','invalid-bandwidth'));
  if (text(root,'isolation_required') === 'yes' && !/(isolat|differential|4-20|current)/i.test(text(root,'interface'))) findings.push(finding('warn','Isolation is marked required, but the interface description does not identify an isolation method.','isolation-review'));
  return {
    kind:'instrumentation',
    metrics:{'Full-scale span':`${round(range,6)} ${text(root,'units')}`,'Quantization step':`${round(lsb,8)} ${text(root,'units')}`,'Accuracy allowance':`±${round(accuracyAbs,6)} ${text(root,'units')}`,'Expected span use':`${round(utilization,2)}%`,'Minimum sample rate':`${round(2.5 * bandwidth,2)} Hz`,'Nominal codes in expected span':round(expectedSpan / lsb,0)},
    findings,
    data:{instrumentName:text(root,'instrument_name'),instrumentType:text(root,'instrument_type'),units:text(root,'units'),rangeMin:min,rangeMax:max,accuracyPercentFullScale:accuracy,resolutionBits:bits,bandwidthHz:bandwidth,expectedMin,expectedMax,quantizationStep:lsb,recommendedMinimumSampleRateHz:2.5*bandwidth}
  };
}

function acquisition(root) {
  const channels = Math.floor(number(root,'channels',1)), rate = number(root,'sample_rate'), duration = number(root,'duration'), bits = Math.floor(number(root,'bit_depth',16));
  const overhead = Math.max(0,number(root,'overhead_percent')) / 100, maxFrequency = number(root,'expected_max_frequency'), bufferSeconds = number(root,'buffer_seconds'), storageMB = number(root,'available_storage_mb');
  const bytesPerSample = Math.ceil(bits / 8), samplesPerChannel = rate * duration, totalSamples = samplesPerChannel * channels;
  const rawBytes = totalSamples * bytesPerSample, totalBytes = rawBytes * (1 + overhead), throughput = rate * channels * bytesPerSample * (1 + overhead), bufferBytes = throughput * bufferSeconds;
  const nyquist = rate / 2, findings = [];
  if (channels < 1 || channels > 256) findings.push(finding('fail','Channel count must be between 1 and 256.','invalid-channel-count'));
  if (!(rate > 0 && duration > 0)) findings.push(finding('fail','Sample rate and duration must be positive.','invalid-acquisition-time'));
  if (!(bits >= 8 && bits <= 32)) findings.push(finding('fail','ADC bit depth must be between 8 and 32 bits.','invalid-bit-depth'));
  if (rate < 2.5 * maxFrequency) findings.push(finding('fail','Sample rate is below the 2.5× engineering margin for the expected maximum signal frequency.','alias-risk'));
  if (number(root,'filter_cutoff') >= nyquist) findings.push(finding('warn','Anti-alias filter cutoff is at or above Nyquist.','filter-cutoff'));
  if (totalBytes > storageMB * 1024 * 1024) findings.push(finding('fail','Estimated acquisition size exceeds the stated available storage.','storage-exceeded'));
  if (text(root,'sampling_mode') === 'multiplexed' && channels > 1) findings.push(finding('warn','Multiplexed channels may have inter-channel skew; verify scan timing against the experiment.','channel-skew'));
  return {kind:'acquisition',metrics:{'Samples per channel':round(samplesPerChannel,0),'Total samples':round(totalSamples,0),'Nyquist frequency':`${round(nyquist,2)} Hz`,'Sustained throughput':`${round(throughput/1024,2)} KiB/s`,'Estimated file size':`${round(totalBytes/1024/1024,3)} MiB`,'Buffer requirement':`${round(bufferBytes/1024,2)} KiB`},findings,data:{acquisitionName:text(root,'acquisition_name'),channels,sampleRateHz:rate,durationS:duration,bitDepth:bits,bytesPerSample,overheadPercent:overhead*100,expectedMaxFrequencyHz:maxFrequency,nyquistHz:nyquist,estimatedBytes:totalBytes,throughputBytesPerSecond:throughput,bufferBytes,samplingMode:text(root,'sampling_mode'),timestampSource:text(root,'timestamp_source')}};
}

function signal(root) {
  const rate = number(root,'sample_rate'), windowSize = Math.max(1,Math.floor(number(root,'filter_window',1))), mode = text(root,'detrend');
  const parsed = parseTimeValue(text(root,'signal_csv'),rate), values = parsed.values, time = parsed.time, findings = [];
  if (values.length < 4) findings.push(finding('fail','At least four valid samples are required.','insufficient-samples'));
  if (!(rate > 0)) findings.push(finding('fail','Sample rate must be positive.','invalid-sample-rate'));
  if (parsed.invalid) findings.push(finding('warn',`${parsed.invalid} rows could not be parsed and were excluded.`,'invalid-rows'));
  const m = mean(values), sd = stddev(values), signalRms = rms(values), min = values.length ? Math.min(...values) : NaN, max = values.length ? Math.max(...values) : NaN;
  const fit = linearFit(time,values), centered = detrend(time,values,mode), filtered = movingAverage(centered,windowSize), diff = values.slice(1).map((value,index)=>value-values[index]);
  const noiseEstimate = diff.length ? stddev(diff)/Math.sqrt(2) : NaN, snr = noiseEstimate > 0 ? 20*Math.log10(rms(centered)/noiseEstimate) : NaN;
  const crest = signalRms > 0 ? Math.max(...values.map(Math.abs))/signalRms : NaN;
  if (windowSize > values.length) findings.push(finding('warn','Moving-average window exceeds the available sample count.','filter-window'));
  if (Math.abs(fit.slope) > 0 && Math.abs(fit.slope) * (time.at(-1)-time[0]) > 0.1 * Math.max(1e-12,Math.max(...values)-Math.min(...values))) findings.push(finding('warn','Linear drift exceeds 10% of the observed peak-to-peak span.','drift'));
  return {kind:'signal',metrics:{'Valid samples':values.length,'Mean':`${round(m,6)} ${text(root,'units')}`,'RMS':`${round(signalRms,6)} ${text(root,'units')}`,'Standard deviation':round(sd,6),'Peak-to-peak':round(max-min,6),'Crest factor':round(crest,4),'Drift slope':`${round(fit.slope,8)} ${text(root,'units')}/s`,'Estimated SNR':`${round(snr,2)} dB`},findings,data:{sampleRateHz:rate,units:text(root,'units'),detrend:mode,filterWindowSamples:windowSize,time,values,filtered,statistics:{mean:m,rms:signalRms,standardDeviation:sd,min,max,peakToPeak:max-min,crestFactor:crest,driftSlope:fit.slope,estimatedNoise:noiseEstimate,estimatedSnrDb:snr}},extra:chartLine(filtered)};
}

function windowCoefficient(type,index,count) {
  if (count <= 1 || type === 'rectangular') return 1;
  if (type === 'hamming') return 0.54 - 0.46 * Math.cos(2*Math.PI*index/(count-1));
  return 0.5 * (1 - Math.cos(2*Math.PI*index/(count-1)));
}
function spectrum(values,rate,windowType) {
  const n = values.length, m = mean(values), weighted = values.map((value,index)=>(value-m)*windowCoefficient(windowType,index,n));
  const gain = weighted.length ? mean(weighted.map((_,index)=>windowCoefficient(windowType,index,n))) : 1;
  const out = [];
  for (let k=0;k<=Math.floor(n/2);k+=1) {
    let re=0,im=0;
    for (let i=0;i<n;i+=1) { const angle=2*Math.PI*k*i/n; re += weighted[i]*Math.cos(angle); im -= weighted[i]*Math.sin(angle); }
    const amplitude = 2*Math.hypot(re,im)/(n*Math.max(gain,1e-12));
    out.push({bin:k,frequencyHz:k*rate/n,amplitude:k===0?amplitude/2:amplitude});
  }
  return out;
}
function frequency(root) {
  const rate = number(root,'sample_rate'), maxExpected = number(root,'expected_max_frequency'), limit = Math.max(8,Math.min(2048,Math.floor(number(root,'max_samples',1024))));
  const parsed = parseNumericSeries(text(root,'frequency_samples')), values = parsed.values.slice(0,limit), windowType = text(root,'window'), findings=[];
  if (values.length < 8) findings.push(finding('fail','At least eight valid samples are required for spectrum analysis.','insufficient-samples'));
  if (!(rate > 0)) findings.push(finding('fail','Sample rate must be positive.','invalid-sample-rate'));
  if (maxExpected >= rate/2) findings.push(finding('fail','Expected maximum frequency reaches or exceeds Nyquist.','alias-risk'));
  if (parsed.values.length > limit) findings.push(finding('warn',`Only the first ${limit} samples were analyzed to keep browser computation bounded.`,'sample-cap'));
  if (parsed.invalid) findings.push(finding('warn',`${parsed.invalid} rows could not be parsed and were excluded.`,'invalid-rows'));
  const bins = values.length >= 2 ? spectrum(values,rate,windowType) : [], nonDC = bins.slice(1), sorted = [...nonDC].sort((a,b)=>b.amplitude-a.amplitude), peak = sorted[0] || {frequencyHz:NaN,amplitude:NaN};
  const top = sorted.slice(0,5);
  const table = top.length ? `<div class="scwb-v240__table-wrap"><table><thead><tr><th>Rank</th><th>Frequency</th><th>Amplitude</th></tr></thead><tbody>${top.map((item,index)=>`<tr><td>${index+1}</td><td>${esc(round(item.frequencyHz,4))} Hz</td><td>${esc(round(item.amplitude,6))}</td></tr>`).join('')}</tbody></table></div>` : '';
  return {kind:'frequency',metrics:{'Analyzed samples':values.length,'Nyquist frequency':`${round(rate/2,3)} Hz`,'Frequency resolution':`${round(rate/Math.max(1,values.length),5)} Hz`,'Dominant frequency':`${round(peak.frequencyHz,4)} Hz`,'Dominant amplitude':round(peak.amplitude,6),'Window':windowType},findings,data:{sampleRateHz:rate,window:windowType,values,spectrum:bins,topPeaks:top,expectedMaximumFrequencyHz:maxExpected},extra:chartBars(bins)+table};
}

function calibration(root) {
  const table = parseTable(text(root,'calibration_csv')), rows = table.rows, direction = text(root,'regression_direction'), findings=[];
  let reference = [], observed = [];
  rows.forEach(row => { const vals=Object.values(row).filter(Number.isFinite); if(vals.length>=2){reference.push(vals[0]);observed.push(vals[1]);} });
  if (reference.length < 3) findings.push(finding('fail','At least three valid calibration points are required.','insufficient-calibration-points'));
  const x = direction === 'observed_to_reference' ? observed : reference;
  const y = direction === 'observed_to_reference' ? reference : observed;
  const fit = linearFit(x,y), accepted = number(root,'acceptance_rmse',Infinity);
  if (Number.isFinite(fit.rmse) && fit.rmse > accepted) findings.push(finding('fail',`Calibration RMSE ${round(fit.rmse,6)} exceeds the acceptance limit ${accepted}.`,'rmse-exceeded'));
  if (Number.isFinite(fit.r2) && fit.r2 < .99) findings.push(finding('warn','Calibration R² is below 0.99; inspect nonlinearity and residual structure.','low-r2'));
  const uncertaintyLines = parseLines(text(root,'uncertainty_csv'));
  const components=[];
  uncertaintyLines.forEach((line,index)=>{
    const parts=line.split(',').map(item=>item.trim());
    if(index===0 && /name|component/i.test(parts[0])) return;
    const raw=Number(parts[1]), distribution=(parts[2]||'standard').toLowerCase();
    if(!Number.isFinite(raw)) return;
    const divisor=distribution==='uniform'?Math.sqrt(3):distribution==='triangular'?Math.sqrt(6):1;
    components.push({name:parts[0]||`component-${index+1}`,reportedValue:raw,distribution,standardUncertainty:Math.abs(raw)/divisor});
  });
  const combined=Math.sqrt(components.reduce((sum,item)=>sum+item.standardUncertainty**2,0)), k=Math.max(0,number(root,'coverage_factor',2)), expanded=k*combined;
  if (!components.length) findings.push(finding('warn','No valid uncertainty components were supplied.','missing-uncertainty-budget'));
  const residualTable = fit.residuals.length ? `<div class="scwb-v240__table-wrap"><table><thead><tr><th>Point</th><th>Reference</th><th>Observed</th><th>Residual</th></tr></thead><tbody>${fit.residuals.map((residual,index)=>`<tr><td>${index+1}</td><td>${esc(reference[index])}</td><td>${esc(observed[index])}</td><td>${esc(round(residual,7))}</td></tr>`).join('')}</tbody></table></div>` : '';
  return {kind:'calibration',metrics:{'Calibration points':reference.length,'Slope':round(fit.slope,9),'Intercept':round(fit.intercept,9),'R²':round(fit.r2,7),'RMSE':`${round(fit.rmse,7)} ${text(root,'units')}`,'Combined uncertainty':`${round(combined,7)} ${text(root,'units')}`,'Expanded uncertainty':`±${round(expanded,7)} ${text(root,'units')} (k=${k})`},findings,data:{units:text(root,'units'),direction,reference,observed,fit,uncertaintyComponents:components,combinedStandardUncertainty:combined,coverageFactor:k,expandedUncertainty:expanded},extra:residualTable};
}

function validation(root) {
  const table=parseTable(text(root,'measurement_csv')), findings=[], expectedRate=number(root,'expected_rate'), rateTolerance=Math.abs(number(root,'rate_tolerance_percent'))/100, maxJitter=Math.abs(number(root,'max_jitter_percent')), minSamples=Math.max(2,Math.floor(number(root,'min_samples',2)));
  if(table.headers.length<2) findings.push(finding('fail','Measurement data must include a time column and at least one value channel.','missing-columns'));
  const timeKey=table.headers[0], times=table.rows.map(row=>row[timeKey]).filter(Number.isFinite), channels=table.headers.slice(1);
  if(times.length<minSamples) findings.push(finding('fail',`Only ${times.length} valid timestamps were supplied; ${minSamples} are required.`,'insufficient-samples'));
  const intervals=[];
  for(let i=1;i<times.length;i+=1){const dt=times[i]-times[i-1];if(dt<=0)findings.push(finding('fail',`Timestamp ${i+1} is not strictly increasing.`,'non-monotonic-time'));else intervals.push(dt);}
  const meanDt=mean(intervals), actualRate=meanDt>0?1/meanDt:NaN, intervalSd=stddev(intervals), jitterPercent=meanDt>0?intervalSd/meanDt*100:NaN;
  if(Number.isFinite(actualRate)&&expectedRate>0&&Math.abs(actualRate-expectedRate)>expectedRate*rateTolerance) findings.push(finding('fail',`Observed sample rate ${round(actualRate,5)} Hz is outside the stated tolerance.`,'sample-rate-error'));
  if(Number.isFinite(jitterPercent)&&jitterPercent>maxJitter) findings.push(finding('fail',`Timing jitter ${round(jitterPercent,3)}% exceeds ${maxJitter}%.`,'timing-jitter'));
  if(table.invalid) findings.push(finding('warn',`${table.invalid} missing or nonnumeric cells were found.`,'invalid-cells'));
  const channelStats=channels.map(name=>{const values=table.rows.map(row=>row[name]).filter(Number.isFinite);return {name,count:values.length,min:values.length?Math.min(...values):NaN,max:values.length?Math.max(...values):NaN,mean:mean(values),standardDeviation:stddev(values)};});
  channelStats.filter(item=>item.count<times.length).forEach(item=>findings.push(finding('warn',`Channel ${item.name} has ${times.length-item.count} missing values.`,'channel-missing-data')));
  if(!text(root,'campaign_notes')) findings.push(finding('warn','Campaign notes are empty; record instrument IDs, conditions, clock source, operator, and anomalies.','missing-provenance'));
  const statsTable=`<div class="scwb-v240__table-wrap"><table><thead><tr><th>Channel</th><th>Count</th><th>Mean</th><th>Std dev</th><th>Min</th><th>Max</th></tr></thead><tbody>${channelStats.map(item=>`<tr><td>${esc(item.name)}</td><td>${item.count}</td><td>${esc(round(item.mean,6))}</td><td>${esc(round(item.standardDeviation,6))}</td><td>${esc(round(item.min,6))}</td><td>${esc(round(item.max,6))}</td></tr>`).join('')}</tbody></table></div>`;
  return {kind:'validation',metrics:{'Rows':table.rows.length,'Channels':channels.length,'Observed sample rate':`${round(actualRate,6)} Hz`,'Mean interval':`${round(meanDt,8)} s`,'Timing jitter':`${round(jitterPercent,4)}%`,'Invalid cells':table.invalid},findings,data:{headers:table.headers,rows:table.rows,expectedSampleRateHz:expectedRate,observedSampleRateHz:actualRate,meanIntervalS:meanDt,intervalStandardDeviationS:intervalSd,jitterPercent,channelStatistics:channelStats,campaignNotes:text(root,'campaign_notes')},extra:statsTable};
}

function analyze(root) {
  let result;
  switch (root.dataset.scwbV240Panel) {
    case 'instrumentation': result=instrumentation(root); break;
    case 'acquisition': result=acquisition(root); break;
    case 'signal': result=signal(root); break;
    case 'frequency': result=frequency(root); break;
    case 'calibration': result=calibration(root); break;
    case 'validation': result=validation(root); break;
    default: return;
  }
  root._scwbV240Result={schema:`sc-workbench-${result.kind}/1.0`,version:CFG.version,generatedAt:new Date().toISOString(),project:root.dataset.scwbV240Project,kind:result.kind,metrics:result.metrics,findings:result.findings,data:result.data};
  render(root,result.kind.replace(/(^|-)(\w)/g,(_,a,b)=>` ${b.toUpperCase()}`).trim(),result.metrics,result.findings,result.extra||'');
}
function init(root) {
  load(root);
  root.addEventListener('click',event=>{
    const button=event.target.closest('[data-scwb-v240-action]');
    if(!button)return;
    const action=button.dataset.scwbV240Action;
    if(action==='analyze')analyze(root);
    if(action==='save'){save(root);analyze(root);}
    if(action==='export'){if(!root._scwbV240Result)analyze(root);download(`workbench-${root.dataset.scwbV240Panel}-${root.dataset.scwbV240Project}.json`,root._scwbV240Result);}
  });
}
document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-scwb-v240-panel]').forEach(init));
})();
