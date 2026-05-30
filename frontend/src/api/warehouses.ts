import client from './client'

export const warehouseApi = {
  list(params: Record<string, any> = {}): Promise<any> {
    return client.get('/stock/warehouses', { params })
  },
  create(data: Record<string, any>): Promise<any> {
    return client.post('/stock/warehouses', data)
  },
  update(id: number | string, data: Record<string, any>): Promise<any> {
    return client.put(`/stock/warehouses/${id}`, data)
  },
  delete(id: number | string): Promise<any> {
    return client.delete(`/stock/warehouses/${id}`)
  },
}
