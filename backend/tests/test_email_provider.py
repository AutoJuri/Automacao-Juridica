"""Testes de app.core.email_provider.detectar_provedor_por_dominio —
sem rede real: `dns.resolver.resolve` é sempre monkeypatchado."""

import dns.resolver
import pytest

from app.core.email_provider import detectar_provedor_por_dominio


class _RegistroMx:
    def __init__(self, exchange: str) -> None:
        self.exchange = exchange


class TestDetectarProvedorPorDominio:
    def test_gmail_com_e_atalho_conhecido_sem_consultar_dns(self, monkeypatch):
        def _explode(*_args, **_kwargs):
            raise AssertionError("não deveria consultar DNS para domínio conhecido")

        monkeypatch.setattr(dns.resolver, "resolve", _explode)

        assert detectar_provedor_por_dominio("advogado@gmail.com") == "gmail"

    def test_outlook_hotmail_live_msn_sao_atalhos_conhecidos(self, monkeypatch):
        def _explode(*_args, **_kwargs):
            raise AssertionError("não deveria consultar DNS para domínio conhecido")

        monkeypatch.setattr(dns.resolver, "resolve", _explode)

        assert detectar_provedor_por_dominio("advogado@hotmail.com") == "outlook"
        assert detectar_provedor_por_dominio("advogado@live.com") == "outlook"
        assert detectar_provedor_por_dominio("advogado@msn.com") == "outlook"
        assert detectar_provedor_por_dominio("advogado@outlook.com") == "outlook"

    def test_dominio_proprio_com_mx_do_google_workspace(self, monkeypatch):
        def _resolve(_dominio, _tipo, lifetime):
            return [_RegistroMx("aspmx.l.google.com.")]

        monkeypatch.setattr(dns.resolver, "resolve", _resolve)

        assert detectar_provedor_por_dominio("advogado@meuescritorio.adv.br") == "gmail"

    def test_dominio_proprio_com_mx_do_microsoft_365(self, monkeypatch):
        def _resolve(_dominio, _tipo, lifetime):
            return [_RegistroMx("meuescritorio-adv-br.mail.protection.outlook.com.")]

        monkeypatch.setattr(dns.resolver, "resolve", _resolve)

        assert detectar_provedor_por_dominio("advogado@meuescritorio.adv.br") == "outlook"

    def test_dominio_com_mx_desconhecido_devolve_none(self, monkeypatch):
        def _resolve(_dominio, _tipo, lifetime):
            return [_RegistroMx("mx.algumoutroprovedor.com.")]

        monkeypatch.setattr(dns.resolver, "resolve", _resolve)

        assert detectar_provedor_por_dominio("advogado@meuescritorio.adv.br") is None

    def test_falha_de_dns_devolve_none(self, monkeypatch):
        def _resolve(*_args, **_kwargs):
            raise dns.resolver.NXDOMAIN()

        monkeypatch.setattr(dns.resolver, "resolve", _resolve)

        assert detectar_provedor_por_dominio("advogado@dominio-que-nao-existe.zzz") is None

    def test_timeout_de_dns_devolve_none(self, monkeypatch):
        def _resolve(*_args, **_kwargs):
            raise dns.resolver.LifetimeTimeout()

        monkeypatch.setattr(dns.resolver, "resolve", _resolve)

        assert detectar_provedor_por_dominio("advogado@dominio-lento.com") is None

    def test_email_sem_arroba_devolve_none(self):
        assert detectar_provedor_por_dominio("nao-e-um-email") is None
