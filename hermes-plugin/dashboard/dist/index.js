const root=document.createElement('div');
root.style.padding='24px';
root.style.fontFamily='ui-monospace,monospace';
root.innerHTML='<h2>Company OS Network</h2><p>This plugin exposes the local read-only Company OS projection API for the Desktop cockpit.</p><p><code>/api/plugins/company-os/snapshot</code></p>';
document.currentScript?.parentElement?.appendChild(root);
