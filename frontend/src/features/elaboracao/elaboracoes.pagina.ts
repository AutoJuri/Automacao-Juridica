export function juntarPorId<T extends { id: string }>(paginas: T[][]): T[] {
  const vistos = new Set<string>()
  const saida: T[] = []
  for (const pagina of paginas) {
    for (const item of pagina) {
      if (vistos.has(item.id)) {
        continue
      }
      vistos.add(item.id)
      saida.push(item)
    }
  }
  return saida
}
