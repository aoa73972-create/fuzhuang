// 计件系统 - 操作简单 · 呈现简洁
const API = (window.API_BASE || '') + '/api';
const axios = window.axios;
if (!axios) throw new Error('axios 未加载，请检查网络连接');

axios.defaults.baseURL = '';
axios.interceptors.request.use(cfg => {
  const t = localStorage.getItem('token');
  if (t) cfg.headers.Authorization = 'Bearer ' + t;
  return cfg;
});
axios.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.reload();
  }
  return Promise.reject(err);
});

const { createApp } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;
const ElMessage = ElementPlus.ElMessage;

function formatDateZh(d) {
  if (!d) return '';
  const p = String(d).split('-');
  if (p.length >= 3) return p[0] + '年' + parseInt(p[1], 10) + '月' + parseInt(p[2], 10) + '日';
  if (p.length === 2) return p[0] + '年' + parseInt(p[1], 10) + '月';
  return d;
}
function formatMonthZh(m) {
  if (!m) return '';
  const p = String(m).split('-');
  return p.length >= 2 ? p[0] + '年' + parseInt(p[1], 10) + '月' : m;
}

// 首页
const Home = {
  template: `
    <div class="card">
      <div class="card-title">概览</div>
      <el-row :gutter="20">
        <el-col :span="8"><div class="stat-card stat-blue"><div class="stat-num">{{ stats.total || '0' }}</div><div class="stat-label">本月金额</div></div></el-col>
        <el-col :span="8"><div class="stat-card stat-green"><div class="stat-num">{{ stats.count || '0' }}</div><div class="stat-label">计件笔数</div></div></el-col>
        <el-col :span="8"><div class="stat-card stat-amber"><div class="stat-num">{{ stats.emp || '0' }}</div><div class="stat-label">参与人数</div></div></el-col>
      </el-row>
      <div class="home-actions">
        <el-button type="primary" size="large" v-if="isAdmin" @click="$router.push('/entry')">计件录入</el-button>
        <el-button size="large" @click="$router.push('/query')">数据查询</el-button>
      </div>
    </div>
  `,
  data: () => ({ stats: {} }),
  computed: { isAdmin() { return this.$root.user?.role === 'admin'; } },
  mounted() {
    const m = new Date().toISOString().slice(0, 7);
    axios.get(API + '/piece-records', { params: { month: m } }).then(r => {
      const d = r.data?.data || [];
      this.stats = { total: d.reduce((s,x) => s + (x.amount||0), 0).toFixed(2), count: d.length, emp: new Set(d.map(x=>x.employee_id)).size };
    }).catch(() => { this.stats = { total: '0', count: '0', emp: '0' }; });
  }
};

// 计件录入 - 员工固定、偶尔新增，主流程：款式 → 数量
const Entry = {
  template: `
    <div class="card">
      <div class="step-bar">
        <span :class="{active:step===0}">1. 款式</span>
        <span :class="{active:step===1}">2. 数量</span>
      </div>
      <!-- 步骤1：款式 -->
      <div v-show="step===0">
        <el-form :model="f" label-width="80" inline size="default">
          <el-form-item label="款式"><el-select v-model="f.style_code" filterable allow-create placeholder="款式" style="width:160px" @change="onStyle">
            <el-option v-for="r in pieceRates" :key="r.id" :label="r.style_code + (r.size?' '+r.size:'') + ' ¥'+r.unit_price" :value="r.style_code" />
          </el-select></el-form-item>
          <el-form-item label="尺码"><el-select v-model="f.size" clearable placeholder="尺码" style="width:120px" @change="onStyle">
            <el-option v-for="s in sizes" :key="s" :label="s" :value="s" />
          </el-select></el-form-item>
          <el-form-item label="单价"><el-input-number v-model="f.unit_price" :min="0" :precision="2" style="width:120px" controls-position="right" /></el-form-item>
          <el-form-item label="日期"><el-date-picker v-model="f.record_date" type="date" value-format="YYYY-MM-DD" format="YYYY年M月D日" style="width:180px" /></el-form-item>
        </el-form>
        <el-button type="primary" size="large" @click="step=1">下一步</el-button>
      </div>
      <!-- 步骤2：数量（员工名单固定，偶尔新增） -->
      <div v-show="step===1">
        <p class="entry-summary">{{ f.style_code }} {{ f.size || '' }} · ¥{{ f.unit_price }} · {{ formatDateZh(f.record_date) }}</p>
        <div class="entry-toolbar">
          <span class="entry-toolbar-label">名单 {{ employees.length }} 人</span>
          <el-input v-model="newName" placeholder="新增员工姓名" style="width:140px" @keyup.enter="addOne" />
          <el-button @click="addOne">添加</el-button>
          <el-button link type="primary" @click="$router.push('/settings')">批量维护名单</el-button>
        </div>
        <el-table :data="qtyRows" max-height="360">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column label="数量" width="140">
            <template #default="{row}"><el-input-number v-model="row.quantity" :min="0" style="width:110px" controls-position="right" /></template>
          </el-table-column>
        </el-table>
        <p v-if="!employees.length" class="entry-empty">暂无员工，请先在设置中添加</p>
        <div class="entry-actions">
          <el-button size="large" @click="step=0">上一步</el-button>
          <el-button type="primary" size="large" @click="submit" :disabled="!employees.length">提交</el-button>
        </div>
      </div>
    </div>
  `,
  data() {
    const today = new Date().toISOString().slice(0, 10);
    return {
      step: 0, newName: '',
      f: { style_code: '', size: '', unit_price: 0, record_date: today },
      employees: [], pieceRates: [], qtyRows: [],
      sizes: ['S','M','L','XL','XXL','XXXL']
    };
  },
  watch: {
    employees: {
      handler(emps) {
        this.qtyRows = emps.map(e => {
          const old = this.qtyRows.find(r => r.employee_id === e.id);
          return old ? { ...old, name: e.name } : { employee_id: e.id, name: e.name, quantity: 0 };
        });
      },
      immediate: true
    },
    step(n) { if (n === 0) this.qtyRows = this.employees.map(e => ({ employee_id: e.id, name: e.name, quantity: 0 })); }
  },
  mounted() {
    axios.get(API + '/employees').then(r => { this.employees = r.data?.data || []; });
    axios.get(API + '/piece-rates').then(r => { this.pieceRates = r.data?.data || []; });
  },
  methods: {
    formatDateZh,
    onStyle() {
      const r = this.pieceRates.find(x => x.style_code === this.f.style_code && (x.size||'') === (this.f.size||''));
      if (r) this.f.unit_price = r.unit_price;
    },
    addOne() {
      if (!this.newName.trim()) { ElMessage.warning('请输入姓名'); return; }
      axios.post(API + '/employees', { name: this.newName.trim() }).then(() => {
        ElMessage.success('已添加');
        this.newName = '';
        axios.get(API + '/employees').then(r => { this.employees = r.data?.data || []; });
      });
    },
    submit() {
      if (!this.f.style_code || !this.f.record_date) { ElMessage.warning('请填写款式和日期'); return; }
      const rows = this.qtyRows.filter(r => r.quantity > 0);
      const invalid = rows.filter(r => !r.employee_id);
      if (invalid.length) { ElMessage.warning('以下员工数据异常，请刷新页面后重试：' + invalid.map(r => r.name).join('、')); return; }
      const items = rows.map(r => ({ employee_id: r.employee_id, quantity: r.quantity }));
      if (!items.length) { ElMessage.warning('请至少录入一条数量'); return; }
      const names = rows.map(r => r.name);
      axios.post(API + '/piece-records/by-style', { ...this.f, size: this.f.size || null, items }).then(r => {
        const d = r.data || {};
        const saved = d.saved || 0;
        const errs = d.errors || [];
        if (errs.length > 0) {
          const msgs = errs.map(e => `第${e.index + 1}条${names[e.index] || ''}: ${e.msg}`).join('；');
          ElMessage.warning({ message: `成功录入 ${saved} 条，${errs.length} 条失败：${msgs}`, duration: 5000 });
        } else {
          ElMessage.success('成功录入 ' + saved + ' 条');
        }
        this.$router.push('/query');
      }).catch(e => { ElMessage.error(e.response?.data?.msg || '录入失败'); });
    }
  }
};

// 数据查询 - 合并计件/薪资/报表/统计
const Query = {
  template: `
    <div class="card">
      <div class="card-title">数据查询</div>
      <el-tabs v-model="tab">
        <el-tab-pane label="计件明细" name="list">
          <el-form inline>
            <el-form-item><el-radio-group v-model="dateMode"><el-radio-button value="day">按日</el-radio-button><el-radio-button value="month">按月</el-radio-button><el-radio-button value="range">日期范围</el-radio-button></el-radio-group></el-form-item>
            <el-form-item v-if="dateMode==='month'"><el-date-picker v-model="month" type="month" value-format="YYYY-MM" format="YYYY年M月" @change="loadList" /></el-form-item>
            <el-form-item v-if="dateMode==='day'">
              <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" format="YYYY年M月D日"
                :shortcuts="dateShortcuts" placeholder="选择日期" @change="loadList" :editable="false" />
            </el-form-item>
            <template v-if="dateMode==='range'">
              <el-form-item label="起"><el-date-picker v-model="startDate" type="date" value-format="YYYY-MM-DD" format="YYYY年M月D日" @change="loadList" /></el-form-item>
              <el-form-item label="止"><el-date-picker v-model="endDate" type="date" value-format="YYYY-MM-DD" format="YYYY年M月D日" @change="loadList" /></el-form-item>
            </template>
            <el-form-item><el-select v-model="size" placeholder="尺码" clearable style="width:110px"><el-option v-for="s in sizes" :key="s" :label="s" :value="s" /></el-select></el-form-item>
            <el-form-item v-if="isAdmin"><el-select v-model="empId" placeholder="全部员工" clearable style="width:120px"><el-option v-for="e in employees" :key="e.id" :label="e.name" :value="e.id" /></el-select></el-form-item>
            <el-form-item><el-button type="primary" @click="loadList">查询</el-button></el-form-item>
            <el-form-item v-if="isAdmin"><el-button type="danger" @click="clearAll">清空</el-button></el-form-item>
          </el-form>
          <div v-if="(size || empId) && tab==='list'" style="margin-bottom:12px;font-size:14px;color:#ff9500">提示：已筛选 尺码{{ size ? '='+size : '' }}{{ empId ? ' 员工' : '' }}，可能只显示部分数据，清空筛选可查看全部</div>
          <div v-if="dateMode==='day' && date" class="query-day-summary">
            <strong>{{ formatDateZh(date) }}</strong>：共 <strong>{{ daySummary.count }}</strong> 条，金额合计 <strong>¥{{ daySummary.amount }}</strong>
          </div>
          <div v-if="(dateMode==='month'||dateMode==='range') && dailySummary.length" class="query-daily-wrap">
            <div class="card-title">每日汇总</div>
            <el-table :data="dailySummary" max-height="220">
              <el-table-column label="日期" width="150"><template #default="{row}">{{ formatDateZh(row.date) }}</template></el-table-column>
              <el-table-column prop="count" label="条数" width="90" />
              <el-table-column prop="amount" label="金额" width="110" />
            </el-table>
          </div>
          <el-table :data="records" stripe>
            <el-table-column label="日期" width="140"><template #default="{row}">{{ formatDateZh(row.record_date) }}</template></el-table-column>
            <el-table-column prop="employee_name" label="员工" width="100" />
            <el-table-column prop="style_code" label="款式" width="120" />
            <el-table-column prop="size" label="尺码" width="80" />
            <el-table-column prop="quantity" label="数量" width="90" />
            <el-table-column prop="unit_price" label="单价" width="90" />
            <el-table-column prop="amount" label="金额" width="100" />
            <el-table-column v-if="isAdmin" label="操作" width="100" fixed="right">
              <template #default="{row}"><el-button link type="primary" @click="editRecord(row)">编辑</el-button></template>
            </el-table-column>
          </el-table>
          <el-dialog v-model="editD.visible" title="修改计件记录" width="420" @close="editD.visible=false">
            <el-form :model="editD.form" label-width="80" v-if="editD.form">
              <el-form-item label="员工"><el-input v-model="editD.form.employee_name" disabled /></el-form-item>
              <el-form-item label="款式"><el-input v-model="editD.form.style_code" disabled /></el-form-item>
              <el-form-item label="尺码"><el-select v-model="editD.form.size" clearable filterable allow-create placeholder="尺码" style="width:100%"><el-option v-for="s in sizes" :key="s" :label="s" :value="s" /></el-select></el-form-item>
              <el-form-item label="数量"><el-input-number v-model="editD.form.quantity" :min="1" style="width:100%" /></el-form-item>
              <el-form-item label="单价"><el-input-number v-model="editD.form.unit_price" :min="0" :precision="2" style="width:100%" /></el-form-item>
              <el-form-item label="金额"><span>{{ (editD.form.quantity * (editD.form.unit_price||0)).toFixed(2) }}</span></el-form-item>
            </el-form>
            <template #footer><el-button @click="editD.visible=false">取消</el-button><el-button type="primary" @click="saveRecord" :loading="editD.loading">保存</el-button></template>
          </el-dialog>
        </el-tab-pane>
        <el-tab-pane label="薪资汇总" name="salary">
          <div class="salary-header">
            <el-form inline>
              <el-form-item label="月份"><el-date-picker v-model="month" type="month" value-format="YYYY-MM" format="YYYY年M月" @change="loadSalary" /></el-form-item>
              <el-form-item v-if="isAdmin" label="员工"><el-select v-model="empId" placeholder="全部员工" clearable style="width:140px" @change="loadSalary"><el-option v-for="e in employees" :key="e.id" :label="e.name" :value="e.id" /></el-select></el-form-item>
              <el-form-item><el-button type="primary" @click="loadSalary">查询</el-button></el-form-item>
            </el-form>
            <div v-if="monthly.length" class="salary-summary-bar">
              <span class="salary-summary-label">{{ formatMonthZh(month) }} 汇总</span>
              <span class="salary-summary-total">合计 <strong>¥{{ salaryTotal }}</strong></span>
            </div>
          </div>
          <div class="salary-table-wrap">
            <el-table :data="monthly" class="salary-table" stripe>
              <el-table-column prop="employee_name" label="员工" min-width="120" />
              <el-table-column label="月份" width="130" align="center"><template #default="{row}">{{ formatMonthZh(row.month) }}</template></el-table-column>
              <el-table-column prop="total_qty" label="数量" width="100" align="right" />
              <el-table-column prop="total_amount" label="金额（元）" width="120" align="right">
                <template #default="{row}">¥{{ parseFloat(row.total_amount||0).toFixed(2) }}</template>
              </el-table-column>
            </el-table>
            <div v-if="monthly.length && !empId" class="salary-total-row">
              <span class="salary-total-label">合计</span>
              <span class="salary-total-qty">{{ salaryTotalQty }}</span>
              <span class="salary-total-amount">¥{{ salaryTotal }}</span>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="导出报表" name="report">
          <el-form inline>
            <el-form-item><el-date-picker v-model="month" type="month" value-format="YYYY-MM" format="YYYY年M月" /></el-form-item>
            <el-form-item v-if="isAdmin"><el-select v-model="empId" placeholder="员工" clearable style="width:120px"><el-option v-for="e in employees" :key="e.id" :label="e.name" :value="e.id" /></el-select></el-form-item>
            <el-form-item><el-button type="primary" @click="exportExcel">导出 Excel</el-button></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="数据统计" name="stats">
          <el-form inline>
            <el-form-item><el-date-picker v-model="month" type="month" value-format="YYYY-MM" format="YYYY年M月" /></el-form-item>
            <el-form-item><el-button type="primary" @click="loadStats">查询</el-button></el-form-item>
          </el-form>
          <el-row :gutter="16">
            <el-col :span="12"><div class="card-title">工序占比</div><el-table :data="processShare"><el-table-column prop="label" /><el-table-column prop="qty" label="数量" width="90" /><el-table-column prop="value" label="金额" width="100" /><el-table-column prop="percent" width="80"><template #default="{row}">{{ row.percent }}%</template></el-table-column></el-table></el-col>
            <el-col :span="12"><div class="card-title">产能排行</div><el-table :data="ranking"><el-table-column prop="rank" width="60" /><el-table-column prop="name" /><el-table-column prop="total_qty" label="数量" width="90" /><el-table-column prop="total_amount" label="金额" width="100" /></el-table></el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </div>
  `,
  data() {
    const m = new Date().toISOString().slice(0, 7);
    const d = new Date().toISOString().slice(0, 10);
    const d1 = m + '-01';  // 当月1号
    return {
      tab: 'list',
      dateMode: 'day', month: m, date: d, startDate: d1, endDate: d, size: null, empId: null,
      records: [], monthly: [], processShare: [], ranking: [],
      employees: [],
      dateShortcuts: [
        { text: '今天', value: () => new Date() },
        { text: '昨天', value: () => { const x = new Date(); x.setDate(x.getDate() - 1); return x; } },
        { text: '前天', value: () => { const x = new Date(); x.setDate(x.getDate() - 2); return x; } }
      ],
      editD: { visible: false, loading: false, form: null }
    };
  },
  computed: {
    isAdmin() { return this.$root.user?.role === 'admin'; },
    sizes() { return ['S','M','L','XL','XXL','XXXL']; },
    daySummary() {
      const total = this.records.reduce((s, r) => s + (r.amount || 0), 0);
      return { count: this.records.length, amount: total.toFixed(2) };
    },
    dailySummary() {
      const map = {};
      this.records.forEach(r => {
        const d = r.record_date;
        if (!map[d]) map[d] = { date: d, count: 0, amount: 0 };
        map[d].count++;
        map[d].amount += r.amount || 0;
      });
      return Object.values(map).sort((a,b) => b.date.localeCompare(a.date)).map(x => ({ ...x, amount: x.amount.toFixed(2) }));
    },
    salaryTotal() {
      const sum = this.monthly.reduce((s, r) => s + parseFloat(r.total_amount || 0), 0);
      return sum.toFixed(2);
    },
    salaryTotalQty() {
      return this.monthly.reduce((s, r) => s + parseInt(r.total_qty || 0, 10), 0);
    }
  },
  watch: {
    dateMode() { this.loadList(); },
    tab(n) { if (n === 'salary') this.loadSalary(); }
  },
  mounted() {
    this.loadList();
    if (this.$root.user?.role === 'admin') axios.get(API + '/employees').then(r => { this.employees = r.data?.data || []; });
  },
  methods: {
    formatDateZh, formatMonthZh,
    loadList() {
      let p = {};
      if (this.dateMode === 'month') p.month = this.month;
      else if (this.dateMode === 'day') p.record_date = this.date;
      else if (this.dateMode === 'range') { p.start_date = this.startDate; p.end_date = this.endDate; }
      if (this.size) p.size = this.size;
      if (this.empId) p.employee_id = this.empId;
      axios.get(API + '/piece-records', { params: p }).then(r => { this.records = r.data?.data || []; });
    },
    loadSalary() {
      const p = { month: this.month };
      if (this.empId) p.employee_id = this.empId;
      axios.get(API + '/salary/summary', { params: p }).then(r => { this.monthly = r.data?.monthly || []; });
    },
    loadStats() {
      const p = { month: this.month };
      if (this.empId) p.employee_id = this.empId;
      Promise.all([axios.get(API + '/stats/process-share', { params: p }), axios.get(API + '/stats/employee-ranking', { params: p })]).then(([a,b]) => {
        this.processShare = a.data?.data || [];
        this.ranking = (b.data?.data || []).map((x,i) => ({ ...x, rank: i+1 }));
      });
    },
    exportExcel() {
      const p = { month: this.month };
      if (this.empId) p.employee_id = this.empId;
      axios.get(API + '/reports/salary-excel', { params: p, responseType: 'blob' }).then(r => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([r.data]));
        a.download = '薪资_' + this.month + '.xlsx';
        a.click();
        ElMessage.success('已导出');
      });
    },
    clearAll() {
      ElementPlus.ElMessageBox.confirm('确定清空所有计件数据？', '确认', { type: 'warning' }).then(() => {
        axios.post(API + '/piece-records/clear-all').then(r => { ElMessage.success('已清空'); this.loadList(); });
      }).catch(() => {});
    },
    editRecord(row) {
      this.editD.form = { id: row.id, employee_name: row.employee_name, style_code: row.style_code, size: row.size || '', quantity: row.quantity, unit_price: row.unit_price };
      this.editD.visible = true;
      this.editD.loading = false;
    },
    saveRecord() {
      const f = this.editD.form;
      if (!f || f.quantity < 1) { ElMessage.warning('数量至少为1'); return; }
      if (f.unit_price < 0) { ElMessage.warning('单价不能为负'); return; }
      this.editD.loading = true;
      axios.put(API + '/piece-records/' + f.id, { size: f.size || null, quantity: f.quantity, unit_price: f.unit_price }).then(() => {
        ElMessage.success('已保存');
        this.editD.visible = false;
        this.loadList();
      }).catch(e => { ElMessage.error(e.response?.data?.msg || '保存失败'); }).finally(() => { this.editD.loading = false; });
    }
  }
};

// 设置
const Settings = {
  template: `
    <div class="card">
      <div class="card-title">系统设置</div>
      <el-tabs>
        <el-tab-pane label="员工">
          <div class="settings-toolbar">
            <el-button type="primary" @click="showEmp()">新增</el-button>
            <el-input v-model="batchNames" type="textarea" :rows="2" placeholder="批量录入：每行一个姓名" style="width:240px" />
            <el-button @click="batchAdd">批量添加</el-button>
          </div>
          <el-table :data="employees"><el-table-column prop="name" label="姓名" width="120" /><el-table-column prop="employee_no" label="工号" width="120" /><el-table-column label="操作" width="180"><template #default="{row}"><el-button link @click="showEmp(row)">编辑</el-button><el-button link type="danger" @click="delEmp(row)">删除</el-button><el-button link @click="showUser(row)">账号</el-button></template></el-table-column></el-table>
        </el-tab-pane>
        <el-tab-pane label="单价">
          <el-button @click="showRate()" style="margin-bottom:16px">新增</el-button>
          <el-table :data="pieceRates"><el-table-column prop="style_code" label="款式" width="140" /><el-table-column prop="size" label="尺码" width="80" /><el-table-column prop="unit_price" label="单价" width="100" /><el-table-column label="操作" width="140"><template #default="{row}"><el-button link @click="showRate(row)">编辑</el-button><el-button link type="danger" @click="delRate(row)">删除</el-button></template></el-table-column></el-table>
        </el-tab-pane>
        <el-tab-pane label="工单">
          <el-button @click="showOrder()" style="margin-bottom:16px">新增</el-button>
          <el-table :data="workOrders"><el-table-column prop="order_no" label="工单号" width="120" /><el-table-column prop="style_code" label="款式" width="120" /><el-table-column prop="delivery_date" label="交货期" width="130" /><el-table-column label="操作" width="140"><template #default="{row}"><el-button link @click="showOrder(row)">编辑</el-button><el-button link type="danger" @click="delOrder(row)">删除</el-button></template></el-table-column></el-table>
        </el-tab-pane>
      </el-tabs>
      <el-dialog v-model="empD.visible" :title="empD.id?'编辑':'新增'" width="400"><el-form :model="empD.form" label-width="80"><el-form-item label="姓名"><el-input v-model="empD.form.name" /></el-form-item><el-form-item label="工号"><el-input v-model="empD.form.employee_no" /></el-form-item></el-form><template #footer><el-button @click="empD.visible=false">取消</el-button><el-button type="primary" @click="saveEmp">保存</el-button></template></el-dialog>
      <el-dialog v-model="rateD.visible" :title="rateD.id?'编辑':'新增'" width="400"><el-form :model="rateD.form" label-width="80"><el-form-item label="款式"><el-input v-model="rateD.form.style_code" /></el-form-item><el-form-item label="尺码"><el-input v-model="rateD.form.size" placeholder="可留空" /></el-form-item><el-form-item label="单价"><el-input-number v-model="rateD.form.unit_price" :min="0" :precision="2" /></el-form-item></el-form><template #footer><el-button @click="rateD.visible=false">取消</el-button><el-button type="primary" @click="saveRate">保存</el-button></template></el-dialog>
      <el-dialog v-model="orderD.visible" :title="orderD.id?'编辑':'新增'" width="400"><el-form :model="orderD.form" label-width="80"><el-form-item label="工单号"><el-input v-model="orderD.form.order_no" /></el-form-item><el-form-item label="款式"><el-input v-model="orderD.form.style_code" /></el-form-item><el-form-item label="交货期"><el-date-picker v-model="orderD.form.delivery_date" type="date" value-format="YYYY-MM-DD" format="YYYY年M月D日" style="width:100%" /></el-form-item></el-form><template #footer><el-button @click="orderD.visible=false">取消</el-button><el-button type="primary" @click="saveOrder">保存</el-button></template></el-dialog>
      <el-dialog v-model="userD.visible" title="创建账号" width="400"><el-form :model="userD.form" label-width="80"><el-form-item label="用户名"><el-input v-model="userD.form.username" /></el-form-item><el-form-item label="密码"><el-input v-model="userD.form.password" type="password" /></el-form-item></el-form><template #footer><el-button @click="userD.visible=false">取消</el-button><el-button type="primary" @click="saveUser">创建</el-button></template></el-dialog>
    </div>
  `,
  data: () => ({
    employees: [], pieceRates: [], workOrders: [], batchNames: '',
    empD: { visible: false, id: null, form: {} },
    rateD: { visible: false, id: null, form: {} },
    orderD: { visible: false, id: null, form: {} },
    userD: { visible: false, empId: null, form: {} }
  }),
  mounted() { this.load(); },
  methods: {
    load() {
      Promise.all([axios.get(API + '/employees'), axios.get(API + '/piece-rates'), axios.get(API + '/work-orders')]).then(([a,b,c]) => {
        this.employees = a.data?.data || [];
        this.pieceRates = b.data?.data || [];
        this.workOrders = c.data?.data || [];
      });
    },
    showEmp(row) { this.empD.id = row?.id; this.empD.form = row ? { ...row } : { name: '', employee_no: '' }; this.empD.visible = true; },
    batchAdd() {
      if (!this.batchNames.trim()) { ElMessage.warning('请输入姓名'); return; }
      const names = this.batchNames.split(/[\n,，\s]+/).map(n=>n.trim()).filter(Boolean);
      axios.post(API + '/employees/batch', { names: names.join('\n') }).then(r => { ElMessage.success('添加 ' + r.data.added + ' 人'); this.batchNames = ''; this.load(); });
    },
    saveEmp() { (this.empD.id ? axios.put(API + '/employees/' + this.empD.id, this.empD.form) : axios.post(API + '/employees', this.empD.form)).then(() => { ElMessage.success('已保存'); this.empD.visible = false; this.load(); }); },
    delEmp(row) { ElementPlus.ElMessageBox.confirm('确定删除？').then(() => axios.delete(API + '/employees/' + row.id).then(() => { ElMessage.success('已删除'); this.load(); })).catch(() => {}); },
    showRate(row) { this.rateD.id = row?.id; this.rateD.form = row ? { ...row } : { style_code: '', size: '', unit_price: 0 }; this.rateD.visible = true; },
    saveRate() { (this.rateD.id ? axios.put(API + '/piece-rates/' + this.rateD.id, this.rateD.form) : axios.post(API + '/piece-rates', this.rateD.form)).then(() => { ElMessage.success('已保存'); this.rateD.visible = false; this.load(); }); },
    delRate(row) { ElementPlus.ElMessageBox.confirm('确定删除？').then(() => axios.delete(API + '/piece-rates/' + row.id).then(() => { ElMessage.success('已删除'); this.load(); })).catch(() => {}); },
    showOrder(row) { this.orderD.id = row?.id; this.orderD.form = row ? { ...row } : { order_no: '', style_code: '', quantity: 0, delivery_date: '' }; this.orderD.visible = true; },
    saveOrder() { (this.orderD.id ? axios.put(API + '/work-orders/' + this.orderD.id, this.orderD.form) : axios.post(API + '/work-orders', this.orderD.form)).then(() => { ElMessage.success('已保存'); this.orderD.visible = false; this.load(); }); },
    delOrder(row) { ElementPlus.ElMessageBox.confirm('确定删除？').then(() => axios.delete(API + '/work-orders/' + row.id).then(() => { ElMessage.success('已删除'); this.load(); })).catch(() => {}); },
    showUser(row) { this.userD.empId = row.id; this.userD.form = { username: row.employee_no || row.name, password: '' }; this.userD.visible = true; },
    saveUser() { axios.post(API + '/auth/create-user', { employee_id: this.userD.empId, ...this.userD.form }).then(() => { ElMessage.success('已创建'); this.userD.visible = false; }); }
  }
};

const routes = [
  { path: '/', component: Home },
  { path: '/entry', component: Entry },
  { path: '/query', component: Query },
  { path: '/settings', component: Settings }
];

const router = createRouter({ history: createWebHashHistory(), routes });

const app = createApp({
  data: () => ({
    token: localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    loginForm: { username: '', password: '', loading: false }
  }),
  computed: { isAdmin() { return this.user?.role === 'admin'; } },
  methods: {
    async doLogin() {
      if (!this.loginForm.username || !this.loginForm.password) { ElMessage.warning('请输入用户名和密码'); return; }
      this.loginForm.loading = true;
      try {
        const r = await axios.post(API + '/auth/login', this.loginForm);
        if (r.data?.ok) {
          localStorage.setItem('token', r.data.token);
          localStorage.setItem('user', JSON.stringify(r.data.user));
          this.token = r.data.token;
          this.user = r.data.user;
          router.push('/');
        } else ElMessage.error(r.data?.msg || '登录失败');
      } catch (e) { ElMessage.error(e.response?.data?.msg || '登录失败'); }
      finally { this.loginForm.loading = false; }
    },
    logout() { localStorage.removeItem('token'); localStorage.removeItem('user'); this.token = null; this.user = null; location.reload(); }
  }
});

app.use(router);
app.use(ElementPlus, { locale: window.ElementPlusLocaleZhCn || {} });
app.mount('#app');
