export function atualizadaHa(iso: string, agora = new Date()): string {
  const data = new Date(iso)
  if (Number.isNaN(data.getTime())) {
    return 'atualizada'
  }
  const minutos = Math.max(0, Math.floor((agora.getTime() - data.getTime()) / 60000))
  if (minutos < 1) {
    return 'atualizada agora'
  }
  if (minutos < 60) {
    return `atualizada há ${minutos} min`
  }
  const horas = Math.floor(minutos / 60)
  if (horas < 24) {
    return `atualizada há ${horas} h`
  }
  const dias = Math.floor(horas / 24)
  return dias === 1 ? 'atualizada há 1 dia' : `atualizada há ${dias} dias`
}
