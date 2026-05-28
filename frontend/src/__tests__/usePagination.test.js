import { describe, it, expect } from 'vitest'
import { usePagination } from '../composables/usePagination'

describe('usePagination', () => {
  it('initializes with default values', () => {
    const { page, perPage, total, totalPages } = usePagination()
    expect(page.value).toBe(1)
    expect(perPage.value).toBe(50)
    expect(total.value).toBe(0)
    expect(totalPages.value).toBe(1)
  })

  it('initializes with custom perPage', () => {
    const { perPage } = usePagination(20)
    expect(perPage.value).toBe(20)
  })

  it('calculates totalPages correctly', () => {
    const { setTotal, totalPages } = usePagination(20)

    setTotal(0)
    expect(totalPages.value).toBe(1)

    setTotal(1)
    expect(totalPages.value).toBe(1)

    setTotal(20)
    expect(totalPages.value).toBe(1)

    setTotal(21)
    expect(totalPages.value).toBe(2)

    setTotal(100)
    expect(totalPages.value).toBe(5)
  })

  it('calculates offset correctly', () => {
    const { offset, goTo, setTotal } = usePagination(20)
    setTotal(100)

    expect(offset.value).toBe(0)
    goTo(3)
    expect(offset.value).toBe(40)
  })

  it('navigates with next/prev', () => {
    const { page, next, prev, setTotal } = usePagination(10)
    setTotal(30)

    next()
    expect(page.value).toBe(2)
    next()
    expect(page.value).toBe(3)
    next() // already at last page
    expect(page.value).toBe(3)

    prev()
    expect(page.value).toBe(2)
  })

  it('prev stops at page 1', () => {
    const { page, prev } = usePagination()
    prev()
    expect(page.value).toBe(1)
  })

  it('goTo clamps to valid range', () => {
    const { page, goTo, setTotal } = usePagination(10)
    setTotal(50)

    goTo(0)
    expect(page.value).toBe(1)

    goTo(100)
    expect(page.value).toBe(5)

    goTo(-5)
    expect(page.value).toBe(1)
  })

  it('reset returns to page 1 with zero total', () => {
    const { page, total, setTotal, goTo, reset } = usePagination(10)
    setTotal(100)
    goTo(5)
    expect(page.value).toBe(5)

    reset()
    expect(page.value).toBe(1)
    expect(total.value).toBe(0)
  })
})
