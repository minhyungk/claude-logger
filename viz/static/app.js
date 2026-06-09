let currentSession = null;
let pollInterval = null;
let lastCallCount = 0;

async function init() {
    await loadSummary();
    await loadSessions();
    startPolling();
}

function startPolling() {
    pollInterval = setInterval(async () => {
        await loadSummary();
        await loadSessions();
        if (currentSession) {
            try {
                const resp = await fetch(`/api/sessions/${currentSession}`);
                const session = await resp.json();
                const newCount = (session.calls || []).length;
                if (newCount !== lastCallCount) {
                    lastCallCount = newCount;
                    renderFromSession(session);
                }
            } catch (e) {}
        }
    }, 3000);
}

async function loadSummary() {
    try {
        const resp = await fetch('/api/summary');
        const data = await resp.json();
        document.getElementById('stat-calls').textContent = `${data.total_calls} calls`;
        document.getElementById('stat-cost').textContent = `$${data.total_cost.toFixed(4)}`;
        document.getElementById('stat-tokens').textContent = `${formatTokens(data.total_input_tokens + data.total_output_tokens)} tokens`;
        document.getElementById('stat-latency').textContent = `${data.avg_latency_ms.toFixed(0)} ms avg`;
    } catch (e) {}
}

async function loadSessions() {
    const container = document.getElementById('sessions-container');
    try {
        const resp = await fetch('/api/sessions');
        const sessions = await resp.json();
        container.innerHTML = '';
        for (const s of sessions) {
            const card = document.createElement('div');
            card.className = 'session-card' + (currentSession === s.session_id ? ' active' : '');
            card.dataset.id = s.session_id;
            card.innerHTML = `
                <div class="name">${s.session_id}</div>
                <div class="stats">${s.num_calls} calls &middot; $${s.total_cost.toFixed(4)} &middot; ${formatTokens(s.total_input_tokens + s.total_output_tokens)}</div>
            `;
            card.onclick = () => selectSession(s.session_id);
            container.appendChild(card);
        }
    } catch (e) {
        container.innerHTML = '<p style="color:#94a3b8;font-size:13px;">No sessions yet</p>';
    }
}

async function selectSession(sessionId) {
    currentSession = sessionId;
    lastCallCount = 0;
    document.querySelectorAll('.session-card').forEach(c => c.classList.remove('active'));
    const active = document.querySelector(`.session-card[data-id="${sessionId}"]`);
    if (active) active.classList.add('active');
    await refreshSession(sessionId);
}

async function refreshSession(sessionId) {
    const resp = await fetch(`/api/sessions/${sessionId}`);
    const session = await resp.json();
    lastCallCount = (session.calls || []).length;
    renderFromSession(session);
}

function renderFromSession(session) {
    document.getElementById('detail-placeholder').classList.add('hidden');
    document.getElementById('detail-content').classList.remove('hidden');
    document.getElementById('detail-title').textContent = session.session_id;

    const calls = session.calls || [];
    const totalTokens = calls.reduce((s, c) => s + (c.tokens?.input_tokens || 0) + (c.tokens?.output_tokens || 0), 0);
    const totalCost = calls.reduce((s, c) => s + (c.cost?.total_cost || 0), 0);
    const avgLatency = calls.length ? calls.reduce((s, c) => s + (c.performance?.latency_ms || 0), 0) / calls.length : 0;

    document.getElementById('session-tokens').textContent = formatTokens(totalTokens);
    document.getElementById('session-cost').textContent = `$${totalCost.toFixed(4)}`;
    document.getElementById('session-latency').textContent = `${avgLatency.toFixed(0)}ms`;
    document.getElementById('session-calls').textContent = calls.length;

    renderCallTimeline(calls, session.session_id);
    renderTokenChart(calls);
    renderLatencyChart(calls);
    loadWorkspace(session.session_id);
}

function renderCallTimeline(calls, sessionId) {
    const container = document.getElementById('calls-container');
    container.innerHTML = '';

    for (const call of calls) {
        const idx = call.meta?.call_index || '?';
        const tokens = call.tokens || {};
        const totalTok = (tokens.input_tokens || 0) + (tokens.output_tokens || 0);
        const cost = call.cost?.total_cost || 0;
        const latency = call.performance?.latency_ms || 0;
        const stop = call.performance?.stop_reason || '';
        const tools = call.tools || [];
        const assistantPreview = extractAssistantPreview(call);
        const userInput = extractUserInput(call);
        const assistantFull = extractAssistantFull(call);
        const bashCmds = extractBashCommands(tools);
        const webSearches = extractWebSearches(tools);
        const files = extractFiles(tools);
        const createdFiles = extractCreatedFiles(tools);

        const row = document.createElement('div');
        row.className = 'call-row';
        row.innerHTML = `
            <div class="call-header">
                <span class="call-index">${idx}</span>
                <div class="call-meta">
                    <span class="prompt-preview">${escapeHtml(assistantPreview)}</span>
                    <div class="call-badges">
                        <span class="badge tokens">${formatTokens(totalTok)}</span>
                        <span class="badge cost">$${cost.toFixed(4)}</span>
                        <span class="badge latency">${latency.toFixed(0)}ms</span>
                        <span class="badge stop">${stop}</span>
                    </div>
                </div>
                <span class="call-expand-icon">&#9654;</span>
            </div>
            <div class="call-detail-body">
                <div class="detail-section">
                    <div class="detail-label">User Input</div>
                    <div class="detail-text user-input">${escapeHtml(userInput)}</div>
                </div>
                <div class="detail-section">
                    <div class="detail-label">Assistant Response</div>
                    <div class="detail-text assistant-response">${escapeHtml(assistantFull)}</div>
                </div>
                ${createdFiles.length ? `
                <div class="detail-section">
                    <div class="detail-label">Files Created / Modified</div>
                    <div class="file-list">${createdFiles.map(f => `<span class="file-item file-created">${escapeHtml(f)}</span>`).join('')}</div>
                </div>` : ''}
                ${bashCmds.length ? `
                <div class="detail-section">
                    <div class="detail-label">Bash Commands</div>
                    ${bashCmds.map(cmd => renderBashCmd(cmd)).join('')}
                </div>` : ''}
                ${webSearches.length ? `
                <div class="detail-section">
                    <div class="detail-label">Web Searches</div>
                    ${webSearches.map(q => `<div class="web-search">${escapeHtml(q)}</div>`).join('')}
                </div>` : ''}
                ${files.length ? `
                <div class="detail-section">
                    <div class="detail-label">Files Read</div>
                    <div class="file-list">${files.map(f => `<span class="file-item">${escapeHtml(f)}</span>`).join('')}</div>
                </div>` : ''}
                ${tools.length ? `
                <div class="detail-section">
                    <div class="detail-label">All Tool Calls (${tools.length})</div>
                    ${renderTools(tools)}
                </div>` : ''}
                <button class="call-detail-btn" onclick="event.stopPropagation(); showCallDetail('${sessionId}', ${idx})">View Full JSON</button>
            </div>
        `;
        row.querySelector('.call-header').addEventListener('click', function(e) {
            e.stopPropagation();
            row.classList.toggle('expanded');
        });
        container.appendChild(row);
    }
}

function renderTools(tools) {
    return tools.map(t => {
        const input = t.input ? summarizeToolInput(t.name, t.input) : '';
        return `<div class="tool-item"><span class="tool-name">${t.name}</span><span class="tool-input">${escapeHtml(input)}</span></div>`;
    }).join('');
}

function summarizeToolInput(name, input) {
    if (name === 'Read' || name === 'Write' || name === 'Edit') {
        return input.file_path || input.path || JSON.stringify(input).slice(0, 80);
    }
    if (name === 'Bash') {
        return input.command || JSON.stringify(input).slice(0, 80);
    }
    const str = JSON.stringify(input);
    return str.length > 100 ? str.slice(0, 100) + '...' : str;
}

function extractAssistantPreview(call) {
    const text = call.conversation?.assistant_response || '';
    if (!text) return '(no response)';
    let clean = text.replace(/\s+/g, ' ').trim();
    // Strip leading JSON/markdown artifacts
    clean = clean.replace(/^```(?:json)?\s*/, '').replace(/```\s*$/, '');
    try {
        const parsed = JSON.parse(clean);
        if (parsed.title) return parsed.title;
    } catch (e) {}
    return clean.slice(0, 120);
}

function extractAssistantFull(call) {
    const text = call.conversation?.assistant_response || '';
    if (!text) return '(no response)';
    return text.slice(0, 2000) + (text.length > 2000 ? '\n...(truncated)' : '');
}

function extractUserInput(call) {
    const messages = call.conversation?.messages || [];
    const userMsgs = messages.filter(m => m.role === 'user');
    if (!userMsgs.length) return '(no user input)';
    const last = userMsgs[userMsgs.length - 1];
    let content = last?.content || '';
    if (Array.isArray(content)) {
        content = content.map(b => b.text || '').filter(Boolean).join(' ');
    }
    return content.slice(0, 1000) + (content.length > 1000 ? '\n...(truncated)' : '');
}

function extractBashCommands(tools) {
    return tools
        .filter(t => t.name === 'Bash' && t.input?.command)
        .map(t => t.input.command);
}

function renderBashCmd(cmd) {
    const lines = cmd.split('\n');
    if (lines.length <= 5) {
        return `<div class="bash-cmd"><code>${escapeHtml(cmd)}</code></div>`;
    }
    const preview = lines.slice(0, 5).join('\n');
    const id = 'bash-' + Math.random().toString(36).slice(2, 8);
    return `<div class="bash-cmd bash-collapsible">
        <code id="${id}-preview">${escapeHtml(preview)}</code>
        <code id="${id}-full" class="hidden">${escapeHtml(cmd)}</code>
        <button class="bash-toggle" onclick="event.stopPropagation(); toggleBash('${id}')">${lines.length - 5} more lines</button>
    </div>`;
}

function extractWebSearches(tools) {
    const searches = [];
    for (const t of tools) {
        if (t.name === 'WebSearch' && t.input?.query) {
            searches.push(t.input.query);
        } else if (t.name === 'WebFetch' && t.input?.url) {
            searches.push(t.input.url);
        }
    }
    return searches;
}

function extractFiles(tools) {
    const files = new Set();
    for (const t of tools) {
        if (t.name !== 'Read' || !t.input) continue;
        const path = t.input.file_path || t.input.path;
        if (path) {
            const short = path.split('/').slice(-2).join('/');
            files.add(short);
        }
    }
    return [...files];
}


async function showCallDetail(sessionId, index) {
    const resp = await fetch(`/api/sessions/${sessionId}/calls/${index}`);
    const data = await resp.json();
    document.getElementById('modal-title').textContent = `Call #${index}`;
    document.getElementById('modal-body').innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
    document.getElementById('call-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('call-modal').classList.add('hidden');
}

function toggleBash(id) {
    const preview = document.getElementById(id + '-preview');
    const full = document.getElementById(id + '-full');
    const btn = preview.parentElement.querySelector('.bash-toggle');
    if (full.classList.contains('hidden')) {
        preview.classList.add('hidden');
        full.classList.remove('hidden');
        btn.textContent = 'collapse';
    } else {
        full.classList.add('hidden');
        preview.classList.remove('hidden');
        const lines = full.textContent.split('\n').length;
        btn.textContent = `${lines - 5} more lines`;
    }
}

function syntaxHighlight(json) {
    return json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                    match = match.replace(/:$/, '');
                    return `<span class="${cls}">${match}</span>:`;
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-bool';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return `<span class="${cls}">${match}</span>`;
        });
}

function renderTokenChart(calls) {
    const canvas = document.getElementById('token-chart');
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    if (!calls.length) return;

    const maxTokens = Math.max(...calls.map(c => {
        const t = c.tokens || {};
        return (t.input_tokens || 0) + (t.output_tokens || 0);
    }));

    const barWidth = Math.max(6, (w - 60) / calls.length - 3);
    const colors = { input: '#3b82f6', output: '#10b981' };

    calls.forEach((call, i) => {
        const t = call.tokens || {};
        const x = 40 + i * (barWidth + 3);
        let y = h - 30;
        const segments = [
            { val: t.input_tokens || 0, color: colors.input },
            { val: t.output_tokens || 0, color: colors.output },
        ];
        for (const seg of segments) {
            const segH = (seg.val / maxTokens) * (h - 50);
            ctx.fillStyle = seg.color;
            ctx.fillRect(x, y - segH, barWidth, segH);
            y -= segH;
        }
    });

    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px -apple-system, sans-serif';
    ctx.fillText('input', 40, h - 10);
    ctx.fillStyle = colors.input; ctx.fillRect(24, h - 18, 8, 8);
    ctx.fillStyle = '#94a3b8'; ctx.fillText('output', 110, h - 10);
    ctx.fillStyle = colors.output; ctx.fillRect(94, h - 18, 8, 8);
}

function renderLatencyChart(calls) {
    const canvas = document.getElementById('latency-chart');
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    if (!calls.length) return;

    const latencies = calls.map(c => (c.performance || {}).latency_ms || 0);
    const maxLat = Math.max(...latencies);
    const barWidth = Math.max(6, (w - 60) / calls.length - 3);

    latencies.forEach((v, i) => {
        const x = 40 + i * (barWidth + 3);
        const barH = (v / maxLat) * (h - 50);
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(x, h - 30 - barH, barWidth, barH);
    });

    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px -apple-system, sans-serif';
    ctx.fillText(`${maxLat.toFixed(0)}ms`, 40, 16);
}

function formatTokens(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
    return String(n);
}

function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

let workspaceFiles = {};

async function loadWorkspace(sessionId) {
    const section = document.getElementById('workspace-section');
    try {
        const resp = await fetch(`/api/sessions/${sessionId}/workspace`);
        const data = await resp.json();
        if (!data.tree || data.tree.length === 0) {
            section.classList.add('hidden');
            return;
        }
        section.classList.remove('hidden');
        workspaceFiles = data.files || {};
        renderFileTree(data.tree);
        document.getElementById('workspace-file-content').textContent = 'Click a file to preview';
    } catch (e) {
        section.classList.add('hidden');
    }
}

function renderFileTree(tree) {
    const container = document.getElementById('workspace-tree');
    const lines = tree.map(f => {
        const indent = f.split('/').length - 1;
        const pad = '  '.repeat(indent);
        const name = f.split('/').pop();
        return `<span class="tree-file" onclick="previewFile('${escapeHtml(f)}')">${pad}${indent > 0 ? '└─ ' : ''}${name}</span>`;
    });
    container.innerHTML = lines.join('\n');
}

function previewFile(path) {
    const content = workspaceFiles[path];
    const el = document.getElementById('workspace-file-content');
    if (content) {
        el.textContent = content;
    } else {
        el.textContent = '(binary or unsupported file)';
    }
    document.querySelectorAll('.tree-file').forEach(f => f.classList.remove('active'));
    const active = [...document.querySelectorAll('.tree-file')].find(f => f.textContent.trim().endsWith(path.split('/').pop()));
    if (active) active.classList.add('active');
}

function extractCreatedFiles(tools) {
    const created = [];
    for (const t of tools) {
        if ((t.name === 'Write' || t.name === 'Edit') && t.input?.file_path) {
            const short = t.input.file_path.split('/').slice(-2).join('/');
            created.push(short);
        } else if (t.name === 'Bash' && t.input?.command) {
            const cmd = t.input.command;
            // Detect "cat > filename" patterns
            const parts = cmd.split('\n')[0].split(/\s+/);
            for (let i = 0; i < parts.length; i++) {
                if (parts[i] === '>' || parts[i] === '>>') {
                    const next = (parts[i+1] || '').replace(/['"]/g, '');
                    if (next && !next.startsWith('/dev/')) created.push(next);
                } else if (parts[i].includes('>') && parts[i] !== '>') {
                    const after = parts[i].split('>').pop().replace(/['"]/g, '');
                    if (after && !after.startsWith('/dev/') && after.includes('.')) created.push(after);
                }
            }
            // Detect "cat > file << 'EOF'" — file is after >
            const catMatch = cmd.match(/cat\s*>\s*([^\s<]+)/);
            if (catMatch) {
                const file = catMatch[1].replace(/['"]/g, '');
                if (file && !file.startsWith('/dev/')) created.push(file);
            }
        }
    }
    return [...new Set(created)];
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
});

init();
