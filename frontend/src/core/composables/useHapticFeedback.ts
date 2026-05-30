/**
 * 触觉反馈 Composable
 * 
 * 提供移动端触觉反馈功能，增强用户交互体验
 * 仅在支持的设备上生效（iOS Safari、Android Chrome等）
 * 
 * @example
 * ```ts
 * const { triggerHaptic } = useHapticFeedback()
 * 
 * // 按钮点击时触发轻微震动
 * onClick(() => {
 *   triggerHaptic('light')
 * })
 * 
 * // 操作成功时触发中等震动
 * onSuccess(() => {
 *   triggerHaptic('success')
 * })
 * ```
 */

export type HapticType = 
  | 'light'      // 轻微震动（点击）
  | 'medium'     // 中等震动（确认）
  | 'heavy'      // 强烈震动（错误/警告）
  | 'success'    // 成功反馈
  | 'warning'    // 警告反馈
  | 'error'      // 错误反馈
  | 'selection'  // 选择变化

export function useHapticFeedback() {
  /**
   * 检测是否支持触觉反馈
   */
  function isSupported(): boolean {
    return typeof navigator !== 'undefined' && 
           'vibrate' in navigator
  }

  /**
   * 触发触觉反馈
   * 
   * @param type - 反馈类型
   * @param pattern - 自定义震动模式（毫秒数组），优先级高于type
   */
  function triggerHaptic(type: HapticType, pattern?: number | number[]) {
    if (!isSupported()) {
      console.debug('Haptic feedback not supported on this device')
      return
    }

    // 如果提供了自定义模式，直接使用
    if (pattern) {
      navigator.vibrate(pattern)
      return
    }

    // 根据类型选择震动模式
    const patterns: Record<HapticType, number | number[]> = {
      light: 10,              // 轻微点击
      medium: 20,             // 中等确认
      heavy: 30,              // 强烈警告
      success: [20, 50, 20],  // 成功：短-停-短
      warning: [30, 50, 30],  // 警告：中-停-中
      error: [50, 100, 50],   // 错误：长-停-长
      selection: 5            // 选择：极短
    }

    navigator.vibrate(patterns[type])
  }

  /**
   * 取消所有正在进行的震动
   */
  function cancelHaptic() {
    if (isSupported()) {
      navigator.vibrate(0)
    }
  }

  /**
   * 创建带触觉反馈的事件处理器
   * 
   * @param handler - 原始事件处理器
   * @param hapticType - 触觉反馈类型
   * @returns 包装后的事件处理器
   */
  function withHaptic<T extends (...args: any[]) => void>(
    handler: T,
    hapticType: HapticType = 'light'
  ): T {
    return ((...args: Parameters<T>) => {
      triggerHaptic(hapticType)
      return handler(...args)
    }) as T
  }

  return {
    isSupported,
    triggerHaptic,
    cancelHaptic,
    withHaptic
  }
}

/**
 * 触觉反馈指令（用于Vue模板）
 * 
 * @example
 * ```vue
 * <button v-haptic:light @click="handleClick">点击</button>
 * <button v-haptic:success @click="handleSuccess">成功</button>
 * ```
 */
export const vHaptic = {
  mounted(el: HTMLElement, binding: { value?: HapticType; arg?: HapticType }) {
    const type = binding.arg || binding.value || 'light'
    
    el.addEventListener('click', () => {
      const { triggerHaptic } = useHapticFeedback()
      triggerHaptic(type)
    }, { passive: true })
  }
}
