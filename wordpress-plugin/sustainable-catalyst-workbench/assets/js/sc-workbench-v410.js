(function () {
  'use strict';
  var VERSION = '4.1.0';
  var ROOT = '[data-scwb-v410]';
  var STORE = 'scwb:v410:team-workspaces';
  var roleCapabilities = {
    owner: ['organization:manage','team:manage','member:manage','project:create','project:read','project:write','project:delete','review:write','export:create','activity:read'],
    admin: ['team:manage','member:manage','project:create','project:read','project:write','project:delete','review:write','export:create','activity:read'],
    editor: ['project:create','project:read','project:write','review:write','export:create','activity:read'],
    reviewer: ['project:read','review:write','export:create','activity:read'],
    viewer: ['project:read','activity:read']
  };

  function readStore() { try { return JSON.parse(localStorage.getItem(STORE) || '[]'); } catch (error) { return []; } }
  function writeStore(records) { localStorage.setItem(STORE, JSON.stringify(records)); }
  function fields(root) {
    var values = {};
    root.querySelectorAll('[data-scwb-v410-field]').forEach(function (field) { values[field.getAttribute('data-scwb-v410-field')] = field.value; });
    return values;
  }
  function parse(value, fallback) { try { return JSON.parse(value); } catch (error) { return fallback; } }
  function slug(value, fallback) { var result = String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); return result || fallback; }
  function show(root, value, summary) {
    var output = root.querySelector('[data-scwb-v410-output]');
    var label = root.querySelector('[data-scwb-v410-summary]');
    if (output) output.textContent = JSON.stringify(value, null, 2);
    if (label) label.textContent = summary || 'Record created.';
  }
  function can(role, capability) { return (roleCapabilities[role] || []).indexOf(capability) >= 0; }
  function workspacePlan(values, root) {
    var members = parse(values.members, []);
    return {
      schema: 'sc-workbench-hosted-collaborative-workspace-plan/1.0', version: VERSION,
      organization: { id: slug(values.organizationName, 'organization'), name: values.organizationName || 'Organization', private: true },
      team: { id: slug(values.teamName, 'team'), name: values.teamName || 'Team', members: members },
      project: { id: slug(values.projectTitle, 'project'), title: values.projectTitle || 'Team Workbench Project', visibility: 'team' },
      authenticated: root.getAttribute('data-scwb-authenticated') === 'true', browserFallback: true, paidExternalDatabaseRequired: false,
      automaticMembershipEscalationAuthorized: false, automaticProjectDeletionAuthorized: false
    };
  }
  function build(root) {
    var panel = root.getAttribute('data-scwb-v410-panel');
    var value = fields(root), result;
    if (panel === 'workspace') result = workspacePlan(value, root);
    else if (panel === 'organization') result = { schema:'sc-workbench-organization-browser-plan/1.0', version:VERSION, organizationId:slug(value.organizationName,'organization'), name:value.organizationName, owners:String(value.owners||'').split(/\n+/).filter(Boolean), retentionDays:Number(value.retentionDays||365), allowExternalInvitations:value.allowExternalInvitations==='true', private:true };
    else if (panel === 'team') result = { schema:'sc-workbench-team-browser-plan/1.0', version:VERSION, organizationId:value.organizationId, teamId:slug(value.teamName,'team'), name:value.teamName, members:parse(value.members,[]), private:true };
    else if (panel === 'roles') { var memberships=parse(value.memberships,[]), roles=memberships.filter(function(item){return item.userId===value.userId&&item.status!=='revoked';}).map(function(item){return item.role;}); result={schema:'sc-workbench-access-browser-report/1.0',version:VERSION,userId:value.userId,action:value.requestedAction,roles:roles,allowed:roles.some(function(role){return can(role,value.requestedAction);}),automaticRoleEscalationAuthorized:false}; }
    else if (panel === 'invitations') result = { schema:'sc-workbench-invitation-browser-plan/1.0',version:VERSION,teamId:value.teamId,emailHashRequired:true,role:value.role||'viewer',expiresAt:value.expiresAt,status:'draft',rawTokenPersisted:false,automaticAcceptanceAuthorized:false };
    else if (panel === 'projects') result = { schema:'sc-workbench-team-project-browser-plan/1.0',version:VERSION,organizationId:value.organizationId,teamId:value.teamId,projectId:value.projectId,title:value.projectTitle,roleBindings:parse(value.roleBindings,[]),visibility:'team',private:true,automaticPublicationAuthorized:false };
    else if (panel === 'revisions') { var base=parse(value.base,{}),local=parse(value.local,{}),remote=parse(value.remote,{}),conflicts=[]; Object.keys(Object.assign({},base,local,remote)).forEach(function(key){if(local[key]!==base[key]&&remote[key]!==base[key]&&local[key]!==remote[key])conflicts.push(key);}); result={schema:'sc-workbench-collaborative-revision-browser-plan/1.0',version:VERSION,strategy:value.strategy||'manual',conflicts:conflicts,conflictCount:conflicts.length,automaticConflictResolutionAuthorized:false,automaticOverwriteAuthorized:false}; }
    else if (panel === 'activity') result = { schema:'sc-workbench-team-activity-browser-record/1.0',version:VERSION,actorUserId:value.actorUserId,action:value.activityAction,targetId:value.targetId,metadata:parse(value.metadata,{}),occurredAt:new Date().toISOString(),immutable:true };
    else result = { schema:'sc-workbench-team-workspace-export-plan/1.0',version:VERSION,organization:parse(value.organization,{}),team:parse(value.team,{}),projects:parse(value.projects,[]),secretsIncluded:false,requiresExplicitImport:true,automaticCloudUpload:false };
    show(root,result,'Collaboration record prepared.'); return result;
  }
  function save(root) { var record=build(root),records=readStore(); records.push({id:'team-record-'+Date.now(),savedAt:new Date().toISOString(),record:record}); writeStore(records); show(root,record,'Saved to this browser.'); }
  function download(root) { var record=build(root),blob=new Blob([JSON.stringify(record,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='workbench-team-workspace-record.json';document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url); }
  function init(root) { if(!root||root.getAttribute('data-scwb-v410-ready')==='true')return;root.setAttribute('data-scwb-v410-ready','true');root.dispatchEvent(new CustomEvent('scwb:team-workspace-ready',{bubbles:true,detail:{version:VERSION,authenticated:root.getAttribute('data-scwb-authenticated')==='true'}})); }
  document.addEventListener('click',function(event){var button=event.target.closest('[data-scwb-v410-action]');if(!button)return;var root=button.closest(ROOT);if(!root)return;var action=button.getAttribute('data-scwb-v410-action');if(action==='build')build(root);if(action==='save-local')save(root);if(action==='export')download(root);});
  function start(){document.querySelectorAll(ROOT).forEach(init);} if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
  document.addEventListener('scwb:project-changed',function(event){var detail=event.detail||{};document.querySelectorAll(ROOT).forEach(function(root){if(detail.projectId)root.setAttribute('data-scwb-project',detail.projectId);});});
  window.SCWBTeamWorkspace={version:VERSION,roleCapabilities:roleCapabilities,can:can,build:build,readStore:readStore,expectedStudioCount:23,privateByDefault:true,browserFallback:true,paidExternalDatabaseRequired:false,automaticInvitationAcceptanceAuthorized:false,automaticMembershipEscalationAuthorized:false,automaticProjectDeletionAuthorized:false};
}());
