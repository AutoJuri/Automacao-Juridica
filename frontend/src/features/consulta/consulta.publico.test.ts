import { describe, expect, it } from 'vitest'

import { mesmosDigitos, numeroCnjCompleto } from './consulta.publico'

describe('numeroCnjCompleto', () => {
  it('aceita o CNJ com máscara ou só com dígitos', () => {
    expect(numeroCnjCompleto('1002345-67.2025.8.26.0100')).toBe(true)
    expect(numeroCnjCompleto('10023456720258260100')).toBe(true)
  })

  it('recusa número incompleto, nome e OAB', () => {
    expect(numeroCnjCompleto('1002345-67.2025')).toBe(false)
    expect(numeroCnjCompleto('Maria da Silva')).toBe(false)
    expect(numeroCnjCompleto('123456')).toBe(false)
  })
})

describe('mesmosDigitos', () => {
  it('reconhece o mesmo CNJ com pontuação diferente', () => {
    expect(mesmosDigitos('10023456720258260100', '1002345-67.2025.8.26.0100')).toBe(true)
    expect(mesmosDigitos('00000000000000000000', '1002345-67.2025.8.26.0100')).toBe(false)
    expect(mesmosDigitos(null, '1002345-67.2025.8.26.0100')).toBe(false)
  })
})
