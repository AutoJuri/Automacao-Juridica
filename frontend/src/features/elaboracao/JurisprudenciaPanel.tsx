import { useState } from 'react'
import { Switch } from '#/components/ui/switch'
import { Label } from '#/components/ui/label'
import { jurisprudenciaToggles } from './elaboracao.mock'

export function JurisprudenciaPanel() {
  const [toggles, setToggles] = useState(() =>
    jurisprudenciaToggles.reduce<Record<string, boolean>>((acc, t) => {
      acc[t.id] = t.ativo
      return acc
    }, {}),
  )

  function handleToggle(id: string, checked: boolean) {
    setToggles((prev) => ({ ...prev, [id]: checked }))
  }

  const tribunais = jurisprudenciaToggles.filter((t) => t.categoria === 'tribunal')
  const fontes = jurisprudenciaToggles.filter((t) => t.categoria === 'fonte')

  return (
    <div>
      <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-3">
        Jurisprudências
      </p>

      <div className="space-y-4">
        <div>
          <p className="text-[9px] text-[#9CA3AF] uppercase tracking-widest mb-2">Tribunais</p>
          <div className="space-y-2">
            {tribunais.map((t) => (
              <div key={t.id} className="flex items-center justify-between gap-2">
                <Label
                  htmlFor={`toggle-${t.id}`}
                  className="flex-1 min-w-0 cursor-pointer"
                >
                  <span className="text-[12px] font-medium text-[#374151] block">{t.label}</span>
                  {t.sublabel && (
                    <span className="text-[10px] text-[#9CA3AF]">{t.sublabel}</span>
                  )}
                </Label>
                <Switch
                  id={`toggle-${t.id}`}
                  checked={toggles[t.id] ?? false}
                  onCheckedChange={(checked) => handleToggle(t.id, checked)}
                  className="shrink-0"
                />
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="text-[9px] text-[#9CA3AF] uppercase tracking-widest mb-2">Fontes</p>
          <div className="space-y-2">
            {fontes.map((t) => (
              <div key={t.id} className="flex items-center justify-between gap-2">
                <Label
                  htmlFor={`toggle-${t.id}`}
                  className="flex-1 min-w-0 cursor-pointer"
                >
                  <span className="text-[12px] font-medium text-[#374151] block">{t.label}</span>
                  {t.sublabel && (
                    <span className="text-[10px] text-[#9CA3AF]">{t.sublabel}</span>
                  )}
                </Label>
                <Switch
                  id={`toggle-${t.id}`}
                  checked={toggles[t.id] ?? false}
                  onCheckedChange={(checked) => handleToggle(t.id, checked)}
                  className="shrink-0"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
