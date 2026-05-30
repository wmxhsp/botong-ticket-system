import { ref, computed } from 'vue'
import { useToast } from '@/composables/useToast'

/**
 * 批量操作 Composable
 * 
 * 提供列表多选和批量操作功能
 * 适用于工单、客户等列表的批量处理
 * 
 * @example
 * ```ts
 * const { selectedIds, toggleSelection, batchDelete } = useBatchOperations()
 * 
 * // 切换选择
 * toggleSelection(itemId)
 * 
 * // 批量删除
 * await batchDelete(async (ids) => {
 *   await api.deleteBatch(ids)
 * })
 * ```
 */

export function useBatchOperations<T extends { id: number | string }>() {
  const { show: showToast } = useToast()
  
  const selectedIds = ref<Set<number | string>>(new Set())
  const isSelectAll = ref(false)
  
  /**
   * 选中的数量
   */
  const selectedCount = computed(() => selectedIds.value.size)
  
  /**
   * 是否有选中项
   */
  const hasSelection = computed(() => selectedIds.value.size > 0)
  
  /**
   * 切换单个项目的选择状态
   */
  function toggleSelection(id: number | string) {
    if (selectedIds.value.has(id)) {
      selectedIds.value.delete(id)
    } else {
      selectedIds.value.add(id)
    }
    
    // 更新全选状态
    updateSelectAllState()
  }
  
  /**
   * 选择所有项目
   */
  function selectAll(items: T[]) {
    items.forEach(item => {
      selectedIds.value.add(item.id)
    })
    isSelectAll.value = true
  }
  
  /**
   * 取消选择所有项目
   */
  function deselectAll() {
    selectedIds.value.clear()
    isSelectAll.value = false
  }
  
  /**
   * 切换全选状态
   */
  function toggleSelectAll(items: T[]) {
    if (isSelectAll.value) {
      deselectAll()
    } else {
      selectAll(items)
    }
  }
  
  /**
   * 更新全选状态
   */
  function updateSelectAllState() {
    // 这个函数需要在外部调用时传入总项目数来判断
    // 这里只做简单的状态重置
    if (selectedIds.value.size === 0) {
      isSelectAll.value = false
    }
  }
  
  /**
   * 检查项目是否被选中
   */
  function isSelected(id: number | string): boolean {
    return selectedIds.value.has(id)
  }
  
  /**
   * 批量删除
   */
  async function batchDelete(
    deleteFn: (ids: Array<number | string>) => Promise<void>,
    options?: {
      confirmMessage?: string
      successMessage?: string
      errorMessage?: string
    }
  ) {
    if (!hasSelection.value) {
      showToast('请先选择要删除的项目', 'warning')
      return
    }
    
    const count = selectedIds.value.size
    const confirmMsg = options?.confirmMessage || `确定要删除选中的 ${count} 个项目吗？此操作不可恢复。`
    
    // 确认对话框
    if (!confirm(confirmMsg)) {
      return
    }
    
    try {
      const ids = Array.from(selectedIds.value)
      await deleteFn(ids)
      
      showToast(options?.successMessage || `成功删除 ${count} 个项目`, 'success')
      
      // 清空选择
      deselectAll()
    } catch (error) {
      console.error('[BatchOperations] Delete failed:', error)
      showToast(options?.errorMessage || '批量删除失败', 'danger')
    }
  }
  
  /**
   * 批量更新状态
   */
  async function batchUpdateStatus(
    status: string,
    updateFn: (ids: Array<number | string>, status: string) => Promise<void>,
    options?: {
      confirmMessage?: string
      successMessage?: string
      errorMessage?: string
    }
  ) {
    if (!hasSelection.value) {
      showToast('请先选择要更新的项目', 'warning')
      return
    }
    
    const count = selectedIds.value.size
    const confirmMsg = options?.confirmMessage || `确定要将选中的 ${count} 个项目的状态修改为"${status}"吗？`
    
    if (!confirm(confirmMsg)) {
      return
    }
    
    try {
      const ids = Array.from(selectedIds.value)
      await updateFn(ids, status)
      
      showToast(options?.successMessage || `成功更新 ${count} 个项目的状态`, 'success')
      
      // 清空选择
      deselectAll()
    } catch (error) {
      console.error('[BatchOperations] Status update failed:', error)
      showToast(options?.errorMessage || '批量更新状态失败', 'danger')
    }
  }
  
  /**
   * 批量导出
   */
  async function batchExport(
    exportFn: (ids: Array<number | string>) => Promise<Blob>,
    filename: string = 'export.csv',
    options?: {
      successMessage?: string
      errorMessage?: string
    }
  ) {
    if (!hasSelection.value) {
      showToast('请先选择要导出的项目', 'warning')
      return
    }
    
    try {
      const ids = Array.from(selectedIds.value)
      const blob = await exportFn(ids)
      
      // 下载文件
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      showToast(options?.successMessage || '导出成功', 'success')
    } catch (error) {
      console.error('[BatchOperations] Export failed:', error)
      showToast(options?.errorMessage || '导出失败', 'danger')
    }
  }
  
  /**
   * 清空选择
   */
  function clearSelection() {
    deselectAll()
  }
  
  return {
    selectedIds,
    selectedCount,
    hasSelection,
    isSelectAll,
    toggleSelection,
    selectAll,
    deselectAll,
    toggleSelectAll,
    isSelected,
    batchDelete,
    batchUpdateStatus,
    batchExport,
    clearSelection,
  }
}
