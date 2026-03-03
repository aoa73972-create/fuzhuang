/**
 * 纯前端 localStorage 数据层 - 无后端，数据保存在浏览器
 * 当 window.API_BASE === 'local' 时使用
 */
(function() {
  const KEY = {
    employees: 'piecework_local_employees',
    rates: 'piecework_local_rates',
    records: 'piecework_local_records',
    orders: 'piecework_local_orders',
    nextId: 'piecework_local_nextId'
  };

  function nextId() {
    let n = parseInt(localStorage.getItem(KEY.nextId) || '1', 10);
    localStorage.setItem(KEY.nextId, String(n + 1));
    return n;
  }

  function get(k, def = []) {
    try {
      const s = localStorage.getItem(k);
      return s ? JSON.parse(s) : def;
    } catch { return def; }
  }
  function set(k, v) { localStorage.setItem(k, JSON.stringify(v)); }

  window.LocalStorageAPI = {
    async login(data) {
      return { ok: true, token: 'local', user: { username: data.username || 'admin', role: 'admin' } };
    },
    async getEmployees() { return { data: get(KEY.employees) }; },
    async postEmployee(data) {
      const list = get(KEY.employees);
      const id = nextId();
      list.push({ id, name: (data.name || '').trim(), employee_no: data.employee_no || null, department: data.department || null });
      set(KEY.employees, list);
      return { id };
    },
    async putEmployee(id, data) {
      const list = get(KEY.employees);
      const i = list.findIndex(x => x.id === id);
      if (i >= 0) { list[i] = { ...list[i], name: (data.name || '').trim(), employee_no: data.employee_no || null, department: data.department || null }; set(KEY.employees, list); }
      return {};
    },
    async deleteEmployee(id) {
      set(KEY.employees, get(KEY.employees).filter(x => x.id !== id));
      return {};
    },
    async postEmployeesBatch(data) {
      const names = (data.names || '').split(/[\n,，\s]+/).map(n => n.trim()).filter(Boolean);
      const list = get(KEY.employees);
      let added = 0;
      for (const name of names) {
        if (list.some(x => x.name === name)) continue;
        list.push({ id: nextId(), name, employee_no: null, department: null });
        added++;
      }
      set(KEY.employees, list);
      return { added };
    },
    async getPieceRates() { return { data: get(KEY.rates) }; },
    async postPieceRate(data) {
      const list = get(KEY.rates);
      const id = nextId();
      list.push({ id, style_code: (data.style_code || '').trim(), size: (data.size || '').trim() || null, unit_price: parseFloat(data.unit_price) || 0 });
      set(KEY.rates, list);
      return { id };
    },
    async putPieceRate(id, data) {
      const list = get(KEY.rates);
      const i = list.findIndex(x => x.id === id);
      if (i >= 0) { list[i] = { ...list[i], style_code: (data.style_code || '').trim(), size: (data.size || '').trim() || null, unit_price: parseFloat(data.unit_price) || 0 }; set(KEY.rates, list); }
      return {};
    },
    async deletePieceRate(id) { set(KEY.rates, get(KEY.rates).filter(x => x.id !== id)); return {}; },
    async getPieceRecords(params) {
      let list = get(KEY.records);
      const empId = params.employee_id;
      const month = params.month;
      const record_date = params.record_date;
      const start_date = params.start_date;
      const end_date = params.end_date;
      const size = params.size;
      if (empId) list = list.filter(r => r.employee_id === empId);
      if (month) list = list.filter(r => (r.record_date || '').slice(0, 7) === month);
      if (record_date) list = list.filter(r => r.record_date === record_date);
      if (start_date) list = list.filter(r => r.record_date >= start_date);
      if (end_date) list = list.filter(r => r.record_date <= end_date);
      if (size) list = list.filter(r => (r.size || '') === size);
      const emps = get(KEY.employees);
      list = list.map(r => ({ ...r, employee_name: (emps.find(e => e.id === r.employee_id) || {}).name }));
      list.sort((a, b) => (b.record_date || '').localeCompare(a.record_date) || (b.id - a.id));
      return { data: list };
    },
    async postPieceRecordsByStyle(data) {
      const items = data.items || [];
      const emps = get(KEY.employees);
      const list = get(KEY.records);
      const style_code = (data.style_code || '').trim();
      const size = (data.size || '').trim() || null;
      const unit_price = parseFloat(data.unit_price) || 0;
      const record_date = (data.record_date || '').trim();
      for (const it of items) {
        const qty = parseInt(it.quantity, 10) || 0;
        if (qty <= 0) continue;
        const empId = parseInt(it.employee_id, 10);
        const emp = emps.find(e => e.id === empId);
        const id = nextId();
        const amount = qty * unit_price;
        list.push({ id, employee_id: empId, employee_name: emp ? emp.name : '', style_code, size, record_date, quantity: qty, unit_price, amount });
      }
      set(KEY.records, list);
      return {};
    },
    async putPieceRecord(id, data) {
      const list = get(KEY.records);
      const i = list.findIndex(x => x.id === id);
      if (i >= 0) {
        const r = list[i];
        const qty = parseInt(data.quantity, 10) || 0;
        const up = parseFloat(data.unit_price) || 0;
        list[i] = { ...r, size: (data.size || '').trim() || null, quantity: qty, unit_price: up, amount: qty * up };
        set(KEY.records, list);
      }
      return {};
    },
    async postPieceRecordsClearAll() { set(KEY.records, []); return {}; },
    async getSalarySummary(params) {
      let list = get(KEY.records);
      const empId = params.employee_id;
      const month = params.month;
      if (empId) list = list.filter(r => r.employee_id === empId);
      if (month) list = list.filter(r => (r.record_date || '').slice(0, 7) === month);
      const emps = get(KEY.employees);
      const byEmpMonth = {};
      for (const r of list) {
        const m = (r.record_date || '').slice(0, 7);
        if (!m) continue;
        const k = r.employee_id + '|' + m;
        if (!byEmpMonth[k]) byEmpMonth[k] = { employee_id: r.employee_id, employee_name: (emps.find(e => e.id === r.employee_id) || {}).name, month: m, total_qty: 0, total_amount: 0 };
        byEmpMonth[k].total_qty += parseInt(r.quantity, 10) || 0;
        byEmpMonth[k].total_amount += parseFloat(r.amount) || 0;
      }
      const monthly = Object.values(byEmpMonth).sort((a, b) => (b.month || '').localeCompare(a.month) || (a.employee_id - b.employee_id));
      return { monthly };
    },
    async getStatsProcessShare(params) {
      const month = (params.month || '').slice(0, 7);
      let list = get(KEY.records);
      if (month) list = list.filter(r => (r.record_date || '').slice(0, 7) === month);
      const byStyle = {};
      for (const r of list) {
        const k = r.style_code || '其他';
        if (!byStyle[k]) byStyle[k] = { label: k, qty: 0, value: 0 };
        byStyle[k].qty += parseInt(r.quantity, 10) || 0;
        byStyle[k].value += parseFloat(r.amount) || 0;
      }
      const total = Object.values(byStyle).reduce((s, x) => s + x.value, 0);
      const data = Object.values(byStyle).map(x => ({ ...x, percent: total ? Math.round(x.value / total * 100) : 0 }));
      return { data };
    },
    async getStatsEmployeeRanking(params) {
      const month = (params.month || '').slice(0, 7);
      let list = get(KEY.records);
      if (month) list = list.filter(r => (r.record_date || '').slice(0, 7) === month);
      const emps = get(KEY.employees);
      const byEmp = {};
      for (const r of list) {
        const id = r.employee_id;
        if (!byEmp[id]) byEmp[id] = { name: (emps.find(e => e.id === id) || {}).name, total_qty: 0, total_amount: 0 };
        byEmp[id].total_qty += parseInt(r.quantity, 10) || 0;
        byEmp[id].total_amount += parseFloat(r.amount) || 0;
      }
      const data = Object.entries(byEmp).map(([id, v]) => ({ ...v, id: parseInt(id, 10) })).sort((a, b) => (b.total_amount || 0) - (a.total_amount || 0));
      return { data };
    },
    async getWorkOrders() { return { data: get(KEY.orders) }; },
    async postWorkOrder(data) {
      const list = get(KEY.orders);
      const id = nextId();
      list.push({ id, order_no: (data.order_no || '').trim(), style_code: (data.style_code || '').trim(), quantity: parseInt(data.quantity, 10) || 0, delivery_date: data.delivery_date || null });
      set(KEY.orders, list);
      return { id };
    },
    async putWorkOrder(id, data) {
      const list = get(KEY.orders);
      const i = list.findIndex(x => x.id === id);
      if (i >= 0) { list[i] = { ...list[i], order_no: (data.order_no || '').trim(), style_code: (data.style_code || '').trim(), quantity: parseInt(data.quantity, 10) || 0, delivery_date: data.delivery_date || null }; set(KEY.orders, list); }
      return {};
    },
    async deleteWorkOrder(id) { set(KEY.orders, get(KEY.orders).filter(x => x.id !== id)); return {}; },
    async getReportsSalaryExcel(params) {
      const monthly = (await this.getSalarySummary(params)).monthly || [];
      const lines = ['员工\t月份\t数量\t金额'];
      for (const r of monthly) lines.push([r.employee_name, r.month, r.total_qty, (r.total_amount || 0).toFixed(2)].join('\t'));
      const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' });
      return { data: blob };
    },
    async postAuthCreateUser() { return {}; }
  };
})();
