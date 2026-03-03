/**
 * API 适配器：API_BASE === 'local' 时走 localStorage，否则走 axios
 */
(function() {
  const API = (window.API_BASE || '') + '/api';
  const isLocal = window.API_BASE === 'local';
  const LS = window.LocalStorageAPI;
  const axios = window.axios;

  function toParams(config) {
    if (!config || !config.params) return {};
    return config.params;
  }

  async function localGet(path, config) {
    const p = toParams(config);
    let data;
    if (path.includes('employees') && !path.includes('batch')) data = await LS.getEmployees();
    else if (path.includes('piece-rates')) data = await LS.getPieceRates();
    else if (path.includes('piece-records') && !path.includes('by-style') && !path.includes('clear')) data = await LS.getPieceRecords(p);
    else if (path.includes('salary/summary')) data = await LS.getSalarySummary(p);
    else if (path.includes('stats/process-share')) data = await LS.getStatsProcessShare(p);
    else if (path.includes('stats/employee-ranking')) data = await LS.getStatsEmployeeRanking(p);
    else if (path.includes('work-orders')) data = await LS.getWorkOrders();
    else if (path.includes('reports/salary-excel')) data = await LS.getReportsSalaryExcel(p);
    else data = {};
    return (path.includes('reports/') && data.data) ? { data: data.data } : { data };
  }

  async function localPost(path, body) {
    let data;
    if (path.includes('auth/login')) data = await LS.login(body);
    else if (path.includes('employees/batch')) data = await LS.postEmployeesBatch(body);
    else if (path.includes('employees')) data = await LS.postEmployee(body);
    else if (path.includes('piece-rates')) data = await LS.postPieceRate(body);
    else if (path.includes('piece-records/by-style')) data = await LS.postPieceRecordsByStyle(body);
    else if (path.includes('piece-records/clear')) data = await LS.postPieceRecordsClearAll();
    else if (path.includes('work-orders')) data = await LS.postWorkOrder(body);
    else if (path.includes('auth/create-user')) data = await LS.postAuthCreateUser();
    else data = {};
    return { data };
  }

  async function localPut(path, body) {
    const id = (path.match(/(\d+)$/) || [])[1];
    if (path.includes('employees')) await LS.putEmployee(parseInt(id, 10), body);
    else if (path.includes('piece-rates')) await LS.putPieceRate(parseInt(id, 10), body);
    else if (path.includes('piece-records')) await LS.putPieceRecord(parseInt(id, 10), body);
    else if (path.includes('work-orders')) await LS.putWorkOrder(parseInt(id, 10), body);
    return { data: {} };
  }

  async function localDelete(path) {
    const id = (path.match(/(\d+)$/) || [])[1];
    if (path.includes('employees')) await LS.deleteEmployee(parseInt(id, 10));
    else if (path.includes('piece-rates')) await LS.deletePieceRate(parseInt(id, 10));
    else if (path.includes('work-orders')) await LS.deleteWorkOrder(parseInt(id, 10));
    return { data: {} };
  }

  window.apiRequest = {
    get(url, config) {
      const path = url.replace(API, '').replace(/^\//, '');
      if (isLocal) return localGet(path, config);
      return axios.get(url, config);
    },
    post(url, body) {
      const path = url.replace(API, '').replace(/^\//, '');
      if (isLocal) return localPost(path, body);
      return axios.post(url, body);
    },
    put(url, body) {
      const path = url.replace(API, '').replace(/^\//, '');
      if (isLocal) return localPut(path, body);
      return axios.put(url, body);
    },
    delete(url) {
      const path = url.replace(API, '').replace(/^\//, '');
      if (isLocal) return localDelete(path);
      return axios.delete(url);
    }
  };
})();
