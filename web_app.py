#!/usr/bin/env python3
"""
PostgreSQL Enterprise Power Telemetry Analytics & Intelligent AI Platform.
Interactive PostgreSQL Primary Engine with 4 Tabbed Navigation Panels:
1. Telemetry Analytics Tab (KPIs & 4 Chart.js Visualizations)
2. AI Dashboard Tab (Qwen3 8B MCP Intelligent Chatbot & Context Memory)
3. SQL Query Tab (Interactive SQL Runner & Query Editor)
4. Raw Data Tab (PostgreSQL Telemetry Records Viewer)
"""

import sys
import os
import json
import re
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "127.0.0.1"
PORT = 5000

from database import get_repository
from ai import route_user_intent, ConversationSessionState, generate_evidence_based_explanation
from mcp import MCPServer
from analytics import (
    calculate_energy_consumption, calculate_power_metrics, calculate_voltage_metrics,
    calculate_current_metrics, analyze_telemetry_trend, analyze_telemetry_correlations,
    analyze_data_quality, evaluate_device_health
)
from ml import detect_isolation_forest_anomalies, forecast_telemetry_metric
from deep_learning import detect_lstm_autoencoder_anomalies, forecast_lstm_telemetry

# Session memory map
SESSION_MEMORY = {}

def get_session(session_id="default"):
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = ConversationSessionState()
    return SESSION_MEMORY[session_id]

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PostgreSQL Telemetry Analytics & AI Portal</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg-dark: #0b0f19;
      --bg-card: #151c2e;
      --bg-hover: #1e293b;
      --border-color: #2d3e5f;
      --text-main: #f8fafc;
      --text-dim: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-indigo: #6366f1;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      --accent-purple: #a855f7;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
    body { background-color: var(--bg-dark); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; overflow-x: hidden; }

    header {
      background: rgba(21, 28, 46, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-color);
      padding: 0.75rem 1.5rem;
      display: flex; justify-content: space-between; align-items: center;
      position: sticky; top: 0; z-index: 100;
    }
    .brand { display: flex; align-items: center; gap: 0.75rem; font-size: 1.1rem; font-weight: 700; color: var(--text-main); }

    .nav-tabs { display: flex; gap: 0.5rem; background: #0f172a; padding: 0.25rem; border-radius: 0.65rem; border: 1px solid var(--border-color); }
    .nav-tab {
      background: transparent; color: var(--text-dim); border: none; padding: 0.5rem 1.1rem;
      border-radius: 0.45rem; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: all 0.2s;
    }
    .nav-tab.active { background: linear-gradient(135deg, var(--accent-blue), var(--accent-indigo)); color: white; }
    .nav-tab:hover:not(.active) { color: var(--text-main); background: var(--bg-hover); }

    .badge-status { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); padding: 0.25rem 0.65rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); }

    .layout-wrapper { display: flex; flex: 1; min-height: calc(100vh - 60px); }
    
    .sidebar-controls {
      width: 300px; background: var(--bg-card); border-right: 1px solid var(--border-color);
      padding: 1.25rem; display: flex; flex-direction: column; gap: 1.1rem; overflow-y: auto;
    }

    .section-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent-blue); margin-bottom: 0.2rem; }
    .form-group { display: flex; flex-direction: column; gap: 0.35rem; }
    label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-dim); }
    input, select, textarea {
      background: #0f172a; border: 1px solid var(--border-color); color: var(--text-main);
      padding: 0.55rem 0.75rem; border-radius: 0.5rem; font-size: 0.85rem; outline: none; width: 100%;
    }
    input:focus, select:focus, textarea:focus { border-color: var(--accent-blue); }

    .btn {
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-indigo));
      color: white; border: none; padding: 0.65rem 1rem; border-radius: 0.5rem;
      font-weight: 600; cursor: pointer; transition: all 0.2s; text-align: center;
    }
    .btn:hover { opacity: 0.9; transform: translateY(-1px); }

    .main-content { flex: 1; padding: 1.25rem; display: flex; flex-direction: column; gap: 1.25rem; overflow-y: auto; }
    .tab-panel { display: none; flex-direction: column; gap: 1.25rem; width: 100%; }
    .tab-panel.active { display: flex; }

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
    .kpi-card { background: var(--bg-card); border: 1px solid var(--border-color); padding: 1rem; border-radius: 0.75rem; }
    .kpi-title { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; font-weight: 600; }
    .kpi-value { font-size: 1.35rem; font-weight: 700; color: var(--accent-blue); margin-top: 0.35rem; }

    .charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.25rem; }
    .chart-card { background: var(--bg-card); border: 1px solid var(--border-color); padding: 1rem; border-radius: 0.75rem; display: flex; flex-direction: column; gap: 0.75rem; height: 320px; }
    .chart-title { font-size: 0.85rem; font-weight: 600; color: var(--text-main); }
    .chart-container { flex: 1; position: relative; width: 100%; height: 100%; }

    /* AI Dashboard Tab Styling */
    .ai-dashboard-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 0.75rem; display: flex; flex-direction: column; height: calc(100vh - 120px); overflow: hidden; }
    .chat-header { padding: 1rem 1.25rem; border-bottom: 1px solid var(--border-color); font-weight: 600; font-size: 1rem; display: flex; align-items: center; justify-content: space-between; background: #0f172a; }
    .chat-messages { flex: 1; padding: 1.25rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; }
    .msg-bubble { padding: 0.85rem 1.1rem; border-radius: 0.75rem; font-size: 0.9rem; line-height: 1.6; max-width: 85%; }
    .msg-user { background: var(--accent-indigo); align-self: flex-end; color: white; }
    .msg-ai { background: #0f172a; border: 1px solid var(--border-color); align-self: flex-start; }
    .chat-input-area { padding: 1rem 1.25rem; border-top: 1px solid var(--border-color); display: flex; gap: 0.75rem; background: #0f172a; }

    .quick-prompts { display: flex; gap: 0.5rem; flex-wrap: wrap; padding: 0 1.25rem 0.75rem 1.25rem; background: #0f172a; }
    .chip { background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-dim); padding: 0.35rem 0.75rem; border-radius: 999px; font-size: 0.78rem; cursor: pointer; transition: all 0.2s; }
    .chip:hover { border-color: var(--accent-blue); color: var(--text-main); }

    .table-wrapper { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 0.75rem; overflow: hidden; }
    table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    th, td { padding: 0.65rem 0.9rem; text-align: left; border-bottom: 1px solid var(--border-color); }
    th { background: #0f172a; color: var(--text-dim); font-weight: 600; }
    tr:hover { background: var(--bg-hover); }

    @media (max-width: 1100px) { .charts-grid { grid-template-columns: 1fr; } .layout-wrapper { flex-direction: column; } .sidebar-controls { width: 100%; } }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <span>PostgreSQL Power Telemetry & AI Analytics Platform</span>
    </div>

    <!-- 4 Navigation Tabs -->
    <div class="nav-tabs">
      <button class="nav-tab active" onclick="switchTab('analyticsTab', this)">Analytics</button>
      <button class="nav-tab" onclick="switchTab('aiTab', this)">AI Dashboard</button>
      <button class="nav-tab" onclick="switchTab('sqlTab', this)">SQL Query</button>
      <button class="nav-tab" onclick="switchTab('rawDataTab', this)">Raw Data</button>
    </div>

    <div class="badge-status disconnected" id="dbConnStatus">PostgreSQL Disconnected</div>
  </header>

  <div class="layout-wrapper">
    <!-- Sidebar Connection & Filter Controls -->
    <div class="sidebar-controls">
      <div class="section-title">PostgreSQL Connection Settings</div>
      <div class="form-group">
        <label>Host</label>
        <input type="text" id="dbHost" value="localhost">
      </div>
      <div class="form-group">
        <label>Port</label>
        <input type="number" id="dbPort" value="5432">
      </div>
      <div class="form-group">
        <label>Database</label>
        <input type="text" id="dbName" value="postgres">
      </div>
      <div class="form-group">
        <label>User</label>
        <input type="text" id="dbUser" value="postgres">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" id="dbPassword" placeholder="Enter DB Password">
      </div>

      <div class="section-title" style="margin-top: 0.5rem;">Telemetry Analytics Filters</div>
      <div class="form-group">
        <label>Select Table</label>
        <select id="tableSelect"><option value="energymeter">energymeter</option></select>
      </div>

      <!-- Multiple Devices View Selector -->
      <div class="form-group">
        <label>Select Device (Multiple Devices View)</label>
        <select id="deviceSelect">
          <option value="">All Devices</option>
        </select>
      </div>

      <div class="form-group">
        <label>Time Window (Hours)</label>
        <input type="number" id="hoursInput" value="24" min="1" max="720">
      </div>

      <button class="btn" onclick="connectAndFetchTelemetry()">Connect & Fetch Telemetry</button>
    </div>

    <!-- Main Content Area with 4 Tab Panels -->
    <div class="main-content">
      
      <!-- TAB 1: TELEMETRY ANALYTICS TAB -->
      <div id="analyticsTab" class="tab-panel active">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-title">Total Records</div>
            <div class="kpi-value" id="kpiTotalRows">0</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Net Energy Consumed</div>
            <div class="kpi-value" id="kpiNetEnergy">0 kWh</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Average Active Power</div>
            <div class="kpi-value" id="kpiAvgPower">0 kW</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Peak Active Load</div>
            <div class="kpi-value" id="kpiPeakPower">0 kW</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Average Line Voltage</div>
            <div class="kpi-value" id="kpiAvgVoltage">0 V</div>
          </div>
        </div>

        <div class="charts-grid">
          <div class="chart-card">
            <div class="chart-title">Power Load Triad (Active kW, Reactive kVAR, Apparent kVA)</div>
            <div class="chart-container"><canvas id="chartPowerTriad"></canvas></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">3-Phase Voltage Bands (Voltage AB, BC, CA, AN, BN, CN)</div>
            <div class="chart-container"><canvas id="chartVoltageBand"></canvas></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">3-Phase Current & Amperage Load (Average Amps & Phase A, B, C)</div>
            <div class="chart-container"><canvas id="chartCurrentPhase"></canvas></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">Power Factor Efficiency & Grid Frequency (Hz)</div>
            <div class="chart-container"><canvas id="chartPfFreq"></canvas></div>
          </div>
        </div>
      </div>

      <!-- TAB 2: AI DASHBOARD TAB -->
      <div id="aiTab" class="tab-panel">
        <div class="ai-dashboard-card">
          <div class="chat-header">
            <span>Qwen3 8B Intelligent AI Assistant & Analytics Engine</span>
            <span style="font-size: 0.78rem; color: var(--accent-blue);">MCP Protocol Active</span>
          </div>

          <div class="chat-messages" id="chatMessages">
            <div class="msg-bubble msg-ai">
              Hello, I'm your telemetry assistant!
            </div>
          </div>

          <div class="quick-prompts">
            <div class="chip" onclick="askQuick('Average active power for Device 1?')">Average active power for Device 1?</div>
            <div class="chip" onclick="askQuick('What about Device 2?')">What about Device 2?</div>
            <div class="chip" onclick="askQuick('Net energy consumed for Device 1')">Net energy consumed</div>
            <div class="chip" onclick="askQuick('Compare Device 1 and Device 2')">Compare Device 1 & 2</div>
          </div>

          <div class="chat-input-area">
            <input type="text" id="chatInput" placeholder="Ask a telemetry, device, or analytics question..." onkeypress="if(event.key==='Enter') sendChatMessage()">
            <button class="btn" onclick="sendChatMessage()">Send Question</button>
          </div>
        </div>
      </div>

      <!-- TAB 3: SQL QUERY TAB -->
      <div id="sqlTab" class="tab-panel">
        <div class="kpi-card" style="display: flex; flex-direction: column; gap: 1rem;">
          <div style="font-size: 0.95rem; font-weight: 600;">Interactive SQL Query Runner</div>
          <textarea id="sqlConsole" rows="4">SELECT time, deviceid, activepower, voltageab, currentavg, importenergykwh FROM public."energymeter" ORDER BY time DESC LIMIT 20;</textarea>
          <div style="display: flex; justify-content: flex-end;">
            <button class="btn" onclick="runCustomSql()">Execute Custom SQL</button>
          </div>
        </div>

        <div class="table-wrapper">
          <div style="padding: 0.85rem; font-weight: 600; border-bottom: 1px solid var(--border-color);">
            SQL Query Results Output
          </div>
          <table>
            <thead><tr id="sqlTableHead"></tr></thead>
            <tbody id="sqlTableBody"></tbody>
          </table>
        </div>
      </div>

      <!-- TAB 4: RAW DATA TAB -->
      <div id="rawDataTab" class="tab-panel">
        <div class="table-wrapper">
          <div style="padding: 0.85rem; font-weight: 600; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
            <span>PostgreSQL Telemetry Records Viewer</span>
            <span style="font-size: 0.78rem; color: var(--text-dim);" id="rawRecordCount">Showing latest 50 records</span>
          </div>
          <table>
            <thead><tr id="rawTableHead"></tr></thead>
            <tbody id="rawTableBody"></tbody>
          </table>
        </div>
      </div>

    </div>
  </div>

  <script>
    let cPower, cVoltage, cCurrent, cPfFreq;
    let chatHistory = [];

    const chartDefaults = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } } } },
      scales: {
        x: { ticks: { display: false }, grid: { display: false } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(45, 62, 95, 0.4)' } }
      }
    };

    function switchTab(tabId, element) {
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      element.classList.add('active');
    }

    function getDBCreds() {
      return {
        host: document.getElementById('dbHost').value || 'localhost',
        port: parseInt(document.getElementById('dbPort').value || '5432'),
        dbname: document.getElementById('dbName').value || 'postgres',
        user: document.getElementById('dbUser').value || 'postgres',
        password: document.getElementById('dbPassword').value || ''
      };
    }

    function initPage() {
      document.getElementById('dbConnStatus').innerText = 'PostgreSQL Disconnected';
      document.getElementById('dbConnStatus').style.color = 'var(--accent-amber)';
    }

    async function fetchDevices() {
      try {
        const creds = getDBCreds();
        creds.table = document.getElementById('tableSelect').value || 'energymeter';
        const res = await fetch('/api/devices', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(creds)
        });
        const data = await res.json();
        if (data.devices) {
          const sel = document.getElementById('deviceSelect');
          sel.innerHTML = '<option value="">All Devices</option>' + data.devices.map(d => `<option value="${d}">Device ${d}</option>`).join('');
        }
      } catch (e) {}
    }

    async function connectAndFetchTelemetry() {
      const creds = getDBCreds();
      creds.table = document.getElementById('tableSelect').value || 'energymeter';
      creds.deviceid = document.getElementById('deviceSelect').value;
      creds.hours = document.getElementById('hoursInput').value || 24;

      try {
        const res = await fetch('/api/telemetry-analytics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(creds)
        });
        const data = await res.json();

        if (!data.success) {
          document.getElementById('dbConnStatus').innerText = 'PostgreSQL Disconnected';
          document.getElementById('dbConnStatus').style.color = 'var(--accent-amber)';
          alert(data.error || 'PostgreSQL Connection Failed. Please check database password and credentials.');
          return;
        }

        document.getElementById('dbConnStatus').innerText = 'PostgreSQL Connected';
        document.getElementById('dbConnStatus').style.color = 'var(--accent-green)';

        fetchDevices();

        // KPIs
        const kpis = data.kpis || {};
        document.getElementById('kpiTotalRows').innerText = (kpis.total_rows || 0).toLocaleString();
        document.getElementById('kpiNetEnergy').innerText = (kpis.net_energy_kwh || 0).toLocaleString() + ' kWh';
        document.getElementById('kpiAvgPower').innerText = (kpis.avg_power_kw || 0).toLocaleString() + ' kW';
        document.getElementById('kpiPeakPower').innerText = (kpis.peak_power_kw || 0).toLocaleString() + ' kW';
        document.getElementById('kpiAvgVoltage').innerText = (kpis.avg_voltage_v || 0).toLocaleString() + ' V';

        renderCharts(data.series || {});
        renderRawTable(data.columns || [], data.rows || []);
      } catch (e) {
        document.getElementById('dbConnStatus').innerText = 'PostgreSQL Disconnected';
        document.getElementById('dbConnStatus').style.color = 'var(--accent-amber)';
        alert('Could not connect to PostgreSQL. Please verify host, user, and password.');
      }
    }

    function renderCharts(s) {
      const timeLabels = s.time || [];

      if (cPower) cPower.destroy();
      cPower = new Chart(document.getElementById('chartPowerTriad'), {
        type: 'line',
        data: {
          labels: timeLabels,
          datasets: [
            { label: 'Active Power (kW)', data: s.activepower || [], borderColor: '#38bdf8', borderWidth: 2, tension: 0.3 },
            { label: 'Reactive Power (kVAR)', data: s.reactivepower || [], borderColor: '#a855f7', borderWidth: 1.5, tension: 0.3 },
            { label: 'Apparent Power (kVA)', data: s.apparentpower || [], borderColor: '#6366f1', borderWidth: 1.5, tension: 0.3 }
          ]
        },
        options: chartDefaults
      });

      if (cVoltage) cVoltage.destroy();
      cVoltage = new Chart(document.getElementById('chartVoltageBand'), {
        type: 'line',
        data: {
          labels: timeLabels,
          datasets: [
            { label: 'Voltage AB', data: s.voltageab || [], borderColor: '#f59e0b', tension: 0.3, borderWidth: 1.5 },
            { label: 'Voltage BC', data: s.voltagebc || [], borderColor: '#ec4899', tension: 0.3, borderWidth: 1.5 },
            { label: 'Voltage CA', data: s.voltageca || [], borderColor: '#38bdf8', tension: 0.3, borderWidth: 1.5 },
            { label: 'Phase AN', data: s.voltagean || [], borderColor: '#10b981', borderDash: [4, 4], borderWidth: 1 },
            { label: 'Phase BN', data: s.voltagebn || [], borderColor: '#a855f7', borderDash: [4, 4], borderWidth: 1 },
            { label: 'Phase CN', data: s.voltagecn || [], borderColor: '#06b6d4', borderDash: [4, 4], borderWidth: 1 }
          ]
        },
        options: chartDefaults
      });

      if (cCurrent) cCurrent.destroy();
      cCurrent = new Chart(document.getElementById('chartCurrentPhase'), {
        type: 'line',
        data: {
          labels: timeLabels,
          datasets: [
            { label: 'Current Avg (A)', data: s.currentavg || [], borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.15)', fill: true, tension: 0.3, borderWidth: 2.5 },
            { label: 'Current Phase A', data: s.currenta || [], borderColor: '#38bdf8', borderWidth: 1.5 },
            { label: 'Current Phase B', data: s.currentb || [], borderColor: '#f59e0b', borderWidth: 1.5 },
            { label: 'Current Phase C', data: s.currentc || [], borderColor: '#ec4899', borderWidth: 1.5 }
          ]
        },
        options: chartDefaults
      });

      if (cPfFreq) cPfFreq.destroy();
      cPfFreq = new Chart(document.getElementById('chartPfFreq'), {
        type: 'line',
        data: {
          labels: timeLabels,
          datasets: [
            { label: 'Power Factor', data: s.powerfactor || [], borderColor: '#a855f7', yAxisID: 'yPF', tension: 0.3, borderWidth: 2 },
            { label: 'Grid Frequency (Hz)', data: s.frequency || [], borderColor: '#38bdf8', yAxisID: 'yHz', tension: 0.3, borderWidth: 1.5 }
          ]
        },
        options: {
          ...chartDefaults,
          scales: {
            ...chartDefaults.scales,
            yPF: { type: 'linear', position: 'left', ticks: { color: '#a855f7' }, grid: { color: 'rgba(45, 62, 95, 0.4)' } },
            yHz: { type: 'linear', position: 'right', ticks: { color: '#38bdf8' }, grid: { drawOnChartArea: false } }
          }
        }
      });
    }

    function renderRawTable(cols, rows) {
      const head = document.getElementById('rawTableHead');
      const body = document.getElementById('rawTableBody');
      if (!cols || cols.length === 0) {
        head.innerHTML = '<tr><th>No Telemetry Data</th></tr>';
        body.innerHTML = '';
        return;
      }
      head.innerHTML = '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';
      body.innerHTML = rows.map(r => '<tr>' + r.map(v => `<td>${v === null ? '<i style="color:var(--text-dim)">NULL</i>' : v}</td>`).join('') + '</tr>').join('');
    }

    function renderSqlTable(cols, rows) {
      const head = document.getElementById('sqlTableHead');
      const body = document.getElementById('sqlTableBody');
      if (!cols || cols.length === 0) {
        head.innerHTML = '<tr><th>No Query Results</th></tr>';
        body.innerHTML = '';
        return;
      }
      head.innerHTML = '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';
      body.innerHTML = rows.map(r => '<tr>' + r.map(v => `<td>${v === null ? '<i style="color:var(--text-dim)">NULL</i>' : v}</td>`).join('') + '</tr>').join('');
    }

    async function runCustomSql() {
      const sql = document.getElementById('sqlConsole').value.trim();
      if (!sql) return;
      const creds = getDBCreds();
      creds.sql = sql;
      try {
        const res = await fetch('/api/custom-query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(creds)
        });
        const data = await res.json();
        if (data.success) {
          renderSqlTable(data.columns, data.rows);
        }
      } catch (e) {}
    }

    function askQuick(text) {
      document.getElementById('chatInput').value = text;
      sendChatMessage();
    }

    async function sendChatMessage() {
      const input = document.getElementById('chatInput');
      const question = input.value.trim();
      if (!question) return;

      const msgs = document.getElementById('chatMessages');
      const userMsg = document.createElement('div');
      userMsg.className = 'msg-bubble msg-user';
      userMsg.innerText = question;
      msgs.appendChild(userMsg);

      input.value = '';
      msgs.scrollTop = msgs.scrollHeight;

      const aiMsg = document.createElement('div');
      aiMsg.className = 'msg-bubble msg-ai';
      aiMsg.innerHTML = '<div><em>Analyzing question via Qwen3 8B & MCP Tools...</em></div>';
      msgs.appendChild(aiMsg);
      msgs.scrollTop = msgs.scrollHeight;

      const creds = getDBCreds();
      creds.question = question;
      creds.history = chatHistory;
      creds.table = document.getElementById('tableSelect').value || 'energymeter';

      try {
        const res = await fetch('/api/ai-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(creds)
        });
        const data = await res.json();
        if (!data.success) {
          aiMsg.innerHTML = `<div>Error: ${data.error}</div>`;
          return;
        }

        aiMsg.innerHTML = `<div style="font-weight: 500; font-size: 0.95rem; color: #f8fafc; line-height: 1.6;">${data.answer}</div>`;

        chatHistory.push({ role: 'user', content: question });
        chatHistory.push({ role: 'assistant', content: data.answer });
        if (chatHistory.length > 20) {
          chatHistory = chatHistory.slice(chatHistory.length - 20);
        }

        msgs.scrollTop = msgs.scrollHeight;
      } catch (err) {
        aiMsg.innerHTML = `<div>Error: ${err.message}</div>`;
      }
    }

    window.onload = initPage;
  </script>
</body>
</html>"""

class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._set_headers(200, "text/html")
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        data = json.loads(post_body.decode("utf-8")) if post_body else {}

        repo = get_repository(db_credentials=data)

        if self.path == "/api/devices":
            table = data.get("table", "energymeter")
            devices = repo.list_devices(table)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "devices": devices}).encode("utf-8"))

        elif self.path == "/api/telemetry-analytics":
            table = data.get("table", "energymeter")
            dev_id = data.get("deviceid")
            if dev_id == "": dev_id = None
            hours = data.get("hours", 24)

            p_res = calculate_power_metrics(repo, table=table, device_id=dev_id, hours=hours)
            e_res = calculate_energy_consumption(repo, table=table, device_id=dev_id, hours=hours)
            v_res = calculate_voltage_metrics(repo, table=table, device_id=dev_id, hours=hours)

            dev_clause = f"AND deviceid = '{dev_id}'" if dev_id else ""
            sql = f"""
                SELECT time::text, activepower, reactivepower, apparentpower, voltageab, voltagebc, voltageca, voltagean, voltagebn, voltagecn, currentavg, currenta, currentb, currentc, powerfactor, frequency
                FROM public."{table}" WHERE 1=1 {dev_clause} ORDER BY time ASC LIMIT 300;
            """
            series_raw = repo.execute_query(sql)
            rows = series_raw.get("rows", [])

            series = {
                "time": [r[0] for r in rows],
                "activepower": [r[1] for r in rows],
                "reactivepower": [r[2] for r in rows],
                "apparentpower": [r[3] for r in rows],
                "voltageab": [r[4] for r in rows],
                "voltagebc": [r[5] for r in rows],
                "voltageca": [r[6] for r in rows],
                "voltagean": [r[7] for r in rows],
                "voltagebn": [r[8] for r in rows],
                "voltagecn": [r[9] for r in rows],
                "currentavg": [r[10] for r in rows],
                "currenta": [r[11] for r in rows],
                "currentb": [r[12] for r in rows],
                "currentc": [r[13] for r in rows],
                "powerfactor": [r[14] for r in rows],
                "frequency": [r[15] for r in rows]
            }

            raw_table_sql = f'SELECT * FROM public."{table}" WHERE 1=1 {dev_clause} ORDER BY time DESC LIMIT 50;'
            raw_res = repo.execute_query(raw_table_sql)

            response = {
                "success": series_raw.get("success", False),
                "source": series_raw.get("source", "PostgreSQL Primary"),
                "kpis": {
                    "total_rows": len(rows),
                    "net_energy_kwh": e_res.get("net_energy_kwh", 0),
                    "avg_power_kw": p_res.get("avg_active_kw", 0),
                    "peak_power_kw": p_res.get("max_active_kw", 0),
                    "avg_voltage_v": v_res.get("avg_line_voltage", 0)
                },
                "series": series,
                "columns": raw_res.get("columns", []),
                "rows": raw_res.get("rows", [])
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/ai-chat":
            question = data.get("question", "")
            history = data.get("history", [])
            table = data.get("table", "energymeter")
            session = get_session("default")

            from ai.source_router import classify_information_source
            from rag import search_knowledge_base
            from ai.web_search import search_web

            # 1. Source Router Classification
            route_info = classify_information_source(question)
            route = route_info.get("route", "TELEMETRY")
            sources = route_info.get("sources", [route])

            telemetry_result = None
            rag_result = None
            web_result = None

            # 2. Execute TELEMETRY Path if active
            if "TELEMETRY" in sources or route in ["TELEMETRY", "HYBRID"]:
                intent_data = route_user_intent(question, session_state=session)
                resolved_intent = session.resolve_followup(intent_data)

                intent = resolved_intent.get("intent", "power_analysis")
                dev_id = resolved_intent.get("device_id")
                hours = resolved_intent.get("duration_hours")

                if intent == "conversation" and route == "TELEMETRY":
                    explanation = "Hello, I'm your telemetry assistant!"
                    self._set_headers(200)
                    self.wfile.write(json.dumps({
                        "success": True,
                        "answer": explanation,
                        "intent": "conversation",
                        "source_route": route_info
                    }).encode("utf-8"))
                    return

                tool_map = {
                    "list_devices": ("mcp_list_devices", {}),
                    "energy_consumption": ("mcp_get_energy_consumption", {"hours": hours, "deviceid": dev_id}),
                    "power_analysis": ("mcp_get_power_metrics", {"hours": hours, "deviceid": dev_id}),
                    "voltage_analysis": ("mcp_get_voltage_metrics", {"hours": hours, "deviceid": dev_id}),
                    "current_analysis": ("mcp_get_current_metrics", {"hours": hours, "deviceid": dev_id}),
                    "frequency_analysis": ("mcp_get_frequency_metrics", {"hours": hours, "deviceid": dev_id}),
                    "power_factor_analysis": ("mcp_get_power_factor", {"hours": hours, "deviceid": dev_id}),
                    "device_summary": ("mcp_get_device_summary", {"deviceid": dev_id or "1"}),
                    "compare_devices": ("mcp_compare_devices", {"device1": dev_id or "1", "device2": resolved_intent.get("comparison_device", "2"), "hours": hours or 24}),
                    "compare_periods": ("mcp_compare_periods", {"deviceid": dev_id or "1", "period1_hours": hours or 24, "period2_hours": 48}),
                    "phase_imbalance": ("mcp_get_phase_imbalance", {"deviceid": dev_id or "1", "hours": hours or 24}),
                    "anomaly_analysis": ("mcp_detect_anomalies", {"deviceid": dev_id, "hours": hours or 24}),
                    "device_health": ("mcp_get_device_health", {"deviceid": dev_id or "1", "hours": hours or 24}),
                    "correlation_analysis": ("mcp_get_correlations", {"deviceid": dev_id, "hours": hours or 24}),
                    "trend_analysis": ("mcp_get_trend_analysis", {"deviceid": dev_id, "hours": hours or 24}),
                    "forecast_power": ("mcp_forecast_power", {"deviceid": dev_id, "horizon": resolved_intent.get("forecast_horizon", 6)}),
                    "forecast_energy": ("mcp_forecast_energy", {"deviceid": dev_id, "horizon": resolved_intent.get("forecast_horizon", 6)}),
                    "explain_anomaly": ("mcp_explain_anomaly", {"deviceid": dev_id or "1"}),
                    "database_summary": ("mcp_get_database_summary", {})
                }

                tool_name, tool_kwargs = tool_map.get(intent, ("mcp_get_power_metrics", {"hours": hours, "deviceid": dev_id}))
                telemetry_result = MCPServer.execute_tool(tool_name, tool_kwargs, repo, table=table)
                session.update(resolved_intent)

            # 3. Execute RAG Path if active
            if "RAG" in sources or route in ["RAG", "HYBRID"]:
                rag_result = search_knowledge_base(question)

            # 4. Execute WEB Path if active
            if "WEB" in sources or route in ["WEB", "HYBRID"]:
                web_result = search_web(question)

            # 5. Generate Multi-Source Grounded Explanation
            explanation = generate_evidence_based_explanation(
                question, route_info=route_info, telemetry_result=telemetry_result,
                rag_result=rag_result, web_result=web_result, session_state=session
            )

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "success": True,
                "answer": explanation,
                "source_route": route_info
            }).encode("utf-8"))

        elif self.path == "/api/custom-query":
            sql = data.get("sql", "").strip()
            forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
            if any(cmd in sql.upper() for cmd in forbidden):
                self._set_headers(403)
                self.wfile.write(json.dumps({"success": False, "error": "Security Restriction: Only SELECT queries are permitted."}).encode("utf-8"))
                return

            res = repo.execute_query(sql)
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

def run_server():
    server_address = ("127.0.0.1", 5000)
    httpd = HTTPServer(server_address, RequestHandler)
    print("=======================================================")
    print(" Unified Power Telemetry AI Platform Server Running at:")
    print("  http://127.0.0.1:5000")
    print("=======================================================")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
