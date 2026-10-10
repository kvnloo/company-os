// Build a diagnostic shell from the installed host's real registry + fetchJSON.
// Writes only to the requested artifact directory; no Hermes source/config edits.
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
const [hostArg, outArg] = process.argv.slice(2)
if (!hostArg || !outArg) throw new Error('usage: node scripts/build-diagnostic.mjs HERMES_ROOT ARTIFACTS')
const host = fs.realpathSync(hostArg), out = path.resolve(outArg)
const require = createRequire(path.join(host, 'package.json'))
const {build} = require('esbuild')
const source = `
import React from 'react';
import {createRoot} from 'react-dom/client';
import {exposePluginSDK,getPluginComponent,onPluginRegistered} from ${JSON.stringify(path.join(host,'web/src/plugins/registry.ts'))};
import {usePlugins} from ${JSON.stringify(path.join(host,'web/src/plugins/usePlugins.ts'))};
import {PluginPage} from ${JSON.stringify(path.join(host,'web/src/plugins/PluginPage.tsx'))};
exposePluginSDK();
window.__COMPANY_OS_DIAGNOSTIC__={registered:false,scope:'isolated diagnostic; actual Hermes loader, registry, PluginPage and fetchJSON'};
onPluginRegistered(()=>{window.__COMPANY_OS_DIAGNOSTIC__.registered=Boolean(getPluginComponent('company-os'));});
function Host(){
  const {manifests}=usePlugins();
  const found=manifests.find(m=>m.name==='company-os'&&m.tab.path===location.pathname);
  return found?React.createElement(PluginPage,{name:found.name}):React.createElement('div',null,'Loading owned manifest');
}
createRoot(document.getElementById('root')).render(React.createElement(Host));
`
await build({stdin:{contents:source,resolveDir:host,loader:'tsx'},outfile:path.join(out,'diagnostic-host.js'),bundle:true,format:'iife',platform:'browser',jsx:'automatic',
  alias:{'@':path.join(host,'web/src'),'@hermes/shared':path.join(host,'apps/shared/src'),'react':path.join(host,'node_modules/react'),'react-dom':path.join(host,'node_modules/react-dom')},
  define:{'process.env.NODE_ENV':'"production"','import.meta.env.DEV':'false'},logLevel:'warning',metafile:true,
}).then(result=>fs.writeFileSync(path.join(out,'diagnostic-build.json'),JSON.stringify(result.metafile,null,2)))
console.log('Built isolated diagnostic from installed Hermes sources')
