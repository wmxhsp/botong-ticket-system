import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useFormValidation, useFieldValidation } from '../composables/useFormValidation'

describe('useFormValidation', () => {
  let validation

  beforeEach(() => {
    validation = useFormValidation()
  })

  describe('validateForm', () => {
    it('returns isValid=true when all fields pass', () => {
      const formData = { name: '张三', phone: '13800138000' }
      const rules = {
        name: [{ rule: 'required' }],
        phone: [{ rule: 'phone' }],
      }
      const { isValid, errors } = validation.validateForm(formData, rules)
      expect(isValid).toBe(true)
      expect(Object.keys(errors)).toHaveLength(0)
    })

    it('returns isValid=false with error messages for invalid fields', () => {
      const formData = { name: '', phone: '123' }
      const rules = {
        name: [{ rule: 'required' }],
        phone: [{ rule: 'phone' }],
      }
      const { isValid, errors } = validation.validateForm(formData, rules)
      expect(isValid).toBe(false)
      expect(errors.name).toBe('此字段必填')
      expect(errors.phone).toBe('请输入有效的手机号码')
    })

    it('validates email format', () => {
      const { errors: e1 } = validation.validateForm(
        { email: 'test@example.com' },
        { email: [{ rule: 'email' }] }
      )
      expect(e1.email).toBeUndefined()

      const { errors: e2 } = validation.validateForm(
        { email: 'not-an-email' },
        { email: [{ rule: 'email' }] }
      )
      expect(e2.email).toBe('请输入有效的邮箱地址')
    })

    it('validates min/max length', () => {
      const rules = {
        name: [{ rule: 'min', value: 2, message: '至少2字' }],
        code: [{ rule: 'max', value: 10, message: '最多10字' }],
      }
      const { isValid: v1 } = validation.validateForm({ name: '一', code: 'ok' }, rules)
      expect(v1).toBe(false)

      const { isValid: v2 } = validation.validateForm({ name: '张三', code: 'a'.repeat(11) }, rules)
      expect(v2).toBe(false)

      const { isValid: v3 } = validation.validateForm({ name: '张三', code: 'ok' }, rules)
      expect(v3).toBe(true)
    })

    it('validates numeric and positive', () => {
      const { errors: e1 } = validation.validateForm(
        { price: 'abc' },
        { price: [{ rule: 'numeric' }] }
      )
      expect(e1.price).toBe('请输入数字')

      const { errors: e2 } = validation.validateForm(
        { amount: -5 },
        { amount: [{ rule: 'positive' }] }
      )
      expect(e2.amount).toBe('请输入正数')
    })

    it('validates decimal places', () => {
      const { errors: e1 } = validation.validateForm(
        { price: '10.123' },
        { price: [{ rule: 'decimal', value: 2 }] }
      )
      expect(e1.price).toBe('最多保留2位小数')

      const { errors: e2 } = validation.validateForm(
        { price: '10.12' },
        { price: [{ rule: 'decimal', value: 2 }] }
      )
      expect(e2.price).toBeUndefined()
    })

    it('validates custom pattern', () => {
      const { errors: e1 } = validation.validateForm(
        { code: 'ABC' },
        { code: [{ rule: 'pattern', value: '^\\d+$', message: '只能输入数字' }] }
      )
      expect(e1.code).toBe('只能输入数字')

      const { errors: e2 } = validation.validateForm(
        { code: '123' },
        { code: [{ rule: 'pattern', value: '^\\d+$' }] }
      )
      expect(e2.code).toBeUndefined()
    })

    it('skips validation for empty optional fields', () => {
      const { isValid } = validation.validateForm(
        { email: '' },
        { email: [{ rule: 'email' }] }
      )
      expect(isValid).toBe(true)
    })
  })

  describe('validateOnBlur / validateOnInput', () => {
    it('validates on blur and marks field as touched', () => {
      const err = validation.validateOnBlur('phone', '123', [{ rule: 'phone' }])
      expect(err).toBe('请输入有效的手机号码')
      expect(validation.touched.phone).toBe(true)
    })

    it('does not validate on input if field not touched', () => {
      const err = validation.validateOnInput('phone', '123', [{ rule: 'phone' }])
      expect(err).toBeUndefined()
    })

    it('validates on input if field was previously touched', () => {
      validation.validateOnBlur('phone', '', [{ rule: 'phone' }])
      const err = validation.validateOnInput('phone', '123', [{ rule: 'phone' }])
      expect(err).toBe('请输入有效的手机号码')
    })
  })

  describe('clearError / clearAllErrors', () => {
    it('clears a specific field error', () => {
      validation.validateForm({ name: '' }, { name: [{ rule: 'required' }] })
      expect(validation.errors.name).toBeDefined()
      validation.clearError('name')
      expect(validation.errors.name).toBeUndefined()
    })

    it('clears all errors and touched state', () => {
      validation.validateForm(
        { name: '', phone: '123' },
        { name: [{ rule: 'required' }], phone: [{ rule: 'phone' }] }
      )
      validation.clearAllErrors()
      expect(Object.keys(validation.errors)).toHaveLength(0)
      expect(Object.keys(validation.touched)).toHaveLength(0)
    })
  })

  describe('useFieldValidation', () => {
    it('validates on blur', () => {
      const field = useFieldValidation('phone', '', [{ rule: 'phone' }])
      field.value.value = '123'
      field.handleBlur()
      expect(field.error.value).toBe('请输入有效的手机号码')
      expect(field.touched.value).toBe(true)
    })

    it('resets to initial state', () => {
      const field = useFieldValidation('name', '初始值', [{ rule: 'required' }])
      field.value.value = ''
      field.handleBlur()
      expect(field.error.value).toBeDefined()
      field.reset()
      expect(field.value.value).toBe('初始值')
      expect(field.error.value).toBeNull()
      expect(field.touched.value).toBe(false)
    })

    it('validates programmatically', () => {
      const field = useFieldValidation('email', 'bad', [{ rule: 'email' }])
      expect(field.validate()).toBe(false)
      expect(field.error.value).toBe('请输入有效的邮箱地址')

      field.value.value = 'ok@test.com'
      expect(field.validate()).toBe(true)
    })
  })
})
