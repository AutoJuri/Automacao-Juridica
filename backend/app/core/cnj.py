"""Parsing do número CNJ e resolução do alias de índice do DataJud.

Formato do número CNJ (Resolução CNJ nº 65/2008): `NNNNNNN-DD.AAAA.J.TR.OOOO`
(7+2+4+1+2+4 dígitos). Só o segmento (`J`) e o código do tribunal (`TR`)
importam pra resolver o alias — sequencial, dígito verificador e origem
(`OOOO`) são ignorados aqui.

Cobertura intencionalmente parcial (ver ADR-015): Justiça Estadual (TJs),
Justiça Federal (TRFs), Justiça do Trabalho (TRTs) e os tribunais
superiores mais comuns (STF/STJ/TST). Segmento/tribunal fora dessa tabela
devolve `None` — quem chama trata como "não suportado ainda", nunca como
erro (nunca lança exceção).
"""

import re

# Aceita com ou sem máscara: "1002345-67.2025.8.26.0100" ou os 20 dígitos
# corridos "10023456720258260100".
_NUMERO_CNJ_RE = re.compile(
    r"^(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})$"
)

# Tabela alfabética de UF usada pelo CNJ (Resolução 65/2008, Anexo V) — a
# mesma ordem vale tanto pra Justiça Estadual (segmento 8) quanto pra
# Justiça Eleitoral (segmento 6, não mapeada abaixo por ora).
_UF_POR_CODIGO_TRIBUNAL = {
    "01": "AC", "02": "AL", "03": "AP", "04": "AM", "05": "BA", "06": "CE",
    "07": "DF", "08": "ES", "09": "GO", "10": "MA", "11": "MT", "12": "MS",
    "13": "MG", "14": "PA", "15": "PB", "16": "PR", "17": "PE", "18": "PI",
    "19": "RJ", "20": "RN", "21": "RS", "22": "RO", "23": "RR", "24": "SC",
    "25": "SE", "26": "SP", "27": "TO",
}

# "tj" + UF em minúsculo, exceto o Distrito Federal (TJDFT, não "tjdf").
_ALIAS_TJ_POR_UF = {uf: f"tj{uf.lower()}" for uf in _UF_POR_CODIGO_TRIBUNAL.values()}
_ALIAS_TJ_POR_UF["DF"] = "tjdft"

_ALIAS_TRF_POR_CODIGO = {
    "01": "trf1", "02": "trf2", "03": "trf3", "04": "trf4", "05": "trf5", "06": "trf6",
}

# TRT1..TRT24 (Resolução 65/2008); TR "90" no segmento 5 é o TST, não um TRT.
_ALIAS_TRT_POR_CODIGO = {f"{i:02d}": f"trt{i}" for i in range(1, 25)}
_TRIBUNAL_TST = "90"

# Segmentos 1 (STF) e 3 (STJ) não usam o código de tribunal (`TR` é sempre
# "00") — o alias já é fixo pelo segmento.
_ALIAS_POR_SEGMENTO_FIXO = {
    "1": "stf",
    "3": "stj",
}


def extrair_segmento_tribunal(numero_cnj: str) -> tuple[str, str] | None:
    """Devolve `(segmento, tribunal)` a partir do número CNJ. `None` se o
    formato não bater — ex.: número interno do e-SAJ (`cd_processo`), que
    não é o número CNJ.
    """
    if not numero_cnj:
        return None
    match = _NUMERO_CNJ_RE.match(numero_cnj.strip())
    if match is None:
        return None
    _sequencial, _digito_verificador, _ano, segmento, tribunal, _origem = match.groups()
    return segmento, tribunal


def resolver_alias_datajud(numero_cnj: str) -> str | None:
    """Alias do índice DataJud (usado como `api_publica_<alias>`) para o
    número CNJ informado, ou `None` se o número for inválido ou o
    segmento/tribunal ainda não estiver mapeado. Nunca lança.
    """
    extraido = extrair_segmento_tribunal(numero_cnj)
    if extraido is None:
        return None
    segmento, tribunal = extraido

    if segmento == "8":
        uf = _UF_POR_CODIGO_TRIBUNAL.get(tribunal)
        return _ALIAS_TJ_POR_UF.get(uf) if uf else None
    if segmento == "4":
        return _ALIAS_TRF_POR_CODIGO.get(tribunal)
    if segmento == "5":
        if tribunal == _TRIBUNAL_TST:
            return "tst"
        return _ALIAS_TRT_POR_CODIGO.get(tribunal)
    return _ALIAS_POR_SEGMENTO_FIXO.get(segmento)
