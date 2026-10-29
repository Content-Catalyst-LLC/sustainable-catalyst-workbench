/** UVR-01.3.7 display policy. Never round, replace, or mutate sampled data.
 * The Python SVG exporter implements this same policy; shared fixtures certify parity.
 */
export function displayYRange(min, max) {
  const spread = max - min;
  const magnitude = Math.max(Math.abs(min), Math.abs(max));
  const nearConstant = spread <= 32 * Number.EPSILON * magnitude;
  const center = min + spread / 2;
  const span = Math.max(1e-12, Math.abs(center) * 0.2);
  return nearConstant ? [center - span / 2, center + span / 2] : [min, max];
}
