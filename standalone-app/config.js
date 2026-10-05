export const WORKBENCH_CONFIG=Object.freeze({
  apiBaseUrl:globalThis.SC_WORKBENCH_API_BASE_URL||"https://workbench-api.sustainablecatalyst.com",
  appName:"Sustainable Catalyst Workbench",
  version:"13.1.0",
  frontendVersionAsset:"/version.json",
  auth:{anonymousBootstrap:true,persistToken:false},
  state:{persistProjectSelection:true,persistNotebookSelection:true}
});
