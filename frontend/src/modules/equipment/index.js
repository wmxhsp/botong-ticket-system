import routes from './routes'
import * as api from './api'

export default {
  name: 'equipment',
  routes,
  api,

  nav: {
    title: '设备管理',
    icon: 'bi-pc-display',
    path: '/equipment',
    order: 30,
    group: '业务',
    routeName: 'EquipmentList',
    children: ['EquipmentDetail'],
  },

  features: [
    { name: 'list', endpoint: 'GET /equipment', status: 'done' },
    { name: 'getById', endpoint: 'GET /equipment/:id', status: 'done' },
    { name: 'create', endpoint: 'POST /equipment', status: 'done' },
    { name: 'update', endpoint: 'PUT /equipment/:id', status: 'done' },
    { name: 'delete', endpoint: 'DELETE /equipment/:id', status: 'done' },
    { name: 'restore', endpoint: 'POST /equipment/:id/restore', status: 'done' },
    { name: 'batchDelete', endpoint: 'POST /equipment/batch/delete', status: 'done' },
    { name: 'batchRestore', endpoint: 'POST /equipment/batch/restore', status: 'done' },
    { name: 'batchQrUrls', endpoint: 'POST /equipment/batch/qr-urls', status: 'done' },
    { name: 'getPhotos', endpoint: 'GET /equipment/:id/photos', status: 'done' },
    { name: 'uploadPhoto', endpoint: 'POST /equipment/:id/photos', status: 'done' },
    { name: 'batchUploadPhotos', endpoint: 'POST /equipment/:id/photos/batch', status: 'done' },
    { name: 'deletePhoto', endpoint: 'DELETE /equipment/:id/photos', status: 'done' },
    { name: 'updatePhotoSettings', endpoint: 'PUT /equipment/:id/photos/settings', status: 'done' },
    { name: 'getTickets', endpoint: 'GET /equipment/:id/tickets', status: 'done' },
    { name: 'getMaintenanceSummary', endpoint: 'GET /equipment/maintenance/summary', status: 'done' },
    { name: 'getMaintenanceOverdue', endpoint: 'GET /equipment/maintenance/overdue', status: 'done' },
    { name: 'recordMaintenance', endpoint: 'POST /equipment/:id/maintenance/record', status: 'done' },
    { name: 'getMaintenanceHistory', endpoint: 'GET /equipment/:id/maintenance/history', status: 'done' },
    { name: 'getComponents', endpoint: 'GET /equipment/:id/components', status: 'done' },
    { name: 'addComponent', endpoint: 'POST /equipment/:id/components', status: 'done' },
    { name: 'updateComponent', endpoint: 'PUT /equipment/:id/components/:compId', status: 'done' },
    { name: 'deleteComponent', endpoint: 'DELETE /equipment/:id/components/:compId', status: 'done' },
    { name: 'getTimeline', endpoint: 'GET /equipment/:id/timeline', status: 'done' },
    { name: 'getQrCode', endpoint: 'GET /equipment/:id/qrcode', status: 'done' },
  ]
}
