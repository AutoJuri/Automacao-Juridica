export function AuthVisualPanel() {
  return (
    <div className="relative hidden lg:flex flex-col items-center justify-center w-1/2 overflow-hidden bg-[#1e1b4b]">
      {/* Gradient base */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#3B5BDB] via-[#5c47d4] to-[#8B5CF6]" />

      {/* Noise texture overlay */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '256px',
        }}
      />

      {/* Geometric grid lines */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.07]"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="white" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Large decorative circle backdrop */}
      <div className="absolute top-[-120px] right-[-120px] w-[520px] h-[520px] rounded-full bg-white/5 blur-xl" />
      <div className="absolute bottom-[-80px] left-[-80px] w-[360px] h-[360px] rounded-full bg-white/5 blur-2xl" />

      {/* Main visual composition */}
      <div className="relative z-10 flex flex-col items-center gap-10 px-12">
        {/* Central emblem — scales of justice abstraction */}
        <svg
          width="220"
          height="220"
          viewBox="0 0 220 220"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="drop-shadow-2xl"
        >
          {/* Outer ring */}
          <circle cx="110" cy="110" r="100" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
          <circle cx="110" cy="110" r="80" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />

          {/* Pillar */}
          <rect x="107" y="50" width="6" height="120" rx="3" fill="rgba(255,255,255,0.9)" />

          {/* Crossbar */}
          <rect x="55" y="72" width="110" height="5" rx="2.5" fill="rgba(255,255,255,0.9)" />

          {/* Left pan chain */}
          <line x1="75" y1="77" x2="68" y2="118" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" strokeDasharray="3 2" />
          <line x1="68" y1="118" x2="55" y2="118" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" />
          <line x1="55" y1="118" x2="48" y2="118" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" />
          {/* Left pan */}
          <path d="M 44 118 Q 62 132 80 118" stroke="rgba(255,255,255,0.9)" strokeWidth="2" fill="none" />

          {/* Right pan chain */}
          <line x1="145" y1="77" x2="152" y2="118" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" strokeDasharray="3 2" />
          <line x1="152" y1="118" x2="165" y2="118" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" />
          <line x1="165" y1="118" x2="172" y2="118" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" />
          {/* Right pan */}
          <path d="M 140 118 Q 158 132 176 118" stroke="rgba(255,255,255,0.9)" strokeWidth="2" fill="none" />

          {/* Base */}
          <rect x="92" y="168" width="36" height="5" rx="2.5" fill="rgba(255,255,255,0.7)" />

          {/* Shield motif */}
          <path
            d="M110 90 L125 98 L125 116 Q125 126 110 132 Q95 126 95 116 L95 98 Z"
            fill="rgba(255,255,255,0.12)"
            stroke="rgba(255,255,255,0.4)"
            strokeWidth="1"
          />
          <path
            d="M110 98 L119 103 L119 115 Q119 121 110 126 Q101 121 101 115 L101 103 Z"
            fill="rgba(255,255,255,0.15)"
          />
        </svg>

        {/* Text block */}
        <div className="text-center space-y-3">
          <p className="text-white/40 text-xs font-medium tracking-[0.25em] uppercase">
            Plataforma Jurídica
          </p>
          <h2
            className="text-white text-3xl leading-snug"
            style={{ fontFamily: 'DM Serif Display, Georgia, serif' }}
          >
            Segurança e controle
            <br />
            <span className="italic text-white/80">para cada processo</span>
          </h2>
          <p className="text-white/50 text-sm leading-relaxed max-w-xs mx-auto">
            Monitoramento automático de autos judiciais com tecnologia de ponta e conformidade total.
          </p>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2">
          {['e-SAJ TJSP', 'Criptografia AES-256', 'Monitoramento 24/7'].map((label) => (
            <span
              key={label}
              className="px-3 py-1 rounded-full text-xs font-medium text-white/70 bg-white/10 border border-white/15 backdrop-blur-sm"
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
    </div>
  )
}
