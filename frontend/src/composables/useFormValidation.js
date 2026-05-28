/**
 * 表单验证 composable
 * 
 * 提供表单验证、错误提示和实时校验功能。
 * 
 * 用法:
 *   const { form, errors, validateField, validateForm } = useFormValidation()
 *   form.email = 'test@example.com'
 *   errors.email = validateField('email', form.email)
 *   
 * 支持的验证规则:
 *   - required: 必填
 *   - email: 邮箱格式
 *   - phone: 手机号格式
 *   - url: URL格式
 *   - min: 最小长度/最小值
 *   - max: 最大长度/最大值
 *   - pattern: 正则表达式
 *   - numeric: 数字
 *   - positive: 正数
 *   - decimal: 小数位数
 */
import { ref, reactive } from 'vue'

// ── 模块级验证规则（供 validateField 和 useFieldValidation 共享） ──

const VALIDATION_RULES = {
  required: (value, rule) => {
    if (!value && value !== 0 && value !== false) {
      return rule.message || '此字段必填'
    }
    return null
  },

  email: (value) => {
    if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      return '请输入有效的邮箱地址'
    }
    return null
  },

  phone: (value) => {
    if (value && !/^1[3-9]\d{9}$/.test(value.replace(/\s/g, ''))) {
      return '请输入有效的手机号码'
    }
    return null
  },

  url: (value) => {
    if (value && !/^https?:\/\/[^\s]+$/.test(value)) {
      return '请输入有效的网址'
    }
    return null
  },

  min: (value, rule) => {
    const minValue = parseFloat(rule.value)
    if (typeof value === 'string' && value.length < minValue) {
      return rule.message || `至少需要${minValue}个字符`
    }
    if (typeof value === 'number' && value < minValue) {
      return rule.message || `最小值为${minValue}`
    }
    return null
  },

  max: (value, rule) => {
    const maxValue = parseFloat(rule.value)
    if (typeof value === 'string' && value.length > maxValue) {
      return rule.message || `最多${maxValue}个字符`
    }
    if (typeof value === 'number' && value > maxValue) {
      return rule.message || `最大值为${maxValue}`
    }
    return null
  },

  pattern: (value, rule) => {
    if (value && rule.value && !new RegExp(rule.value).test(value)) {
      return rule.message || '格式不正确'
    }
    return null
  },

  numeric: (value) => {
    if (value && isNaN(parseFloat(value))) {
      return '请输入数字'
    }
    return null
  },

  positive: (value) => {
    const num = parseFloat(value)
    if (!isNaN(num) && num <= 0) {
      return '请输入正数'
    }
    return null
  },

  decimal: (value, rule) => {
    const decimals = rule.value || 2
    const regex = new RegExp(`^\\d+(\\.\\d{1,${decimals}})?$`)
    if (value && !regex.test(value)) {
      return rule.message || `最多保留${decimals}位小数`
    }
    return null
  },
}

/**
 * 单字段验证（模块级，供 composable 内部和 useFieldValidation 共享）
 * @param {string} fieldName - 字段名
 * @param {*} value - 字段值
 * @param {Array<{rule: string, value?: *, message?: string}>} rules - 验证规则
 * @returns {string|null} 错误信息，无错误返回 null
 */
function validateField(fieldName, value, rules = []) {
  for (const rule of rules) {
    const ruleFn = VALIDATION_RULES[rule.rule]
    if (ruleFn) {
      const error = ruleFn(value, rule)
      if (error) return error
    }
  }
  return null
}

// ── Composable: 表单级验证 ──

export function useFormValidation() {
  const form = reactive({})
  const errors = reactive({})
  const touched = reactive({})

  function validateForm(formData, fieldRules) {
    const allErrors = {}
    let isValid = true

    for (const [field, rules] of Object.entries(fieldRules)) {
      const value = formData[field]
      const error = validateField(field, value, rules)
      if (error) {
        allErrors[field] = error
        isValid = false
      }
    }

    Object.assign(errors, allErrors)
    return { isValid, errors: allErrors }
  }

  function validateOnBlur(fieldName, value, rules) {
    touched[fieldName] = true
    errors[fieldName] = validateField(fieldName, value, rules)
    return errors[fieldName]
  }

  function validateOnInput(fieldName, value, rules) {
    if (touched[fieldName]) {
      errors[fieldName] = validateField(fieldName, value, rules)
    }
    return errors[fieldName]
  }

  function setFieldError(fieldName, error) {
    errors[fieldName] = error
  }

  function clearError(fieldName) {
    delete errors[fieldName]
  }

  function clearAllErrors() {
    Object.keys(errors).forEach(key => delete errors[key])
    Object.keys(touched).forEach(key => delete touched[key])
  }

  function isFieldValid(fieldName) {
    return !errors[fieldName]
  }

  return {
    form,
    errors,
    touched,
    validateField,
    validateForm,
    validateOnBlur,
    validateOnInput,
    setFieldError,
    clearError,
    clearAllErrors,
    isFieldValid,
  }
}

// ── Composable: 单字段验证 ──

export function useFieldValidation(fieldName, initialValue = '', rules = []) {
  const value = ref(initialValue)
  const error = ref(null)
  const touched = ref(false)

  function validate() {
    error.value = validateField(fieldName, value.value, rules)
    return !error.value
  }

  function handleInput(event) {
    value.value = event.target?.value ?? event
    if (touched.value) {
      error.value = validateField(fieldName, value.value, rules)
    }
  }

  function handleBlur() {
    touched.value = true
    error.value = validateField(fieldName, value.value, rules)
  }

  function reset() {
    value.value = initialValue
    error.value = null
    touched.value = false
  }

  return {
    value,
    error,
    touched,
    validate,
    handleInput,
    handleBlur,
    reset,
  }
}
