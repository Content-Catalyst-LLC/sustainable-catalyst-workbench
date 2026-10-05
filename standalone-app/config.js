export const WORKBENCH_CONFIG=Object.freeze({
  apiBaseUrl:globalThis.SC_WORKBENCH_API_BASE_URL||"https://workbench-api.sustainablecatalyst.com",
  appName:"Sustainable Catalyst Workbench",
  version:"13.4.0",
  frontendVersionAsset:"/version.json",
  auth:{anonymousBootstrap:true,persistToken:false},
  state:{persistProjectSelection:true,persistNotebookSelection:true,persistResearchSessionSelection:true,recentExpressionLimit:8},
  calculator:{notationNormalization:"conservative",showNormalizationPreview:true},
  workspace:{restoreLastResearchSession:true,activityLimit:100}
});
