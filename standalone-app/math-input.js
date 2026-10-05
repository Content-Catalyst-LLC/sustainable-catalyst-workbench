export const MATH_INPUT_PALETTE=Object.freeze([
  {group:"Operators",items:[
    {label:"×",insert:"×"},{label:"÷",insert:"÷"},{label:"−",insert:"−"},
    {label:"x²",insert:"²"},{label:"x³",insert:"³"},{label:"^",insert:"^"},
    {label:"√",insert:"√("},{label:"(",insert:"("},{label:")",insert:")"}
  ]},
  {group:"Functions",items:[
    {label:"sin",insert:"sin("},{label:"cos",insert:"cos("},{label:"tan",insert:"tan("},
    {label:"asin",insert:"asin("},{label:"acos",insert:"acos("},{label:"atan",insert:"atan("},
    {label:"ln",insert:"ln("},{label:"log",insert:"log("},{label:"exp",insert:"exp("},
    {label:"abs",insert:"Abs("}
  ]},
  {group:"Constants",items:[
    {label:"π",insert:"π"},{label:"e",insert:"E"},{label:"i",insert:"I"},{label:"∞",insert:"∞"}
  ]},
  {group:"Greek",items:[
    {label:"α",insert:"alpha"},{label:"β",insert:"beta"},{label:"γ",insert:"gamma"},
    {label:"δ",insert:"delta"},{label:"θ",insert:"theta"},{label:"λ",insert:"lambda"},
    {label:"μ",insert:"mu"},{label:"σ",insert:"sigma"},{label:"φ",insert:"phi"},{label:"ω",insert:"omega"}
  ]}
]);

export function insertAtCursor(element,text){
  const start=element.selectionStart??element.value.length;
  const end=element.selectionEnd??element.value.length;
  element.value=element.value.slice(0,start)+text+element.value.slice(end);
  const next=start+text.length;
  element.focus();
  element.setSelectionRange(next,next);
  element.dispatchEvent(new Event("input",{bubbles:true}));
}

export function paletteHtml(){
  return MATH_INPUT_PALETTE.map(group=>`
    <div class="sc-palette-group">
      <span class="sc-palette-label">${group.group}</span>
      <div class="sc-palette-buttons">
        ${group.items.map(item=>`<button type="button" class="sc-math-key" data-math-insert="${item.insert.replaceAll('"','&quot;')}">${item.label}</button>`).join("")}
      </div>
    </div>`).join("");
}
